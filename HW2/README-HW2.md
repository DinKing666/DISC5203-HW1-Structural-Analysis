# Homework 2 - Slab-to-Beam Load Transfer and Subframes

This folder contains the complete DISC 5203 Homework 2 submission for **Shuhan He / 何抒翰**, student ID **21345221**, using **Floor Plan 1**.

## Primary deliverables

- `report/21345221-report-HW2.md` - required Markdown report.
- `output/pdf/21345221-report-HW2.pdf` - submission-ready PDF copy.
- `models/beam_A_pure.py`, `models/beam_A_subframe.py`, `models/beam_B_pure.py`, and `models/beam_B_subframe.py` - four OpenSees entry files.
- `output/results/hw2_beam_line_loads.csv` - beam census and complete line-load table.
- `output/results/hw2_beam_profiles.json` - frozen non-uniform dead/live profiles.
- `briefings/` - plain-language model briefings and the human-in-the-loop iteration log.
- `output/figures/` - tributary, load, deformation, N/V/M, bound, and cross-check figures.

The accepted HW1 geometry and axial results are read from the sibling `../HW1/` folder in the same cumulative repository and are not recalculated or overwritten.

## Reproduce

From the cumulative repository root:

```powershell
Set-Location HW2
python -m pip install -r requirements-HW2.txt
python scripts/analyze_hw2_beam_loads.py
python scripts/run_hw2_models.py
python scripts/summarize_hw2_models.py
python scripts/build_hw2_report.py
python scripts/render_hw2_report_pdf.py
python scripts/verify_hw2_outputs.py
```

All calculations use kN and m. Generated files are deterministic and overwrite only files under this folder's `output/` and `report/` directories.
