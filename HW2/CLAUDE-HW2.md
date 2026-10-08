# HW2 project guidance

- Treat `assignment/`, `assets/`, and everything under `../HW1/` as immutable source/reference material.
- Reuse `../HW1/config/plan1_geometry.json`; do not re-derive the HW1 outline, openings, columns, walls, or vertical-element tributary areas.
- Read slab load panel by panel. Matched edge conditions use 45-degree bisectors; a continuous/fixed edge paired with a discontinuous/simple edge uses 60 degrees from the continuous edge and 30 degrees from the discontinuous edge. A free edge is never treated as a support.
- Store the exact dead/live line-load profiles in `output/results/hw2_beam_profiles.json`. Report both the load-equivalent UDL and the simply-supported midspan-moment-equivalent UDL; retain the exact profile in OpenSees.
- Use kN, m, kN/m and kN/m2. Enter E in kN/m2 and I in m4 in OpenSees.
- Freeze load profiles before running the four models. Do not tune loads to force agreement with HW1.
- Run `python scripts/verify_hw2_outputs.py` before committing or uploading.
