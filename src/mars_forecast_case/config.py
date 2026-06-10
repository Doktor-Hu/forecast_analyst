"""Central paths used by the Mars forecast case project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOK_DIR = PROJECT_ROOT / "notebook"
APP_DIR = PROJECT_ROOT / "app"
DELIVERY_DIR = PROJECT_ROOT / "delivery"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"

BRIEF_PATH = DOCS_DIR / "Business Case - Forecast Analyst.docx"
EXCEL_PATH = DOCS_DIR / "Business Case - Forecast Analyst.xlsx"

TARGET_YEAR = 2022
TARGET_PERIOD = "P01"
TARGET_WEEKS = ["W1", "W2", "W3", "W4"]
