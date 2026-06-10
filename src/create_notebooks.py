"""Generate the Mars forecast case Jupyter notebooks."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebook"


def code(source: str) -> nbf.NotebookNode:
    """Create a Python code cell."""

    return nbf.v4.new_code_cell(dedent(source).strip() + "\n")


def markdown(source: str) -> nbf.NotebookNode:
    """Create a Markdown cell."""

    return nbf.v4.new_markdown_cell(dedent(source).strip())


def build_exploration_notebook() -> nbf.NotebookNode:
    """Build the exploratory data analysis notebook."""

    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3 (Mars forecast case)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    nb["cells"] = [
        markdown(
            """
            # Mars Forecast Analyst Case - Data Exploration

            Objective: understand the weekly forecast, actual delivered cases, promotion flags,
            and casefill signals before proposing a January 2022 forecast.
            """
        ),
        code(
            """
            \"\"\"Set up imports, paths, and the shared Mars forecast pipeline.\"\"\"

            from pathlib import Path
            import sys

            import matplotlib.pyplot as plt
            import pandas as pd
            import seaborn as sns

            PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebook" else Path.cwd()
            SRC_DIR = PROJECT_ROOT / "src"
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))

            from mars_forecast_case.pipeline import build_outputs

            sns.set_theme(style="whitegrid")
            """
        ),
        code(
            """
            def load_analysis_tables(project_root: Path) -> dict[str, pd.DataFrame]:
                \"\"\"Rebuild pipeline outputs and load the analyst-facing tables.\"\"\"

                build_outputs(project_root / "outputs")
                outputs = project_root / "outputs"
                return {
                    "weekly": pd.read_csv(outputs / "weekly_clean_data.csv", parse_dates=["week_start"]),
                    "period": pd.read_csv(outputs / "period_summary.csv"),
                    "promotion": pd.read_csv(outputs / "promotion_summary.csv"),
                    "forecast": pd.read_csv(outputs / "forecast_summary.csv"),
                }


            tables = load_analysis_tables(PROJECT_ROOT)
            weekly = tables["weekly"]
            period = tables["period"]
            promotion = tables["promotion"]
            forecast = tables["forecast"]

            weekly.head()
            """
        ),
        markdown(
            """
            ## Initial Read

            The workbook contains 52 weekly observations for one product in 2021.
            The important fields are the existing forecast, delivered actuals, customer promotion flags,
            and casefill. Because casefill is delivered cases divided by ordered cases, delivered actuals
            should be corrected to estimated ordered demand before judging demand strength.
            """
        ),
        code(
            """
            def summarize_data_quality(df: pd.DataFrame) -> pd.DataFrame:
                \"\"\"Summarize service, promotion, and forecast accuracy indicators.\"\"\"

                return pd.DataFrame(
                    {
                        "metric": [
                            "weeks",
                            "promotion weeks",
                            "weeks below 95% casefill",
                            "total actual delivered ('000)",
                            "total estimated ordered ('000)",
                            "total forecast ('000)",
                            "mean absolute percentage error",
                        ],
                        "value": [
                            len(df),
                            int(df["promo_flag"].sum()),
                            int((df["casefill"] < 0.95).sum()),
                            round(df["actual_k_cases"].sum(), 1),
                            round(df["estimated_ordered_k_cases"].sum(), 1),
                            round(df["forecast_k_cases"].sum(), 1),
                            f"{df['absolute_percentage_error'].mean() * 100:.1f}%",
                        ],
                    }
                )


            summarize_data_quality(weekly)
            """
        ),
        code(
            """
            \"\"\"Visualize forecast versus delivered actuals and identify promotion weeks.\"\"\"

            fig, ax = plt.subplots(figsize=(13, 5))
            ax.plot(weekly["week"], weekly["forecast_k_cases"], label="Forecast", color="#6B7280", linewidth=2)
            ax.plot(weekly["week"], weekly["actual_k_cases"], label="Actual delivered", color="#9E1B32", linewidth=2.2)
            promo = weekly[weekly["promo_flag"]]
            ax.scatter(promo["week"], promo["actual_k_cases"], label="Promotion week", color="#F2A900", edgecolor="#263238", s=55, zorder=5)
            ax.set_title("Weekly forecast versus actual delivered cases")
            ax.set_xlabel("Week")
            ax.set_ylabel("'000 cases")
            ax.legend(frameon=False, ncols=3, loc="upper left")
            plt.show()
            """
        ),
        code(
            """
            \"\"\"Show where actuals understate ordered demand because service levels fell.\"\"\"

            fig, ax = plt.subplots(figsize=(13, 4))
            ax.plot(weekly["week"], weekly["casefill_pct"], color="#007A78", linewidth=2.3)
            ax.axhline(95, color="#9E1B32", linestyle="--", linewidth=1.4, label="95% service watchline")
            low = weekly[weekly["casefill_pct"] < 95]
            ax.scatter(low["week"], low["casefill_pct"], color="#9E1B32", s=60, label="Low casefill", zorder=5)
            ax.set_ylim(65, 101)
            ax.set_title("Casefill fell sharply in late 2021")
            ax.set_xlabel("Week")
            ax.set_ylabel("Casefill (%)")
            ax.legend(frameon=False, loc="lower left")
            plt.show()
            """
        ),
        code(
            """
            \"\"\"Review period-level bias, service loss, and promotion concentration.\"\"\"

            display(period)

            fig, ax = plt.subplots(figsize=(12, 4.5))
            ax.bar(period["period"], period["estimated_ordered_k_cases"], color="#007A78", alpha=0.85, label="Estimated ordered")
            ax.plot(period["period"], period["forecast_k_cases"], color="#9E1B32", marker="o", label="Forecast")
            ax.set_title("Period demand after correcting delivered actuals for casefill")
            ax.set_ylabel("'000 cases")
            ax.tick_params(axis="x", rotation=45)
            ax.legend(frameon=False)
            plt.show()
            """
        ),
        code(
            """
            \"\"\"Compare promotion demand ranges by customer.\"\"\"

            display(promotion)

            data = promotion[promotion["promotion_type"].isin(["Customer 1", "Customer 2"])].copy()
            fig, ax = plt.subplots(figsize=(9, 4))
            for idx, row in data.reset_index(drop=True).iterrows():
                ax.hlines(idx, row["min_ordered_k_cases"], row["max_ordered_k_cases"], color="#CBD5E1", linewidth=8)
                ax.scatter(row["median_ordered_k_cases"], idx, color="#9E1B32", s=80, zorder=4)
                ax.text(row["median_ordered_k_cases"] + 10, idx, f\"median {row['median_ordered_k_cases']:.0f}\", va="center")
            ax.set_yticks(range(len(data)), data["promotion_type"])
            ax.set_xlabel("Estimated ordered demand per promo week ('000 cases)")
            ax.set_title("Customer promotion history is valuable, but variable")
            plt.show()
            """
        ),
        markdown(
            """
            ## Exploration Takeaways

            - P13 is the cleanest recent base read: no promotions and normal casefill.
            - P12 delivered actuals are not a good base because service was constrained.
            - Customer 1 promotions are steadier; Customer 2 has a much wider range and two extreme late-year weeks.
            - January sign-off should therefore separate a factory baseline from a signed-promotion scenario.
            """
        ),
    ]
    return nb


def build_forecast_notebook() -> nbf.NotebookNode:
    """Build the forecast modeling and recommendation notebook."""

    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3 (Mars forecast case)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    nb["cells"] = [
        markdown(
            """
            # Mars Forecast Analyst Case - January Forecast Recommendation

            This notebook turns the exploration into a forecast position for the Sales and Supply Chain meeting.
            """
        ),
        code(
            """
            \"\"\"Load reusable forecast functions and generated outputs.\"\"\"

            from pathlib import Path
            import json
            import sys

            import matplotlib.pyplot as plt
            import pandas as pd
            import seaborn as sns

            PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebook" else Path.cwd()
            SRC_DIR = PROJECT_ROOT / "src"
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))

            from mars_forecast_case.data import load_supporting_data
            from mars_forecast_case.forecast import (
                base_weekly_forecast,
                build_january_scenarios,
                recent_clean_base,
                scenario_frame,
                scenario_summary_frame,
                summarize_history,
            )
            from mars_forecast_case.pipeline import build_outputs

            sns.set_theme(style="whitegrid")
            build_outputs(PROJECT_ROOT / "outputs")
            weekly, metadata = load_supporting_data()
            """
        ),
        markdown(
            """
            ## Forecast Principle

            The operational forecast for the factory should include committed demand, not Sales optimism.
            A promotion belongs in the official number only once the customer, mechanics, dates, expected phasing,
            and supply feasibility are confirmed.
            """
        ),
        code(
            """
            def compare_base_reads(df: pd.DataFrame) -> pd.DataFrame:
                \"\"\"Compare plausible base-demand anchors for January 2022.\"\"\"

                recent = recent_clean_base(df)
                return pd.DataFrame(
                    {
                        "base_read": [
                            "P01 2021 estimated ordered demand",
                            "P13 2021 estimated ordered demand",
                            "Recent clean weekly median x 4",
                            "Recent clean weekly mean x 4",
                        ],
                        "forecast_k_cases": [
                            df.loc[df["period"].eq("P01"), "estimated_ordered_k_cases"].sum(),
                            df.loc[df["period"].eq("P13"), "estimated_ordered_k_cases"].sum(),
                            recent["estimated_ordered_k_cases"].median() * 4,
                            recent["estimated_ordered_k_cases"].mean() * 4,
                        ],
                        "comment": [
                            "Direct January analogy but one year old.",
                            "Latest clean four-week period with normal service.",
                            "Robust recent base, ignores weekly phasing.",
                            "Recent base but more sensitive to high weeks.",
                        ],
                    }
                )


            base_reads = compare_base_reads(weekly)
            base_reads
            """
        ),
        code(
            """
            \"\"\"Build weekly January scenarios from the reusable model.\"\"\"

            scenarios = build_january_scenarios(weekly)
            scenario_weekly = scenario_frame(scenarios)
            scenario_summary = scenario_summary_frame(scenarios)
            display(scenario_weekly)
            display(scenario_summary)
            """
        ),
        code(
            """
            \"\"\"Visualize the weekly shape of each January scenario.\"\"\"

            fig, ax = plt.subplots(figsize=(10, 5))
            for scenario, data in scenario_weekly.groupby("scenario"):
                ax.plot(data["week_of_period"], data["forecast_k_cases"], marker="o", linewidth=2.4, label=scenario)
            ax.set_title("January 2022 weekly forecast scenarios")
            ax.set_xlabel("Week of period")
            ax.set_ylabel("'000 cases")
            ax.legend(frameon=False)
            plt.show()
            """
        ),
        code(
            """
            \"\"\"Visualize scenario totals for the Sales and Supply Chain sign-off discussion.\"\"\"

            colors = ["#007A78", "#9E1B32", "#F2A900"]
            fig, ax = plt.subplots(figsize=(9, 4.5))
            ax.barh(scenario_summary["scenario"], scenario_summary["total_forecast_k_cases"], color=colors)
            for idx, row in scenario_summary.iterrows():
                ax.text(row["total_forecast_k_cases"] + 20, idx, f\"{row['total_forecast_k_cases']:.0f}\", va="center")
            ax.set_title("Recommended forecast separates base from promo upside")
            ax.set_xlabel("'000 cases")
            plt.show()
            """
        ),
        code(
            """
            \"\"\"Create the final meeting recommendation and information request.\"\"\"

            metrics = summarize_history(weekly)
            signed_total = float(
                scenario_summary.loc[
                    scenario_summary["scenario"].eq("Signed two-week promo"),
                    "total_forecast_k_cases",
                ].iloc[0]
            )

            recommendation = pd.DataFrame(
                {
                    "topic": [
                        "Factory forecast to sign off",
                        "Promotion gate",
                        "Additional information needed",
                        "Sales follow-up",
                    ],
                    "position": [
                        f\"Use {metrics['p13_estimated_ordered_k_cases']:.0f}k cases as the no-promo January baseline.\",
                        f\"Move to {signed_total:.0f}k cases only for a signed two-week event with confirmed weekly phasing.\",
                        "Customer, mechanic, discount/display support, committed orders, cannibalization, and supply feasibility.",
                        "Ask Sales to own the customer volume assumption and review actual orders/casefill weekly during January.",
                    ],
                }
            )
            recommendation
            """
        ),
        markdown(
            """
            ## Forecast Decision

            Recommend **856k cases** as the January 2022 factory baseline.
            If Sales secures a confirmed two-week Customer 1-like promotion, prepare the factory for **1,144k cases**,
            with W2-W3 as the constrained weeks. Keep the larger Sales upside sensitivity as a capacity-risk discussion,
            not as the default operational forecast.
            """
        ),
    ]
    return nb


def main() -> None:
    """Write both notebooks to the notebook directory."""

    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    notebooks = {
        "01_data_exploration.ipynb": build_exploration_notebook(),
        "02_forecast_modeling.ipynb": build_forecast_notebook(),
    }
    for filename, notebook in notebooks.items():
        nbf.write(notebook, NOTEBOOK_DIR / filename)
        print(f"Wrote {NOTEBOOK_DIR / filename}")


if __name__ == "__main__":
    main()
