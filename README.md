# DISC 5203 Homework 1 - AI-Assisted Structural Analysis

This repository contains a reproducible tributary-area and gravity-load analysis for **Floor Plan 1** for Shuhan He, student ID **21345221**. The source assignment and images are preserved unchanged.

## Quick start

```powershell
python -m pip install -r requirements.txt
python scripts/analyze_floor_plan.py
python scripts/build_report.py
python scripts/render_report_pdf.py
python scripts/verify_outputs.py
```

Primary deliverables:

- `report/21345221_HW1_report.md` - required Markdown report
- `output/pdf/HW1_report.pdf` - submission-ready PDF convenience copy
- `output/results/element_loads.csv` - numerical results
- `output/figures/` - extracted geometry, tributary-area, and load plots
- `output/intermediate/geometry_plan1.json` - machine-readable digitization

All coordinates use metres and a local Cartesian datum documented in the report. The analysis is deterministic; rerunning it overwrites generated outputs with the same results.

## Homework 2 extension

The same Git working tree now also contains the HW2 slab-to-beam load-transfer and OpenSees subframe work. HW1 geometry and column/wall axial results are reused unchanged.

```powershell
python scripts/analyze_hw2_beam_loads.py
python scripts/run_hw2_models.py
python scripts/summarize_hw2_models.py
python scripts/build_hw2_report.py
python scripts/render_hw2_report_pdf.py
python scripts/verify_hw2_outputs.py
```

HW2 primary deliverables:

- `report/21345221_HW2_report.md`
- `output/pdf/21345221_HW2_report.pdf`
- `models/beam_A_pure.py`, `models/beam_A_subframe.py`, `models/beam_B_pure.py`, `models/beam_B_subframe.py`
- `output/results/hw2_beam_line_loads.csv` and the frozen non-uniform profiles
- `output/figures/hw2_*.png`
- `briefings/` containing the words-to-model briefings and iteration log

The HW2 changes remain uncommitted until the student reviews and signs off the report.
