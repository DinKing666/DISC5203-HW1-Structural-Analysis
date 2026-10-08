# DISC 5203 Homework 1 - AI-Assisted Structural Analysis

This repository contains a reproducible tributary-area and gravity-load analysis for **Floor Plan 1** for Shuhan He, student ID **21345221**. The source assignment and images are preserved unchanged.

## Quick start

```powershell
Set-Location HW1
python -m pip install -r requirements-HW1.txt
python scripts/analyze_floor_plan.py
python scripts/build_report.py
python scripts/render_report_pdf.py
python scripts/verify_outputs.py
```

Primary deliverables:

- `report/21345221-report-HW1.md` - required Markdown report
- `output/pdf/21345221-report-HW1.pdf` - submission-ready PDF convenience copy
- `output/results/element_loads.csv` - numerical results
- `output/figures/` - extracted geometry, tributary-area, and load plots
- `output/intermediate/geometry_plan1.json` - machine-readable digitization

All coordinates use metres and a local Cartesian datum documented in the report. The analysis is deterministic; rerunning it overwrites generated outputs with the same results.
