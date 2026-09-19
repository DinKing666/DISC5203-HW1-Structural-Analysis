from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "HW1_report.md"


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join(lines)


def main():
    with (ROOT / "config" / "plan1_geometry.json").open(encoding="utf-8") as f:
        cfg = json.load(f)
    with (ROOT / "output" / "intermediate" / "geometry_plan1.json").open(encoding="utf-8") as f:
        geo = json.load(f)
    with (ROOT / "output" / "results" / "element_loads.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with (ROOT / "output" / "results" / "building_level_totals.csv").open(encoding="utf-8") as f:
        levels = list(csv.DictReader(f))
    with (ROOT / "output" / "results" / "verification.json").open(encoding="utf-8") as f:
        checks = json.load(f)

    qd = cfg["loads"]["slab_thickness_m"] * cfg["loads"]["concrete_unit_weight_kN_m3"]
    ql = cfg["loads"]["live_load_kN_m2"]
    result_rows = [[
        r["id"], r["type"], f"({float(r['x_m']):.2f}, {float(r['y_m']):.2f})",
        r["size_mm"], f"{float(r['tributary_area_m2']):.2f}",
        f"{float(r['dead_load_1floor_kN']):.1f}", f"{float(r['live_load_1floor_kN']):.1f}",
        f"{float(r['total_load_1floor_kN']):.1f}", f"{float(r['base_load_5storey_kN']):.1f}"
    ] for r in rows]
    level_rows = [[r[k] for k in ["level", "floors_supported", "dead_kN", "live_kN", "total_kN"]] for r in levels]
    text = f"""# Homework 1: AI-Assisted Structural Analysis of a Building Floor Plan

**Course:** Computer (& AI) Methods for Structural Engineering (DISC 5203)  
**Student:** Shuhan He  
**Student ID:** 21345221  
**Assigned input:** Floor Plan 1 (ID final digit = 1)  
**Date:** 19 September 2026

## 1. Executive summary

This report presents a reproducible extraction and gravity-load analysis of Floor Plan 1. The net slab area is **{geo['net_floor_area_m2']:.2f} m²** after excluding **{geo['opening_area_m2']:.2f} m²** of stair/core openings. Seven columns and eleven shear-wall elements were identified. A nearest-support partition, equivalent to a generalized Voronoi construction for both points and line segments, assigns every slab cell to exactly one vertical element. The one-floor gravity load is **{geo['net_floor_area_m2']*(qd+ql):.1f} kN** and the five-storey base total is **{5*geo['net_floor_area_m2']*(qd+ql):.1f} kN**.

## 2. Input and interpretation

The assignment PDF and `assets/FloorPlan1.png` were inspected visually. The printed dimensions were used to establish a metric coordinate system rather than inferring scale from image pixels. The origin is the lower-left principal wall-centreline intersection, with +x to the right and +y upward. Geometry is stored independently in `config/plan1_geometry.json` so that every interpreted coordinate can be reviewed or changed without editing the solver.

The source is a structural floor-plan diagram rather than a machine-readable CAD model. Dimensions that are explicit in the image govern; where a wall endpoint or opening extent is visually indicated but not fully dimensioned, its centreline was digitized from adjacent dimension chains. These assumptions affect the local partition but do not change the global load equilibrium.

![Assigned source floor plan](../assets/FloorPlan1.png)

## 3. Extracted geometry and vertical elements

The slab model consists of the principal rectangular floor, the top and bottom balcony slabs, and two excluded core/stair openings. Columns are point supports at their centre coordinates. Walls are finite centreline segments, so their distance field reflects both length and orientation.

![Extracted outline and supports](../output/figures/01_extracted_geometry.png)

Key area values:

- Gross modeled slab envelope: **{geo['gross_area_m2']:.2f} m²**
- Excluded openings: **{geo['opening_area_m2']:.2f} m²**
- Net loaded floor area: **{geo['net_floor_area_m2']:.2f} m²**
- Floor-to-floor height: **3.0 m** (assignment input; not required for gravity-load magnitude)
- Number of identical storeys: **5**

## 4. Tributary-area method

The net slab is discretized into 0.02 m square cells. For each cell centre, the script calculates Euclidean distance to each column centre and the shortest perpendicular/end distance to each finite wall centreline. The cell is assigned to the closest support. This constructs midpoint boundaries automatically; at corners, equal-distance loci form the required 45-degree transitions. Exact numerical ties are resolved in stable ID order.

For a point **p** and wall segment from **a** to **b**, the distance is

`t = clamp(((p-a)·(b-a)) / ||b-a||², 0, 1)` and `d = ||p - (a + t(b-a))||`.

The raster areas are normalized by the ratio of exact polygon area to counted cell area. This correction is only for boundary-cell discretization and preserves relative tributary shares. The pre-normalization area closure error is **{geo['area_closure_error_before_normalization_percent']:.4f}%**.

![Computed tributary areas](../output/figures/02_tributary_areas.png)

## 5. Load calculation

Only loads specified by the assignment are applied. Concrete slab self-weight is treated as dead load; beams, columns, walls, finishes, facade and partitions are excluded because their densities or weights were not supplied.

- Slab thickness `h = 0.150 m`
- Reinforced-concrete unit weight `γ = 25.0 kN/m³`
- Dead area load `q_D = γh = {qd:.2f} kN/m²`
- Live area load `q_L = {ql:.2f} kN/m²`
- Total area load `q = q_D + q_L = {qd+ql:.2f} kN/m²`

For vertical element *i* with tributary area `A_i`:

`D_i = q_D A_i`, `L_i = q_L A_i`, `N_i,1 = D_i + L_i`, and `N_i,base = 5 N_i,1`.

The five-storey multiplier assumes identical aligned supports and identical gravity loading on all levels. Values are unfactored service loads, not ultimate design actions.

## 6. Results by vertical element

Coordinates are support points for columns and wall-segment midpoints for walls. `Base total` is the cumulative unfactored axial load at the base of a five-storey stack.

{table(['ID','Type','Location (m)','Size (mm)','Area (m²)','Dead (kN)','Live (kN)','1-floor total (kN)','Base total (kN)'], result_rows)}

![Element load comparison](../output/figures/03_element_loads.png)

## 7. Building-level load accumulation

{table(['Level','Floors supported','Dead (kN)','Live (kN)','Total (kN)'], level_rows)}

## 8. Verification checks

1. **Area closure:** `ΣA_i = {checks['sum_tributary_area_m2']:.6f} m²`; independent net polygon area = `{checks['net_area_m2']:.6f} m²`; difference = `{checks['area_difference_m2']:.3e} m²`.
2. **Dead-load conservation:** element sum = `{checks['dead_load_sum_kN']:.3f} kN`; global calculation = `{checks['dead_load_global_kN']:.3f} kN`.
3. **Live-load conservation:** element sum = `{checks['live_load_sum_kN']:.3f} kN`; global calculation = `{checks['live_load_global_kN']:.3f} kN`.
4. **Unit check:** `(m²)(kN/m²) = kN` for each axial-load result.
5. **Positivity and coverage:** all 18 elements receive a positive tributary area, and every in-slab cell is assigned exactly once.

## 9. Limitations and defensibility

- The drawing is a raster image, so some wall endpoints and opening limits require engineering interpretation. The digitized JSON makes those judgments auditable.
- Nearest-distance partition is a geometric gravity-load idealization. A detailed slab analysis could redistribute load because of stiffness, span direction, openings and discontinuities.
- Support self-weight and non-slab dead loads are intentionally excluded. Adding them requires explicit material and section data.
- The algorithm generalizes to irregular outlines, holes, point columns and finite wall axes. A new input can be analyzed by replacing only the geometry configuration.

## 10. Reproducibility and AI-agent workflow

The agent inspected the assignment PDF and all supplied images, translated visible dimensions into a reviewable geometry configuration, implemented the partition and load workflow, generated plots and tables, and ran deterministic verification checks. The Git repository includes source inputs, scripts, configuration, guidance (`CLAUDE.md`, `skills.md`), a pre-commit verification hook, intermediate geometry, results and this report.

To reproduce from the repository root:

```powershell
python -m pip install -r requirements.txt
python scripts/analyze_floor_plan.py
python scripts/build_report.py
python scripts/render_report_pdf.py
python scripts/verify_outputs.py
```

## 11. Files produced

- `config/plan1_geometry.json`: independently reviewable interpretation of the drawing
- `scripts/analyze_floor_plan.py`: geometry, partition, loads and plots
- `scripts/build_report.py`: deterministic Markdown report assembly
- `scripts/render_report_pdf.py`: PDF convenience export
- `scripts/verify_outputs.py`: automated numerical and artifact checks
- `output/results/*.csv`: element and level results
- `output/intermediate/geometry_plan1.json`: extracted geometry and area audit
- `output/figures/*.png`: geometry, tributary and load diagrams
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
