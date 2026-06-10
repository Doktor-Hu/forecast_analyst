"""Forecast logic and scenario generation for the Mars January discussion."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mars_forecast_case.config import TARGET_PERIOD, TARGET_WEEKS, TARGET_YEAR


@dataclass(frozen=True)
class ForecastScenario:
    """A weekly January forecast scenario in thousands of cases."""

    scenario: str
    weekly_forecast_k_cases: pd.Series
    assumption: str
    decision_use: str

    @property
    def total_k_cases(self) -> float:
        """Return the total scenario volume in thousands of cases."""

        return float(self.weekly_forecast_k_cases.sum())


def summarize_history(df: pd.DataFrame) -> dict[str, float]:
    """Create high-signal metrics for the executive forecast recommendation."""

    service_affected = df["casefill"] < 0.95
    recent_clean = recent_clean_base(df)
    promo = df[df["promo_flag"]]
    no_promo = df[~df["promo_flag"]]

    return {
        "source_year_actual_k_cases": float(df["actual_k_cases"].sum()),
        "source_year_forecast_k_cases": float(df["forecast_k_cases"].sum()),
        "source_year_estimated_ordered_k_cases": float(df["estimated_ordered_k_cases"].sum()),
        "source_year_forecast_bias_pct": float(
            (df["actual_k_cases"].sum() / df["forecast_k_cases"].sum() - 1) * 100
        ),
        "source_year_mape_pct": float(df["absolute_percentage_error"].mean() * 100),
        "promo_week_count": int(promo.shape[0]),
        "non_promo_week_count": int(no_promo.shape[0]),
        "customer_1_promo_median_ordered_k_cases": float(
            promo.loc[promo["promotion_type"].eq("Customer 1"), "estimated_ordered_k_cases"].median()
        ),
        "customer_2_promo_median_ordered_k_cases": float(
            promo.loc[promo["promotion_type"].eq("Customer 2"), "estimated_ordered_k_cases"].median()
        ),
        "recent_clean_weekly_median_ordered_k_cases": float(
            recent_clean["estimated_ordered_k_cases"].median()
        ),
        "recent_clean_weekly_mean_ordered_k_cases": float(
            recent_clean["estimated_ordered_k_cases"].mean()
        ),
        "service_affected_weeks": int(service_affected.sum()),
        "service_loss_k_cases": float(df.loc[service_affected, "service_loss_k_cases"].sum()),
        "p13_estimated_ordered_k_cases": float(
            df.loc[df["period"].eq("P13"), "estimated_ordered_k_cases"].sum()
        ),
        "p01_2021_estimated_ordered_k_cases": float(
            df.loc[df["period"].eq("P01"), "estimated_ordered_k_cases"].sum()
        ),
    }


def recent_clean_base(df: pd.DataFrame) -> pd.DataFrame:
    """Return recent non-promotion weeks with healthy service levels.

    The case is set in December 2021. P10-P13 give the most recent read on
    underlying demand, but low-service weeks and promotions should not be used
    as a clean base.
    """

    mask = (df["period_number"] >= 10) & (~df["promo_flag"]) & (df["casefill"] >= 0.95)
    recent = df.loc[mask].copy()
    if recent.empty:
        recent = df.loc[(~df["promo_flag"]) & (df["casefill"] >= 0.95)].copy()
    return recent


def base_weekly_forecast(df: pd.DataFrame) -> pd.Series:
    """Build a no-promotion January forecast by week of period.

    P13 is the cleanest recent four-week demand read: no promotion flags and
    normal casefill. If a future workbook lacks a clean P13, the fallback uses
    recent clean week-of-period medians and then the overall recent median.
    """

    p13 = df.loc[
        df["period"].eq("P13") & (~df["promo_flag"]) & (df["casefill"] >= 0.95),
        ["week_of_period", "estimated_ordered_k_cases"],
    ].copy()
    base = p13.set_index("week_of_period")["estimated_ordered_k_cases"].reindex(TARGET_WEEKS)

    if base.isna().any():
        recent = recent_clean_base(df)
        by_week = recent.groupby("week_of_period")["estimated_ordered_k_cases"].median()
        base = base.fillna(by_week)
        base = base.fillna(recent["estimated_ordered_k_cases"].median())

    base.name = "forecast_k_cases"
    return base


def promotion_week_demand(df: pd.DataFrame, promotion_type: str = "Customer 1") -> float:
    """Estimate typical ordered demand for a promotion week.

    Customer 1 has the steadier historical promotion profile in the case data.
    Customer 2 contains two exceptional late-year spikes, so its median is
    conservative and its upper quartile is used only as an upside reference.
    """

    promo = df.loc[df["promotion_type"].eq(promotion_type), "estimated_ordered_k_cases"]
    if promo.empty:
        promo = df.loc[df["promo_flag"], "estimated_ordered_k_cases"]
    return float(promo.median())


def upside_promo_week_demand(df: pd.DataFrame) -> float:
    """Return a high-but-not-maximum promotion demand reference."""

    promo = df.loc[df["promo_flag"], "estimated_ordered_k_cases"]
    return float(promo.quantile(0.75))


def build_january_scenarios(df: pd.DataFrame) -> list[ForecastScenario]:
    """Create base, signed-promotion, and sales-upside January scenarios."""

    base = base_weekly_forecast(df)

    signed_promo = base.copy()
    typical_customer_1 = promotion_week_demand(df, "Customer 1")
    signed_promo.loc[["W2", "W3"]] = typical_customer_1

    upside = base.copy()
    upside.loc[["W2", "W3"]] = upside_promo_week_demand(df)

    return [
        ForecastScenario(
            scenario="Base operational forecast",
            weekly_forecast_k_cases=base,
            assumption=(
                "No January promotion is loaded. Uses clean P13 estimated ordered demand "
                "as the latest normal demand read."
            ),
            decision_use="Factory baseline and sign-off number unless a promotion is formally confirmed.",
        ),
        ForecastScenario(
            scenario="Signed two-week promo",
            weekly_forecast_k_cases=signed_promo,
            assumption=(
                "W2-W3 promotion replaces base weeks with the median historical Customer 1 "
                "promotion demand."
            ),
            decision_use="Use only after customer, mechanic, dates, display, and volume commitment are signed.",
        ),
        ForecastScenario(
            scenario="Sales upside sensitivity",
            weekly_forecast_k_cases=upside,
            assumption=(
                "W2-W3 promotion uses the 75th percentile of all observed promotion demand, "
                "excluding a full repeat of the highest Customer 2 spike."
            ),
            decision_use="Capacity and risk conversation, not the default factory forecast.",
        ),
    ]


def scenario_frame(scenarios: list[ForecastScenario]) -> pd.DataFrame:
    """Convert scenarios into a rectangular weekly table."""

    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        for week_of_period, value in scenario.weekly_forecast_k_cases.items():
            rows.append(
                {
                    "target_year": TARGET_YEAR,
                    "target_period": TARGET_PERIOD,
                    "week_of_period": week_of_period,
                    "scenario": scenario.scenario,
                    "forecast_k_cases": float(value),
                    "assumption": scenario.assumption,
                    "decision_use": scenario.decision_use,
                }
            )
    return pd.DataFrame(rows)


def scenario_summary_frame(scenarios: list[ForecastScenario]) -> pd.DataFrame:
    """Return one row per scenario with total volume and recommendation text."""

    return pd.DataFrame(
        [
            {
                "scenario": scenario.scenario,
                "total_forecast_k_cases": scenario.total_k_cases,
                "assumption": scenario.assumption,
                "decision_use": scenario.decision_use,
            }
            for scenario in scenarios
        ]
    )


def promotion_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize observed promotion demand by customer."""

    promo = df[df["promo_flag"]].copy()
    summary = (
        promo.groupby("promotion_type", dropna=False)
        .agg(
            weeks=("week", "count"),
            median_ordered_k_cases=("estimated_ordered_k_cases", "median"),
            mean_ordered_k_cases=("estimated_ordered_k_cases", "mean"),
            min_ordered_k_cases=("estimated_ordered_k_cases", "min"),
            max_ordered_k_cases=("estimated_ordered_k_cases", "max"),
            median_forecast_k_cases=("forecast_k_cases", "median"),
            median_actual_k_cases=("actual_k_cases", "median"),
        )
        .reset_index()
        .sort_values("median_ordered_k_cases", ascending=False)
    )
    return summary


def period_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize forecast, actuals, service, and promotion count by period."""

    summary = (
        df.groupby(["period_number", "period"], as_index=False)
        .agg(
            weeks=("week", "count"),
            promotions=("promo_flag", "sum"),
            forecast_k_cases=("forecast_k_cases", "sum"),
            actual_k_cases=("actual_k_cases", "sum"),
            estimated_ordered_k_cases=("estimated_ordered_k_cases", "sum"),
            avg_casefill_pct=("casefill_pct", "mean"),
            service_loss_k_cases=("service_loss_k_cases", "sum"),
        )
        .sort_values("period_number")
    )
    summary["actual_vs_forecast_pct"] = (
        summary["actual_k_cases"] / summary["forecast_k_cases"] - 1
    ) * 100
    summary["ordered_vs_forecast_pct"] = (
        summary["estimated_ordered_k_cases"] / summary["forecast_k_cases"] - 1
    ) * 100
    return summary


def recommendation_text(
    summary: dict[str, float], signed_promo_total_k_cases: float | None = None
) -> dict[str, str]:
    """Return concise business recommendations for the dashboard and slides."""

    base_total = summary["p13_estimated_ordered_k_cases"]
    c1_median = summary["customer_1_promo_median_ordered_k_cases"]
    uplift = c1_median - summary["recent_clean_weekly_median_ordered_k_cases"]
    promo_total = signed_promo_total_k_cases or (base_total + uplift * 2)

    return {
        "official_forecast": (
            f"Recommend {base_total:,.0f}k cases as the January factory baseline "
            "until promotion mechanics and customer volume are signed."
        ),
        "promo_gate": (
            f"If Sales secures a two-week Customer 1-like event, move to roughly "
            f"{promo_total:,.0f}k cases and lock W2-W3 supply before sign-off."
        ),
        "sales_alignment": (
            "Ask Sales for customer, mechanic, display support, expected weekly phasing, "
            "committed orders, cannibalization, and a fallback plan if casefill risk appears."
        ),
    }
