"""Chart builders used by the pipeline, notebooks, dashboard, and deck."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


MARS_RED = "#9E1B32"
INK = "#263238"
GOLD = "#F2A900"
TEAL = "#007A78"
GRAY = "#6B7280"


def set_theme() -> None:
    """Apply a restrained business-analysis chart style."""

    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
        }
    )


def save_weekly_actual_forecast_chart(df: pd.DataFrame, path: Path) -> Path:
    """Save a weekly actual-vs-forecast chart with promotion markers."""

    set_theme()
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(df["week"], df["forecast_k_cases"], color=GRAY, linewidth=2, label="Forecast")
    ax.plot(df["week"], df["actual_k_cases"], color=MARS_RED, linewidth=2.3, label="Actual delivered")

    promo = df[df["promo_flag"]]
    ax.scatter(
        promo["week"],
        promo["actual_k_cases"],
        color=GOLD,
        edgecolor=INK,
        s=52,
        zorder=5,
        label="Promotion week",
    )

    ax.set_title("2021 weekly forecast vs actuals")
    ax.set_xlabel("Week")
    ax.set_ylabel("Cases ('000)")
    ax.legend(loc="upper left", frameon=False, ncols=3)
    ax.margins(x=0.01)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def save_casefill_chart(df: pd.DataFrame, path: Path) -> Path:
    """Save a casefill chart highlighting late-year service risk."""

    set_theme()
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(df["week"], df["casefill_pct"], color=TEAL, linewidth=2.2)
    ax.axhline(95, color=MARS_RED, linestyle="--", linewidth=1.3, label="95% service watchline")
    low = df[df["casefill_pct"] < 95]
    ax.scatter(low["week"], low["casefill_pct"], color=MARS_RED, s=58, zorder=5, label="Low casefill")
    ax.set_ylim(65, 101)
    ax.set_title("Casefill shows delivered actuals were constrained in late 2021")
    ax.set_xlabel("Week")
    ax.set_ylabel("Casefill (%)")
    ax.legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def save_promotion_summary_chart(promo_summary: pd.DataFrame, path: Path) -> Path:
    """Save a promotion demand range chart by customer."""

    set_theme()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = promo_summary[promo_summary["promotion_type"].ne("Both customers")].copy()

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    y = range(len(data))
    ax.hlines(
        y=y,
        xmin=data["min_ordered_k_cases"],
        xmax=data["max_ordered_k_cases"],
        color="#CBD5E1",
        linewidth=8,
        zorder=1,
    )
    ax.scatter(data["median_ordered_k_cases"], y, color=MARS_RED, s=80, zorder=3)
    for row_index, (_, row) in enumerate(data.iterrows()):
        ax.text(
            row["median_ordered_k_cases"] + 10,
            row_index,
            f"median {row['median_ordered_k_cases']:,.0f}",
            va="center",
            color=INK,
            fontsize=10,
        )
    ax.set_yticks(list(y), data["promotion_type"])
    ax.set_xlabel("Estimated ordered demand per promo week ('000 cases)")
    ax.set_title("Promotion outcomes are material, but customer variability matters")
    ax.set_xlim(data["min_ordered_k_cases"].min() - 25, data["max_ordered_k_cases"].max() + 35)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def save_scenario_chart(scenario_summary: pd.DataFrame, path: Path) -> Path:
    """Save a scenario total bar chart for January forecast sign-off."""

    set_theme()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = scenario_summary.copy()
    colors = [TEAL, MARS_RED, GOLD]

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    bars = ax.barh(data["scenario"], data["total_forecast_k_cases"], color=colors[: len(data)])
    ax.set_xlabel("January 2022 forecast ('000 cases)")
    ax.set_title("January forecast should separate committed base from promo upside")
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 18, bar.get_y() + bar.get_height() / 2, f"{width:,.0f}", va="center")
    ax.set_xlim(0, max(data["total_forecast_k_cases"]) * 1.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path
