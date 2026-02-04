# Excel Reporter
Excel Data Profiler + HTML Dashboard

Excel Reporter is a desktop tool that analyzes Excel files (including messy and non-standard ones) and generates:
- A structured Excel report (tables, summaries, quality checks)
- A modern HTML report with a mini dashboard (charts)

Built with Python, Pandas, Tkinter, Jinja2 and Chart.js.

---

## Features

### Core Features
- Desktop UI built with Tkinter
- Select Excel files via file picker
- Supports large Excel files using sampling
- Generates:
  - Excel report (.xlsx)
  - HTML dashboard report (.html)

---

### Automatic Header Detection (v1.1)
- Detects the real header row even if it is not the first row
- Handles messy Excel sheets with empty rows or fake headers
- Uses heuristics:
  - non-empty cell count
  - text ratio and uniqueness
  - penalties for fake headers (Column1, Unnamed)
  - penalties for empty rows after header
- Provides a confidence score

---

### HTML Dashboard (v1.2)
- Interactive charts powered by Chart.js
- Sheet-based row count visualization
- Top missing columns (Top 10)
- Clean, minimal and readable layout

---

## Project Structure

```text
excel_reporter/
  app/
    core.py                # main pipeline
    gui.py                 # Tkinter UI
    excel_reader.py        # Excel reader + auto header detection
    header_detector.py     # header detection logic
    profiler.py            # column profiling
    quality_checks.py      # data quality checks
    report_html.py         # HTML report generator (Jinja2)
    report_xlsx.py         # Excel report generator
    utils.py               # helper utilities
  templates/
    report_template.html   # HTML report template
  output/                  # generated reports (gitignored)
  requirements.txt
  README.md
---





  