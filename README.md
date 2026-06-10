# Mars Forecast Analyst Case

This project prepares the January 2022 forecast discussion for Mars the Real Deal.

## Quick Start

```powershell
# From C:\Users\41646\Documents\JobApplications\Mars
.\.venv\Scripts\python.exe src\run_forecast.py
.\.venv\Scripts\streamlit.exe run app\app.py
```

The core pipeline normalizes the workbook, corrects delivered actuals to estimated ordered demand using casefill, separates base demand from promotion demand, and writes forecast-ready outputs to `outputs/`.

## Project Structure

- `docs/`: Original case brief and Excel workbook.
- `src/`: Reusable data, forecast, visualization, and pipeline code.
- `notebook/`: Jupyter notebooks for EDA and forecast modeling.
- `app/`: Streamlit dashboard.
- `delivery/`: PowerPoint delivery deck.
