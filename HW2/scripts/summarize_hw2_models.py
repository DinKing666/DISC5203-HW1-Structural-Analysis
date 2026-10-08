from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
HW1_ROOT = ROOT.parent / "HW1"
RESULTS = ROOT / "output" / "results"
MODELS = RESULTS / "models"
FIG_DIR = ROOT / "output" / "figures"


def read_csv(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    cfg = json.loads((ROOT / "config" / "hw2_beams.json").read_text(encoding="utf-8"))
    prof = json.loads((RESULTS / "hw2_beam_profiles.json").read_text(encoding="utf-8"))["profiles"]
    summaries = []
    reactions = []
    model_data = {}
    for mark in ("A", "B"):
        ids = cfg["marked_beams"][mark]["segments"]
        simple_bounds = []
        fixed_scales = []
        for bid in ids:
            p = prof[bid]
            q = float(p["total_moment_eq_kN_m"])
            length = p["length_m"]
            simple_bounds.append(q*length**2/8)
            fixed_scales.append(q*length**2/12)
        for kind in ("pure", "subframe"):
            data = json.loads((MODELS / f"beam_{mark}_{kind}.json").read_text(encoding="utf-8"))
            model_data[(mark, kind)] = data
            moments = np.asarray(data["beam_response"]["M_kNm"])
            summaries.append({
                "beam": mark, "model": kind,
                "applied_load_kN": f"{data['applied_vertical_load_kN']:.3f}",
                "reaction_sum_kN": f"{data['sum_vertical_reaction_kN']:.3f}",
                "equilibrium_error_kN": f"{data['equilibrium_error_kN']:.3e}",
                "max_sagging_kNm": f"{moments.max():.3f}",
                "max_hogging_kNm": f"{moments.min():.3f}",
                "max_abs_moment_kNm": f"{np.abs(moments).max():.3f}",
                "max_downward_deflection_mm": f"{data['max_downward_deflection_mm']:.4f}",
                "largest_qL2_over_8_bound_kNm": f"{max(simple_bounds):.3f}",
                "largest_qL2_over_12_scale_kNm": f"{max(fixed_scales):.3f}",
                "bound_and_sign_verdict": "PASS" if moments.max() > 0 and moments.min() < 0 and np.abs(moments).max() < 1.5*max(simple_bounds) else "REVIEW",
            })
            for r in data["reactions"]:
                reactions.append({"beam": mark, "model": kind, **{k: r[k] for k in r}})
    write_csv(RESULTS / "hw2_model_summary.csv", summaries)
    write_csv(RESULTS / "hw2_support_reactions.csv", reactions)

    hw1 = {r["id"]: r for r in read_csv(HW1_ROOT / "output" / "results" / "element_loads.csv")}
    mapping = {
        "A": [("G00", "T1"), ("G01", "C1"), ("G02", "C4"), ("G03", "T10")],
        "B": [("G01", "C1"), ("G11", "T5"), ("G21", "C2"), ("G31", "C3")],
    }
    cross = []
    for mark in ("A", "B"):
        data = model_data[(mark, "subframe")]
        for idx, (grid, member) in enumerate(mapping[mark]):
            n_hw1 = -float(hw1[member]["total_load_1floor_kN"])
            n_hw2 = float(data["column_forces"][idx]["top_axial_kN"])
            pct = 100*(abs(n_hw2)-abs(n_hw1))/abs(n_hw1)
            cross.append({
                "beam_strip": mark, "grid_point": grid, "hw1_vertical_element": member,
                "hw1_column_axial_kN_compression_negative": f"{n_hw1:.3f}",
                "hw2_subframe_column_top_N_kN_compression_negative": f"{n_hw2:.3f}",
                "percent_difference_magnitude": f"{pct:.1f}",
                "sign_check": "PASS" if n_hw1 < 0 and n_hw2 < 0 else "FAIL",
                "interpretation": "2D strip reaction versus HW1 whole-floor nearest-support estimate; gap measures omitted/redistributed orthogonal paths"
            })
    write_csv(RESULTS / "hw2_axial_crosscheck.csv", cross)

    labels = [f"{r['beam_strip']}-{r['grid_point']}\n{r['hw1_vertical_element']}" for r in cross]
    vals = [float(r["percent_difference_magnitude"]) for r in cross]
    colors = ["#588157" if abs(v) <= 10 else "#bc4749" for v in vals]
    fig, ax = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    bars = ax.bar(np.arange(len(vals)), vals, color=colors)
    ax.axhline(0, color="#333", lw=.8)
    ax.axhspan(-10, 10, color="#a3b18a", alpha=.18, label="within +/-10%")
    ax.set_xticks(np.arange(len(vals)), labels)
    ax.set_ylabel("Difference in axial-force magnitude (%)")
    ax.set_title("HW2 2D Strip Reactions vs HW1 Whole-Floor Tributary Axials", weight="bold")
    ax.grid(axis="y", alpha=.18)
    ax.legend(frameon=False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+(3 if v >= 0 else -3), f"{v:.1f}%",
                ha="center", va="bottom" if v >= 0 else "top", fontsize=8)
    fig.savefig(FIG_DIR / "hw2_09_axial_crosscheck.png", dpi=220)
    plt.close(fig)
    print(f"Wrote {len(summaries)} model summaries and {len(cross)} axial cross-check rows")


if __name__ == "__main__":
    main()
