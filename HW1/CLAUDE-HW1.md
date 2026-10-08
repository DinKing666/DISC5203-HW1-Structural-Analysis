# Project guidance

- Treat `assignment/assignment-HW1.pdf`, `assignment/assets-HW1.zip`, and everything under `assets/` as immutable source material.
- Work in SI units: m, m2, kN/m2, and kN.
- Store manually interpreted geometry in `config/plan2_geometry.json`; do not hide geometry inside plotting code.
- Generate numerical outputs from scripts rather than editing result tables by hand.
- Require the sum of tributary areas to equal the net floor area within the documented raster tolerance.
- Keep one-floor applied load separate from five-storey cumulative load.
- Run `python scripts/verify_outputs.py` before committing generated results.

