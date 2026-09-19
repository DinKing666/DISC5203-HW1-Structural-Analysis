from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path):
    if not path.exists() or path.stat().st_size == 0:
        raise AssertionError(f"Missing or empty artifact: {path}")


def main():
    paths = [
        ROOT / "report" / "HW1_report.md",
        ROOT / "output" / "pdf" / "HW1_report.pdf",
        ROOT / "output" / "results" / "element_loads.csv",
        ROOT / "output" / "results" / "building_level_totals.csv",
        ROOT / "output" / "results" / "verification.json",
        ROOT / "output" / "intermediate" / "geometry_plan1.json",
        ROOT / "output" / "figures" / "01_extracted_geometry.png",
        ROOT / "output" / "figures" / "02_tributary_areas.png",
        ROOT / "output" / "figures" / "03_element_loads.png",
    ]
    for path in paths:
        require(path)

    with paths[2].open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 18, f"Expected 18 elements, found {len(rows)}"
    assert {r["id"] for r in rows} == {*(f"C{i}" for i in range(1, 8)), *(f"T{i}" for i in range(1, 12))}
    assert all(float(r["tributary_area_m2"]) > 0 for r in rows)

    with paths[4].open(encoding="utf-8") as f:
        checks = json.load(f)
    assert abs(checks["area_difference_m2"]) < 1e-8
    assert abs(checks["dead_load_sum_kN"] - checks["dead_load_global_kN"]) < 1e-8
    assert abs(checks["live_load_sum_kN"] - checks["live_load_global_kN"]) < 1e-8
    print("Verification passed: 18 elements, exact area closure, exact global load conservation, all artifacts present.")


if __name__ == "__main__":
    main()

