from __future__ import annotations

import csv
import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def require(path):
    if not path.exists() or path.stat().st_size == 0:
        raise AssertionError(f"Missing or empty artifact: {path}")


def main():
    required = [
        ROOT/"report"/"21345221_HW2_report.md", ROOT/"output"/"pdf"/"21345221_HW2_report.pdf",
        ROOT/"output"/"results"/"hw2_beam_line_loads.csv", ROOT/"output"/"results"/"hw2_beam_profiles.json",
        ROOT/"output"/"results"/"hw2_model_summary.csv", ROOT/"output"/"results"/"hw2_support_reactions.csv",
        ROOT/"output"/"results"/"hw2_axial_crosscheck.csv", ROOT/"briefings"/"beam_A.md",
        ROOT/"briefings"/"beam_B.md", ROOT/"briefings"/"iteration_log.md",
        ROOT/"models"/"beam_A_pure.py", ROOT/"models"/"beam_A_subframe.py",
        ROOT/"models"/"beam_B_pure.py", ROOT/"models"/"beam_B_subframe.py",
    ]
    required += list((ROOT/"output"/"figures").glob("hw2_*.png"))
    for p in required:
        require(p)
    with (ROOT/"output"/"results"/"hw2_beam_line_loads.csv").open(encoding="utf-8") as f:
        beams = list(csv.DictReader(f))
    assert len(beams) == 24
    checks = json.loads((ROOT/"output"/"results"/"hw2_load_verification.json").read_text(encoding="utf-8"))
    assert abs(checks["sum_beam_tributary_area_m2_exact"]-checks["net_slab_area_m2"]) < 1e-8
    with (ROOT/"output"/"results"/"hw2_model_summary.csv").open(encoding="utf-8") as f:
        models = list(csv.DictReader(f))
    assert len(models) == 4 and all(r["bound_and_sign_verdict"] == "PASS" for r in models)
    assert all(abs(float(r["equilibrium_error_kN"])) < 1e-8 for r in models)
    pdf = PdfReader(str(ROOT/"output"/"pdf"/"21345221_HW2_report.pdf"))
    assert len(pdf.pages) >= 10
    print(f"HW2 verification passed: 24 beams, exact area closure, 4 model checks, {len(pdf.pages)}-page PDF, all artifacts present.")


if __name__ == "__main__":
    main()
