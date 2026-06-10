"""Streamlit dashboard for the Mars Forecast Analyst business case."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mars_forecast_case.pipeline import build_outputs  # noqa: E402


OUTPUT_DIR = PROJECT_ROOT / "outputs"
HEADER_IMAGE = PROJECT_ROOT / "asset" / "Mars-Snacking.jpg"
MARS_RED = "#9E1B32"
INK = "#263238"
TEAL = "#007A78"
GOLD = "#F2A900"
LIGHT = "#F7F5F2"
GRAY = "#6B7280"


st.set_page_config(
    page_title="Mars Real Deal Forecast",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_dashboard_data() -> dict[str, object]:
    """Load generated analysis outputs, rebuilding them when needed."""

    required = [
        OUTPUT_DIR / "weekly_clean_data.csv",
        OUTPUT_DIR / "forecast_summary.csv",
        OUTPUT_DIR / "january_forecast_scenarios.csv",
        OUTPUT_DIR / "period_summary.csv",
        OUTPUT_DIR / "promotion_summary.csv",
        OUTPUT_DIR / "key_metrics.json",
    ]
    if not all(path.exists() for path in required):
        build_outputs(OUTPUT_DIR)

    with (OUTPUT_DIR / "key_metrics.json").open(encoding="utf-8") as file:
        metrics = json.load(file)

    return {
        "weekly": pd.read_csv(OUTPUT_DIR / "weekly_clean_data.csv", parse_dates=["week_start"]),
        "forecast_summary": pd.read_csv(OUTPUT_DIR / "forecast_summary.csv"),
        "weekly_scenarios": pd.read_csv(OUTPUT_DIR / "january_forecast_scenarios.csv"),
        "period": pd.read_csv(OUTPUT_DIR / "period_summary.csv"),
        "promotion": pd.read_csv(OUTPUT_DIR / "promotion_summary.csv"),
        "metrics": metrics,
    }


def fmt_k(value: float) -> str:
    """Format a thousands-of-cases value for KPI display."""

    return f"{value:,.0f}k"


def apply_css() -> None:
    """Apply restrained Mars-inspired dashboard styling."""

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {LIGHT};
            color: {INK};
        }}
        div[data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            padding: 14px 16px;
            border-radius: 8px;
        }}
        div[data-testid="stMetricValue"] {{
            color: {MARS_RED};
        }}
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] p {{
            color: #374151 !important;
            font-weight: 600;
        }}
        .section-note {{
            color: {GRAY};
            font-size: 0.94rem;
            line-height: 1.45;
        }}
        .decision-box {{
            background: #FFFFFF;
            border-left: 5px solid {MARS_RED};
            padding: 16px 18px;
            border-radius: 6px;
            margin: 8px 0 18px 0;
        }}
        .hero-image {{
            min-height: 232px;
            border-radius: 8px;
            background-size: cover;
            background-position: center 46%;
            display: flex;
            align-items: flex-end;
            margin: 8px 0 28px 0;
            box-shadow: 0 10px 28px rgba(38, 50, 56, 0.14);
            overflow: hidden;
        }}
        .hero-copy {{
            padding: 30px 34px;
            color: #FFFFFF;
            text-shadow: 0 2px 12px rgba(0, 0, 0, 0.38);
        }}
        .hero-copy h1 {{
            font-size: 2.45rem;
            line-height: 1.08;
            margin: 0 0 8px 0;
            letter-spacing: 0;
        }}
        .hero-copy p {{
            font-size: 1rem;
            margin: 0;
            color: rgba(255, 255, 255, 0.92);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def image_data_uri(path: Path) -> str:
    """Return a base64 data URI for the local dashboard header image."""

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def render_header() -> None:
    """Render the dashboard header image and forecast title."""

    if not HEADER_IMAGE.exists():
        st.title("Mars the Real Deal - January 2022 Forecast")
        st.caption("Forecast sign-off view for Sales and Supply Chain")
        return

    st.markdown(
        f"""
        <div class="hero-image" style="background-image:
            linear-gradient(90deg, rgba(38, 50, 56, 0.76) 0%, rgba(38, 50, 56, 0.42) 48%, rgba(38, 50, 56, 0.12) 100%),
            url('{image_data_uri(HEADER_IMAGE)}');">
            <div class="hero-copy">
                <h1>Mars the Real Deal - January 2022 Forecast</h1>
                <p>Forecast sign-off view for Sales and Supply Chain</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


data = load_dashboard_data()
weekly = data["weekly"]
forecast_summary = data["forecast_summary"]
weekly_scenarios = data["weekly_scenarios"]
period = data["period"]
promotion = data["promotion"]
metrics = data["metrics"]["metrics"]
recommendations = data["metrics"]["recommendations"]

apply_css()
render_header()


def polish_plotly(fig: go.Figure, height: int) -> go.Figure:
    """Apply the dashboard's light visual system to a Plotly figure."""

    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=55, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=INK),
        title_font=dict(color=INK),
        legend=dict(bgcolor="rgba(255,255,255,0)"),
    )
    fig.update_xaxes(gridcolor="#E5E7EB", zerolinecolor="#CBD5E1")
    fig.update_yaxes(gridcolor="#E5E7EB", zerolinecolor="#CBD5E1")
    return fig

scenario_options = forecast_summary["scenario"].tolist()
selected_scenario = st.sidebar.radio("Scenario", scenario_options, index=0)
show_ordered = st.sidebar.checkbox("Show estimated ordered demand", value=True)
show_promotions = st.sidebar.checkbox("Highlight promotions", value=True)
service_threshold = st.sidebar.slider("Casefill watchline", min_value=70, max_value=99, value=95, step=1)

selected_total = float(
    forecast_summary.loc[
        forecast_summary["scenario"].eq(selected_scenario), "total_forecast_k_cases"
    ].iloc[0]
)
base_total = float(
    forecast_summary.loc[
        forecast_summary["scenario"].eq("Base operational forecast"), "total_forecast_k_cases"
    ].iloc[0]
)
promo_total = float(
    forecast_summary.loc[
        forecast_summary["scenario"].eq("Signed two-week promo"), "total_forecast_k_cases"
    ].iloc[0]
)

st.markdown(
    f"""
    <div class="decision-box">
    <strong>Recommendation:</strong> {recommendations["official_forecast"]}
    <br><strong>Promotion gate:</strong> {recommendations["promo_gate"]}
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
kpi_1.metric("Selected January scenario", fmt_k(selected_total), delta=f"{selected_total - base_total:,.0f}k vs base")
kpi_2.metric("Factory baseline", fmt_k(base_total), delta="P13 clean run-rate")
kpi_3.metric("Signed promo gate", fmt_k(promo_total), delta="W2-W3 promotion")
kpi_4.metric("Late-year service loss", fmt_k(metrics["service_loss_k_cases"]), delta=f"{metrics['service_affected_weeks']} low-service weeks")

forecast_tab, drivers_tab, service_tab, signoff_tab = st.tabs(
    ["Forecast", "Demand Drivers", "Service Risk", "Sign-Off"]
)

with forecast_tab:
    left, right = st.columns([1.25, 1])
    with left:
        scenario_weekly = weekly_scenarios[weekly_scenarios["scenario"].eq(selected_scenario)]
        fig = px.line(
            scenario_weekly,
            x="week_of_period",
            y="forecast_k_cases",
            markers=True,
            color_discrete_sequence=[MARS_RED],
            labels={"week_of_period": "Week of period", "forecast_k_cases": "'000 cases"},
            title=f"{selected_scenario}: weekly phasing",
        )
        fig.update_traces(line=dict(width=4), marker=dict(size=10))
        polish_plotly(fig, 390)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(
            forecast_summary,
            x="total_forecast_k_cases",
            y="scenario",
            orientation="h",
            color="scenario",
            color_discrete_map={
                "Base operational forecast": TEAL,
                "Signed two-week promo": MARS_RED,
                "Sales upside sensitivity": GOLD,
            },
            labels={"total_forecast_k_cases": "'000 cases", "scenario": ""},
            title="Scenario totals",
        )
        polish_plotly(fig, 390)
        fig.update_layout(showlegend=False, margin=dict(l=10, r=20, t=55, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        scenario_weekly[
            ["target_period", "week_of_period", "forecast_k_cases", "assumption", "decision_use"]
        ],
        use_container_width=True,
        hide_index=True,
    )

with drivers_tab:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["forecast_k_cases"],
            mode="lines",
            name="Forecast",
            line=dict(color=GRAY, width=2.4),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["actual_k_cases"],
            mode="lines",
            name="Actual delivered",
            line=dict(color=MARS_RED, width=2.8),
        )
    )
    if show_ordered:
        fig.add_trace(
            go.Scatter(
                x=weekly["week"],
                y=weekly["estimated_ordered_k_cases"],
                mode="lines",
                name="Estimated ordered",
                line=dict(color=TEAL, width=2.2, dash="dot"),
            )
        )
    if show_promotions:
        promo = weekly[weekly["promo_flag"]]
        fig.add_trace(
            go.Scatter(
                x=promo["week"],
                y=promo["actual_k_cases"],
                mode="markers",
                name="Promotion week",
                marker=dict(color=GOLD, size=10, line=dict(color=INK, width=1)),
                text=promo["promotion_type"],
            )
        )
    polish_plotly(fig, 430)
    fig.update_layout(
        title="2021 forecast, delivered actuals, and demand signals",
        xaxis_title="Week",
        yaxis_title="'000 cases",
    )
    st.plotly_chart(fig, use_container_width=True)

    customer_data = promotion[promotion["promotion_type"].isin(["Customer 1", "Customer 2"])]
    fig = go.Figure()
    for _, row in customer_data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["min_ordered_k_cases"], row["max_ordered_k_cases"]],
                y=[row["promotion_type"], row["promotion_type"]],
                mode="lines",
                line=dict(color="#CBD5E1", width=13),
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[row["median_ordered_k_cases"]],
                y=[row["promotion_type"]],
                mode="markers+text",
                marker=dict(color=MARS_RED, size=13),
                text=[f"median {row['median_ordered_k_cases']:,.0f}"],
                textposition="middle right",
                showlegend=False,
            )
        )
    polish_plotly(fig, 270)
    fig.update_layout(
        title="Promotion demand range by customer",
        xaxis_title="Estimated ordered demand per promo week ('000 cases)",
    )
    st.plotly_chart(fig, use_container_width=True)

with service_tab:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["casefill_pct"],
            mode="lines",
            name="Casefill",
            line=dict(color=TEAL, width=3),
        )
    )
    fig.add_hline(
        y=service_threshold,
        line_dash="dash",
        line_color=MARS_RED,
        annotation_text=f"{service_threshold}% watchline",
        annotation_position="bottom right",
    )
    low = weekly[weekly["casefill_pct"] < service_threshold]
    fig.add_trace(
        go.Scatter(
            x=low["week"],
            y=low["casefill_pct"],
            mode="markers",
            name="Below watchline",
            marker=dict(color=MARS_RED, size=10),
        )
    )
    polish_plotly(fig, 420)
    fig.update_layout(
        title="Casefill risk: actuals need to be read with service context",
        xaxis_title="Week",
        yaxis_title="Casefill (%)",
        yaxis=dict(range=[65, 101]),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        period[
            [
                "period",
                "promotions",
                "forecast_k_cases",
                "actual_k_cases",
                "estimated_ordered_k_cases",
                "avg_casefill_pct",
                "service_loss_k_cases",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with signoff_tab:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Additional information needed")
        st.markdown(
            """
            - Customer and account owner.
            - Promotion mechanic, discount depth, feature/display plan, and exact weeks.
            - Expected weekly sell-in phasing and committed order quantity.
            - Any forward-buy, pantry-loading, or cannibalization risk.
            - Supply constraints, minimum casefill commitment, and contingency volume.
            """
        )
    with col_b:
        st.subheader("How to get Sales on board")
        st.markdown(
            """
            - Show base demand and promo upside as separate decisions.
            - Ask Sales to sign the customer-backed uplift, not just the ambition.
            - Align on a single forecast owner and a weekly order/casefill review.
            - Keep upside visible for capacity planning without loading uncommitted demand.
            """
        )

    st.subheader("Expected Sales behavior and follow-up")
    st.markdown(
        """
        Sales will likely push for the upside number because recent promotion weeks showed large peaks.
        Follow up with a weekly January control cycle: compare orders, shipments, casefill, and sell-in
        against the signed scenario; adjust the factory signal only when customer evidence changes.
        """
    )
