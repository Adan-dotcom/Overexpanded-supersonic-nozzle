#!/usr/bin/env python3
"""Build the short continuation config from the audited LUT smoke test."""

from pathlib import Path


HERE = Path(__file__).resolve().parent


def main() -> None:
    text = (HERE / "hybrid_lut_smoke.cfg").read_text(encoding="ascii")
    replacements = {
        "READ_BINARY_RESTART= NO": "READ_BINARY_RESTART= YES",
        "CFL_NUMBER= 0.005": "CFL_NUMBER= 0.02",
        "ITER= 5": "ITER= 100",
        "SOLUTION_FILENAME= ../sensor_study/npr20_hybrid_lut_screen/restart_hybrid_lut_seed":
            "SOLUTION_FILENAME= ../sensor_study/npr20_hybrid_lut_screen/restart_smoke",
        "history_smoke": "history_continue",
        "restart_smoke": "restart_continue",
        "flow_smoke": "flow_continue",
        "wall_smoke": "wall_continue",
        "OUTPUT_WRT_FREQ= 5": "OUTPUT_WRT_FREQ= 100",
    }
    for old, new in replacements.items():
        if old not in text:
            raise RuntimeError(f"Expected config text not found: {old}")
        text = text.replace(old, new)
    text = text.replace(
        "SOLUTION_FILENAME= ../sensor_study/npr20_hybrid_lut_screen/restart_continue",
        "SOLUTION_FILENAME= ../sensor_study/npr20_hybrid_lut_screen/restart_smoke",
    )
    output = HERE / "hybrid_lut_continue.cfg"
    output.write_text(text, encoding="ascii")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
