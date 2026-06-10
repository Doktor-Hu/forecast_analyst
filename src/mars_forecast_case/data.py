"""Load and normalize the case brief and supporting Excel workbook."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


from mars_forecast_case.config import BRIEF_PATH, EXCEL_PATH


@dataclass(frozen=True)
class CaseMetadata:
    """Metadata extracted from the supporting workbook."""

    product: str
    source_year: int
    source_file: Path




def load_supporting_data(path: Path = EXCEL_PATH) -> tuple[pd.DataFrame, CaseMetadata]:
    """Normalize the wide weekly worksheet into one record per week.

    The source workbook stores measures as rows and weeks as columns. This
    function converts that layout into a tidy time series and adds fields that
    are useful for forecast analysis:
    forecast, delivered actuals, casefill-corrected ordered demand, promotion
    flags, service loss, and forecast error.
    """

    raw = pd.read_excel(path, sheet_name="Supporting Data", header=None)

    product = str(raw.iloc[1, 1]).strip()
    source_year = int(raw.iloc[2, 1])
    week_cols = list(range(1, 53))

    data = pd.DataFrame(
        {
            "year": source_year,
            "week": pd.to_numeric(raw.iloc[3, week_cols]).astype(int).to_numpy(),
            "period": raw.iloc[4, week_cols].astype(str).to_numpy(),
            "week_of_period": raw.iloc[5, week_cols].astype(str).to_numpy(),
            "forecast_k_cases": pd.to_numeric(raw.iloc[6, week_cols]).to_numpy(),
            "customer_1_promo": raw.iloc[7, week_cols].eq("X").to_numpy(),
            "customer_2_promo": raw.iloc[8, week_cols].eq("X").to_numpy(),
            "actual_k_cases": pd.to_numeric(raw.iloc[9, week_cols]).to_numpy(),
            "casefill": pd.to_numeric(raw.iloc[10, week_cols]).to_numpy(),
        }
    )

    data["period_number"] = data["period"].str.replace("P", "", regex=False).astype(int)
    data["promo_flag"] = data["customer_1_promo"] | data["customer_2_promo"]
    data["promotion_type"] = np.select(
        [
            data["customer_1_promo"] & data["customer_2_promo"],
            data["customer_1_promo"],
            data["customer_2_promo"],
        ],
        ["Both customers", "Customer 1", "Customer 2"],
        default="No promotion",
    )
    data["estimated_ordered_k_cases"] = data["actual_k_cases"] / data["casefill"]
    data["service_loss_k_cases"] = data["estimated_ordered_k_cases"] - data["actual_k_cases"]
    data["forecast_error_k_cases"] = data["actual_k_cases"] - data["forecast_k_cases"]
    data["forecast_error_pct"] = data["forecast_error_k_cases"] / data["forecast_k_cases"]
    data["absolute_percentage_error"] = (
        data["forecast_error_k_cases"].abs() / data["actual_k_cases"].replace(0, np.nan)
    )
    data["casefill_pct"] = data["casefill"] * 100

    monday_dates = pd.to_datetime(
        data["year"].astype(str) + "-W" + data["week"].astype(str).str.zfill(2) + "-1",
        format="%G-W%V-%u",
    )
    data["week_start"] = monday_dates

    metadata = CaseMetadata(product=product, source_year=source_year, source_file=path)
    return data, metadata


def write_normalized_data(df: pd.DataFrame, output_path: Path) -> Path:
    """Persist normalized weekly data for notebooks, dashboard, and QA."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path
