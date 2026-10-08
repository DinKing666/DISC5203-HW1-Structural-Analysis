from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "output" / "results"
OUT = ROOT / "report" / "21345221-report-HW2.md"


def read_csv(name):
    with (RESULTS / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"]*len(headers)) + "|"]
    lines.extend("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |" for row in rows)
    return "\n".join(lines)


def main():
    cfg = json.loads((ROOT / "config" / "hw2_beams.json").read_text(encoding="utf-8"))
    loads = read_csv("hw2_beam_line_loads.csv")
    models = read_csv("hw2_model_summary.csv")
    cross = read_csv("hw2_axial_crosscheck.csv")
    checks = json.loads((RESULTS / "hw2_load_verification.json").read_text(encoding="utf-8"))
    qd = cfg["loads"]["slab_thickness_m"]*cfg["loads"]["concrete_unit_weight_kN_m3"]
    ql = cfg["loads"]["live_load_kN_m2"]
    worked = next(r for r in loads if r["beam_id"] == "H1-2")
    beam_a_prompt = "\n".join((ROOT / "briefings" / "beam_A.md").read_text(encoding="utf-8").splitlines()[2:]).strip()
    beam_b_prompt = "\n".join((ROOT / "briefings" / "beam_B.md").read_text(encoding="utf-8").splitlines()[2:]).strip()
    iteration_body = "\n".join((ROOT / "briefings" / "iteration_log.md").read_text(encoding="utf-8").splitlines()[2:]).strip().replace("## ", "#### ")
    model_lookup = {(r["beam"], r["model"]): r for r in models}
    bound_a = max(float(r["largest_qL2_over_8_bound_kNm"]) for r in models if r["beam"] == "A")
    bound_b = max(float(r["largest_qL2_over_8_bound_kNm"]) for r in models if r["beam"] == "B")

    census_rows = [[
        r["beam_id"], r["start_m"], r["end_m"], r["span_m"], r["depth_m"],
        r["bordering_panels"], r["support_class"]
    ] for r in loads]
    load_rows = [[
        r["beam_id"], r["span_m"], r["tributary_area_m2"], r["mean_tributary_width_m"],
        r["load_shape"], r["dead_eq_kN_m"], r["live_eq_kN_m"], r["total_eq_kN_m"],
        r["total_moment_eq_kN_m"]
    ] for r in loads]
    model_rows = [[
        r["beam"], r["model"], r["applied_load_kN"], r["max_sagging_kNm"],
        r["max_hogging_kNm"], r["max_abs_moment_kNm"], r["max_downward_deflection_mm"],
        r["largest_qL2_over_8_bound_kNm"], r["bound_and_sign_verdict"]
    ] for r in models]
    cross_rows = [[
        r["beam_strip"], r["grid_point"], r["hw1_vertical_element"],
        r["hw1_column_axial_kN_compression_negative"],
        r["hw2_subframe_column_top_N_kN_compression_negative"],
        r["percent_difference_magnitude"], r["sign_check"]
    ] for r in cross]

    text = f"""# Homework 2: From Slab to Beam - Tributary Areas, Line Loads and a Two-Dimensional Subframe

**Course:** Computer (& AI) Methods for Structural Engineering (DISC 5203)<br>
**Student:** Shuhan He / 何抒翰<br>
**Student ID:** 21345221<br>
**Assigned input:** Floor Plan 1 (student-ID final digit = 1)<br>
**Prepared for review:** 7 October 2026<br>
**Repository state:** cumulative course repository extended directly from the accepted HW1 Git state; HW1 remains separately reviewable under `HW1/` and this work is under `HW2/`

## 1. Executive summary

This report extends the accepted HW1 geometry rather than re-deriving it. The same **{checks['net_slab_area_m2']:.3f} m²** net slab is read horizontally onto 24 finite beam segments. Each panel is classified before load allocation: matched supports divide at 45 degrees, while a continuous/fixed edge paired with a discontinuous/simple edge divides at 60 degrees from the continuous edge and 30 degrees from the discontinuous edge. The beam tributary areas close to the HW1 net slab area within numerical precision. Dead and live slab loads are stored separately as non-uniform profiles; the table distinguishes total-load-equivalent and midspan-moment-equivalent UDLs.

Student ID 21345221 selects Floor Plan 1. The marked vertical member is **Beam A**, the left perimeter beam with slab primarily on one side. The marked horizontal member is **Beam B**, the continuous beam on the C1-C2-C3 line with slab on both sides. Four OpenSees analyses were completed: a standalone continuous beam and a one-floor beam-column subframe for each marked beam. All four close vertical equilibrium to less than 1e-8 kN and pass the pre-solve sign and magnitude checks.

The HW2 subframe-versus-HW1 axial comparison gives the same compression sign at every mapped support, but not a close magnitude match. This is reported as a diagnostic result, not hidden: the 2D marked strip contains only the load delivered to that beam line, whereas HW1 assigns the whole floor directly to its nearest column/wall, including orthogonal load paths and wall aggregation. Exact reconciliation would require a full 3D floor-grid model or a common support-aggregation rule.

## 2. Reused input, assumptions and marked beams

![Assigned Floor Plan 1 with marked beams](../assets/FloorPlan1_HW2.png)

The HW1 local datum, slab outline, additions, openings, column locations and wall locations are reused unchanged from `../HW1/config/plan1_geometry.json`. The new beam grid uses x = 0.20, 3.19, 7.60 and 10.70 m and y = 1.00, 7.03, 12.47 and 16.70 m. Segment endpoints are grid intersections; therefore reported spans are centreline distances.

Load and modelling assumptions:

- slab thickness `h = 0.150 m`;
- concrete unit weight `gamma = 25.0 kN/m³`;
- slab dead load `n_D = gamma h = {qd:.2f} kN/m²`;
- live load `n_L = {ql:.2f} kN/m²`;
- no superimposed finish is added because Floor Plan 1 gives none;
- beam self-weight is excluded so that both models compare the same slab-to-beam transfer requested by HW2;
- beam size is not printed on the plan, so both model types use an explicit common assumption of 300 x 600 mm;
- columns are 400 x 400 mm, storey height is 3.0 m, and `E = 30.0 GPa = 30.0e6 kN/m²`;
- service loads are unfactored. Units in OpenSees are kN and m, so second moments of area are in m4.

## 3. Beam tributary-area methodology

The net HW1 slab polygon is discretised into 0.02 m cells and treated panel by panel. Exterior main-slab edges are classified as discontinuous/simple; shared interior grid edges are continuous/fixed. A cell is assigned to the edge with the smallest weighted distance `d/w`, using `w = 1` for a discontinuous edge and `w = sqrt(3)` for a continuous edge. Matched supports have equal weights and retain the 45-degree bisector. At a mixed corner, `d_cont/sqrt(3) = d_disc`, so the boundary leaves the continuous edge at 60 degrees and the discontinuous edge at 30 degrees. This gives the continuous edge the larger tributary share required by the deck.

For an ideal rectangular two-way panel with matched supports, the 45-degree construction gives each short edge a triangular area

`A_short = a²/4`,

and each long edge a trapezoidal area

`A_long = ab/2 - a²/4 = a(2b-a)/4`.

The same weighted rule is applied to the actual net polygon rather than idealised full rectangles, so the stair/core openings remove load before assignment. P10 and P11 are one-edge cantilever balcony slabs; all their load goes to H0/H3 and their free edges are not treated as supports. This explicitly avoids the two assignment traps: beta-vx/beta-vy is not interchanged, and a free edge is not entered into a four-edge table. The area route is the governing calculation; any coefficient-table check must use the short span and the coefficient for the correct edge orientation.

![Beam tributary areas with 45-degree and 60/30-degree boundaries](../output/figures/hw2_01_beam_tributary_areas.png)

Verification:

- beam count: **{checks['beam_count']}**;
- sum of exact beam tributary areas: **{checks['sum_beam_tributary_area_m2_exact']:.6f} m²**;
- reused HW1 net slab area: **{checks['net_slab_area_m2']:.6f} m²**;
- global dead/live loads: **{checks['global_dead_load_kN']:.3f} / {checks['global_live_load_kN']:.3f} kN**.

## 4. Beam census

`Depth = 0.600 assumed` is deliberately labelled wherever the drawing gives no beam depth.

{md_table(['ID','Start (m)','End (m)','Span (m)','Depth (m)','Bordering panel(s)','Class'], census_rows)}

## 5. Line load on every beam

For beam segment `i`, the exact integrated loads are `D_i = n_D A_i` and `L_i = n_L A_i`. The equivalent UDL values in the table are

`w_D,eq = D_i/L_i,beam`, `w_L,eq = L_i/L_i,beam`, and `w_eq = w_D,eq + w_L,eq`.

The load-equivalent values preserve **total load only**. For the required moment equivalent, the simply-supported midspan influence line is `m(s) = s/2` for `s <= L/2` and `m(s) = (L-s)/2` for `s > L/2`. Thus `M_mid = integral w(s)m(s) ds` and `w_M,eq = 8 M_mid/L²`. Neither UDL replaces the local polygonal profile in OpenSees; the frozen profile is applied piecewise so local shear and moment shape are retained.

{md_table(['ID','Span','Area','Mean width','Shape','Dead load-eq','Live load-eq','Total load-eq','Total moment-eq'], load_rows)}

Units: span and mean width in m; area in m²; equivalent line loads in kN/m.

![Equivalent dead and live line loads for all beams](../output/figures/hw2_02_all_beam_line_loads.png)

### 5.1 Worked example - H1-2 (central segment of Beam B)

H1-2 runs from {worked['start_m']} to {worked['end_m']}, so `L = {float(worked['span_m']):.3f} m`. It borders P2 and P5 and is an interior, two-sided segment. The panel-by-panel 45/60/30 allocation, after removing the core opening, is `A_t = {float(worked['tributary_area_m2']):.3f} m²`, giving

`D = 3.75 x {float(worked['tributary_area_m2']):.3f} = {qd*float(worked['tributary_area_m2']):.3f} kN`,

`L_live = 5.00 x {float(worked['tributary_area_m2']):.3f} = {ql*float(worked['tributary_area_m2']):.3f} kN`,

`w_D,eq = D/{float(worked['span_m']):.3f} = {float(worked['dead_eq_kN_m']):.3f} kN/m`,

`w_L,eq = L_live/{float(worked['span_m']):.3f} = {float(worked['live_eq_kN_m']):.3f} kN/m`,

`w_total,eq = {float(worked['total_eq_kN_m']):.3f} kN/m`.

For the moment equivalent, `M_mid = w_M,eq L²/8 = {float(worked['total_moment_eq_kN_m'])*float(worked['span_m'])**2/8:.3f} kN m`, so

`w_M,eq = {float(worked['total_moment_eq_kN_m']):.3f} kN/m`.

The plotted profile is the sum of the P2 and P5 polygonal contributions after the opening is removed. The load-equivalent UDL checks total load; the moment-equivalent UDL sets the hand bound; the exact profile is used by OpenSees.

![Frozen non-uniform profiles for marked beams](../output/figures/hw2_03_marked_beam_load_profiles.png)

## 6. Pre-solve hand bounds and expected shapes

Before OpenSees was run, each span was bounded by `w_M,eq L²/8` for a simple span, with `w_M,eq L²/12` used as a fixed-end/continuous scale. The standalone and subframe beams were expected to show positive sagging at span centres, negative hogging over internal supports, zero or small end moments depending on support idealisation, and inflection points between the positive and negative regions. Beam B's middle span was expected to dominate because it is both the longest horizontal span and receives load from two sides.

![Pre-solve moment bounds and curvature sketches](../output/figures/hw2_04_hand_bounds_and_sketches.png)

The largest simple-span bounds are {bound_a:.3f} kN m for Beam A and {bound_b:.3f} kN m for Beam B. The solver peaks remain below 1.5 times these conservative order-of-magnitude bounds and have the expected signs.

## 7. OpenSees Model A - standalone continuous beams

The plain-language briefings are stored before the generated files in `briefings/beam_A.md` and `briefings/beam_B.md`. Each standalone model uses shared nodes through three spans, one horizontal restraint at the first support, vertical restraints at all supports, free rotations, elasticBeamColumn elements, and the frozen downward local-y piecewise line load. Sixty elements per grid segment reproduce the stored load profile without replacing it by the tabulated UDL.

![Beam A standalone response](../output/figures/hw2_beam_A_pure_response.png)

![Beam B standalone response](../output/figures/hw2_beam_B_pure_response.png)

## 8. OpenSees Model B - one-floor subframes

For each marked beam, the point supports are replaced by 3.0 m high 400 x 400 mm elastic columns with fixed bases. Beam and column elements share the same floor node, allowing finite support rotation and frame action. The same beam geometry, material, section and frozen load profile are retained, so differences from the standalone case are caused by support stiffness and continuity rather than changed loading.

![Beam A subframe response](../output/figures/hw2_beam_A_subframe_response.png)

![Beam B subframe response](../output/figures/hw2_beam_B_subframe_response.png)

The subframe curves remain smooth through the support nodes; there is no displacement kink caused by duplicate or disconnected nodes. The columns sway/rotate with the floor line as one connected frame. Small beam axial forces appear only in the subframe because column bending couples horizontal translation and joint rotation into the beam.

## 9. Numerical model results and comparison

{md_table(['Beam','Model','Load','Max sagging','Max hogging','Max |M|','Max down (mm)','Largest qL2/8','Verdict'], model_rows)}

Units: load in kN; moments in kN m.

For Beam A, finite column stiffness changes the maximum absolute moment from {float(model_lookup[('A','pure')]['max_abs_moment_kNm']):.3f} to {float(model_lookup[('A','subframe')]['max_abs_moment_kNm']):.3f} kN m and the maximum downward deflection from {float(model_lookup[('A','pure')]['max_downward_deflection_mm']):.4f} to {float(model_lookup[('A','subframe')]['max_downward_deflection_mm']):.4f} mm. The subframe introduces beam axial compression and non-zero end moments because the column joints are neither perfect pins nor ideal vertical rollers. For Beam B, the pure/subframe peak absolute moments are {float(model_lookup[('B','pure')]['max_abs_moment_kNm']):.3f} / {float(model_lookup[('B','subframe')]['max_abs_moment_kNm']):.3f} kN m; the subframe develops end moment and axial compression and redistributes the sagging peak. The small deflections follow from the assumed uncracked 300 x 600 mm elastic section; they should not be read as cracked-service deflections.

The **subframe is the more defensible model for beam design actions** because it represents finite column stiffness and joint continuity. The standalone beam is still valuable as an independent bound and debugging model. It answers a deliberately simplified support question rather than the full frame-interaction question.

## 10. Subframe support reactions and HW1 axial cross-check

Compression is reported as negative in both columns. Percentage difference is `(abs(N_HW2)-abs(N_HW1))/abs(N_HW1) x 100%`.

{md_table(['Strip','Grid','HW1 element','HW1 N','HW2 N','Difference %','Sign'], cross_rows)}

![Axial-force percentage-difference plot](../output/figures/hw2_09_axial_crosscheck.png)

All eight comparisons have the correct compression sign and the same order of magnitude, but none is within a few percent; therefore this is **not claimed as a close-match positive result**. The dominant reason is model scope. HW1 directly assigns each entire slab cell to its nearest vertical element, including orthogonal load paths and walls represented as aggregated finite segments. Each HW2 model is only one marked 2D strip and applies load to that beam line; it cannot contain all perpendicular beams delivering load to the same column/wall. Some grid points also map to wall junctions rather than one-to-one columns. No load was tuned to improve the comparison.

For the marked beam's own design actions, the HW2 subframe is trusted because it follows the explicit slab-to-beam-to-column path with frame stiffness. HW1 remains the independent whole-floor gravity estimate. A required exact reconciliation should be performed with a 3D floor grid or a common nodal aggregation model; the present discrepancy is retained as a transparent limitation and a useful diagnostic.

## 11. Speech-to-model prompt and iteration record

The agent was given two short structural briefings in words, not scripts. Each states the marked beam path, spans, supports, frozen loads, section, material and required outputs. The agent then transcribed those briefings into:

- `models/beam_A_pure.py` and `models/beam_A_subframe.py`;
- `models/beam_B_pure.py` and `models/beam_B_subframe.py`;
- shared audited implementation in `models/common.py`.

### 11.1 Beam A plain-language briefing

{beam_a_prompt}

### 11.2 Beam B plain-language briefing

{beam_b_prompt}

### 11.3 Iteration and human-gate record

{iteration_body}

The same wording is preserved in `briefings/beam_A.md`, `briefings/beam_B.md` and `briefings/iteration_log.md`.

## 12. Reproducibility, verification and limitations

Run from the repository root:

```powershell
Set-Location HW2
python scripts/analyze_hw2_beam_loads.py
python scripts/run_hw2_models.py
python scripts/summarize_hw2_models.py
python scripts/build_hw2_report.py
python scripts/render_hw2_report_pdf.py
python scripts/verify_hw2_outputs.py
```

Key deterministic checks are exact beam-area closure, global dead/live load conservation, four OpenSees reaction/load closures, expected sagging/hogging signs, pre-solve bound compliance and existence of every deliverable. The method generalises because a different floor plan changes the slab polygon, beam segments and openings in configuration rather than the load-transfer algorithm.

Limitations are explicit: the source plan is raster; unprinted beam dimensions are assumptions; linear uncracked elastic sections do not represent cracked stiffness; and the 2D subframes omit orthogonal frame members. The pre-solve hand-check sketches are independently generated schematics placed beside every solver output. The numerical work and report are complete in the `HW2/` package, while the accepted `HW1/` package remains unchanged and separately reviewable in the same cumulative repository.

## 13. Deliverable index

- report: `report/21345221-report-HW2.md` and `output/pdf/21345221-report-HW2.pdf`;
- beam census and line-load table: `output/results/hw2_beam_line_loads.csv`;
- frozen profiles: `output/results/hw2_beam_profiles.json`;
- four OpenSees inputs: `models/beam_A_pure.py`, `models/beam_A_subframe.py`, `models/beam_B_pure.py`, `models/beam_B_subframe.py`;
- reactions, model summaries and cross-check tables: `output/results/hw2_support_reactions.csv`, `hw2_model_summary.csv`, `hw2_axial_crosscheck.csv`;
- response diagrams and verification figures: `output/figures/hw2_*.png`;
- prompt record: `briefings/`;
- configuration and reusable procedures: `config/hw2_beams.json`, `CLAUDE-HW2.md`, `skills-HW2.md`.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
