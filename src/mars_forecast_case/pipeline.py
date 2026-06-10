"""End-to-end pipeline for the Mars forecast case deliverables."""

from __future__ import annotations

import json
from pathlib import Path

from mars_forecast_case.config import CHART_DIR, OUTPUT_DIR
from mars_forecast_case.data import load_supporting_data, read_case_brief, write_normalized_data
from mars_forecast_case.forecast import (
    build_january_scenarios,
    build_promotion_combination_scenarios,
    forecast_error_summary,
    period_summary,
    promotion_combination_summary,
    promotion_summary,
    recommendation_text,
    scenario_frame,
    scenario_summary_frame,
    summarize_history,
    weekly_error_analysis,
)
from mars_forecast_case.visualize import (
    save_casefill_chart,
    save_promotion_summary_chart,
    save_scenario_chart,
    save_weekly_actual_forecast_chart,
)


def build_outputs(output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    """Run the complete analysis pipeline and return generated artifact paths."""

    output_dir.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    brief = read_case_brief()
    df, metadata = load_supporting_data()
    scenarios = build_january_scenarios(df)
    weekly_scenarios = scenario_frame(scenarios)
    scenario_summary = scenario_summary_frame(scenarios)
    promotion_combinations = build_promotion_combination_scenarios(df)
    promotion_combinations_summary = promotion_combination_summary(promotion_combinations)
    weekly_errors = weekly_error_analysis(df)
    error_summary = forecast_error_summary(df)
    period = period_summary(df)
    promo = promotion_summary(df)
    metrics = summarize_history(df)
    signed_promo_total = float(
        scenario_summary.loc[
            scenario_summary["scenario"].eq("Signed two-week promo"),
            "total_forecast_k_cases",
        ].iloc[0]
    )
    recommendations = recommendation_text(metrics, signed_promo_total)

    artifacts = {
        "normalized_data": write_normalized_data(df, output_dir / "weekly_clean_data.csv"),
        "weekly_scenarios": output_dir / "january_forecast_scenarios.csv",
        "scenario_summary": output_dir / "forecast_summary.csv",
        "promotion_combinations": output_dir / "promotion_combination_scenarios.csv",
        "promotion_combination_summary": output_dir / "promotion_combination_summary.csv",
        "weekly_error_analysis": output_dir / "weekly_error_analysis.csv",
        "forecast_error_summary": output_dir / "forecast_error_summary.csv",
        "period_summary": output_dir / "period_summary.csv",
        "promotion_summary": output_dir / "promotion_summary.csv",
        "metrics": output_dir / "key_metrics.json",
        "brief": output_dir / "case_brief.txt",
        "weekly_chart": CHART_DIR / "weekly_actual_vs_forecast.png",
        "casefill_chart": CHART_DIR / "casefill_service_risk.png",
        "promotion_chart": CHART_DIR / "promotion_demand_ranges.png",
        "scenario_chart": CHART_DIR / "january_scenario_totals.png",
    }

    weekly_scenarios.to_csv(artifacts["weekly_scenarios"], index=False)
    scenario_summary.to_csv(artifacts["scenario_summary"], index=False)
    promotion_combinations.to_csv(artifacts["promotion_combinations"], index=False)
    promotion_combinations_summary.to_csv(
        artifacts["promotion_combination_summary"], index=False
    )
    weekly_errors.to_csv(artifacts["weekly_error_analysis"], index=False)
    error_summary.to_csv(artifacts["forecast_error_summary"], index=False)
    period.to_csv(artifacts["period_summary"], index=False)
    promo.to_csv(artifacts["promotion_summary"], index=False)
    artifacts["brief"].write_text(brief, encoding="utf-8")
    artifacts["metrics"].write_text(
        json.dumps(
            {
                "metadata": {
                    "product": metadata.product,
                    "source_year": metadata.source_year,
                    "source_file": str(metadata.source_file),
                },
                "metrics": metrics,
                "recommendations": recommendations,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    save_weekly_actual_forecast_chart(df, artifacts["weekly_chart"])
    save_casefill_chart(df, artifacts["casefill_chart"])
    save_promotion_summary_chart(promo, artifacts["promotion_chart"])
    save_scenario_chart(scenario_summary, artifacts["scenario_chart"])

    return artifacts


def main() -> None:
    """CLI entry point for rebuilding all generated forecast outputs."""

    artifacts = build_outputs()
    print("Mars Forecast Analyst case outputs rebuilt:")
    for name, path in artifacts.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
