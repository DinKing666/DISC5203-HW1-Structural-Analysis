from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models"))

from common import solve_case


def main():
    for mark in ("A", "B"):
        for model_type in ("pure", "subframe"):
            result = solve_case(mark, model_type)
            print(
                f"Beam {mark} {model_type}: load={result['applied_vertical_load_kN']:.3f} kN, "
                f"reaction={result['sum_vertical_reaction_kN']:.3f} kN, "
                f"max|M|={result['max_abs_moment_kNm']:.3f} kN m"
            )


if __name__ == "__main__":
    main()
