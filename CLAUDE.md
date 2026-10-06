# Project guidance

- Treat `HW1.pdf` and everything under `assets/` as immutable source material.
- Work in SI units: m, m2, kN/m2, and kN.
- Store manually interpreted geometry in `config/plan2_geometry.json`; do not hide geometry inside plotting code.
- Generate numerical outputs from scripts rather than editing result tables by hand.
- Require the sum of tributary areas to equal the net floor area within the documented raster tolerance.
- Keep one-floor applied load separate from five-storey cumulative load.
- Run `python scripts/verify_outputs.py` before committing generated results.

## Homework 2 extension

- Reuse `config/plan1_geometry.json`; do not re-derive the HW1 outline or vertical-element tributary areas.
- Read slab load across to the 24 finite beam segments using nearest-edge distance. Equal distance to perpendicular edges is the required 45-degree bisector.
- Keep the exact non-uniform beam profiles in `output/results/hw2_beam_profiles.json`; label any tabulated UDL as equivalent by total load only.
- Use kN, m, kN/m and kN/m2. Enter E in kN/m2 and I in m4 in OpenSees.
- Freeze load profiles before running the four OpenSees cases. Do not tune loads to force agreement with HW1.
- Run `python scripts/verify_hw2_outputs.py` before any HW2 commit or upload.

