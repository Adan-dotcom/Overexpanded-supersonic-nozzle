#!/usr/bin/env python3
"""Create the corrected one-atmosphere LUT plume screening configs."""

from pathlib import Path


HERE = Path(__file__).resolve().parent
CASE = "sea_level_hybrid_lut_screen"


def main() -> None:
    smoke = (HERE / "hybrid_lut_smoke.cfg").read_text(encoding="ascii")
    smoke = smoke.replace("260000.0", "101325.0")
    smoke = smoke.replace("npr20_hybrid_lut_screen", CASE)
    (HERE / "sea_level_lut_smoke.cfg").write_text(smoke, encoding="ascii")

    continuation = smoke.replace("READ_BINARY_RESTART= NO", "READ_BINARY_RESTART= YES")
    continuation = continuation.replace("CFL_NUMBER= 0.005", "CFL_NUMBER= 0.02")
    continuation = continuation.replace("ITER= 5", "ITER= 100")
    continuation = continuation.replace("restart_hybrid_lut_seed", "restart_smoke")
    continuation = continuation.replace("history_smoke", "history_continue")
    continuation = continuation.replace("RESTART_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_smoke", "RESTART_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_continue")
    continuation = continuation.replace("flow_smoke", "flow_continue")
    continuation = continuation.replace("wall_smoke", "wall_continue")
    continuation = continuation.replace("OUTPUT_WRT_FREQ= 5", "OUTPUT_WRT_FREQ= 100")
    (HERE / "sea_level_lut_continue.cfg").write_text(continuation, encoding="ascii")

    relax = continuation.replace(
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_smoke",
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_continue",
    )
    relax = relax.replace("CFL_NUMBER= 0.02", "CFL_NUMBER= 0.05")
    relax = relax.replace("CFL_ADAPT= NO", "CFL_ADAPT= YES\nCFL_ADAPT_PARAM= ( 0.5, 1.05, 0.01, 1.0 )")
    relax = relax.replace("ITER= 100", "ITER= 400")
    relax = relax.replace("history_continue", "history_relax")
    relax = relax.replace("restart_continue", "restart_relax")
    relax = relax.replace("flow_continue", "flow_relax")
    relax = relax.replace("wall_continue", "wall_relax")
    relax = relax.replace("OUTPUT_WRT_FREQ= 100", "OUTPUT_WRT_FREQ= 400")
    relax = relax.replace(
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_relax",
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_continue",
    )
    (HERE / "sea_level_lut_relax.cfg").write_text(relax, encoding="ascii")

    safe = continuation.replace(
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_smoke",
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_continue",
    )
    safe = safe.replace("ITER= 100", "ITER= 400")
    safe = safe.replace("history_continue", "history_safe")
    safe = safe.replace("restart_continue", "restart_safe")
    safe = safe.replace("flow_continue", "flow_safe")
    safe = safe.replace("wall_continue", "wall_safe")
    safe = safe.replace("OUTPUT_WRT_FREQ= 100", "OUTPUT_WRT_FREQ= 400")
    safe = safe.replace(
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_safe",
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_continue",
    )
    (HERE / "sea_level_lut_relax_safe.cfg").write_text(safe, encoding="ascii")

    urans = safe.replace(
        "READ_BINARY_RESTART= YES\nAXISYMMETRIC= YES",
        "READ_BINARY_RESTART= YES\nTIME_DOMAIN= YES\nTIME_MARCHING= DUAL_TIME_STEPPING-1ST_ORDER\nTIME_STEP= 2.5E-8\nTIME_ITER= 10\nINNER_ITER= 30\nAXISYMMETRIC= YES",
    )
    urans = urans.replace("ITER= 400\n", "")
    urans = urans.replace("SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_continue", "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_safe")
    urans = urans.replace("history_safe", "history_urans_smoke")
    urans = urans.replace("restart_safe", "restart_urans_smoke")
    urans = urans.replace("flow_safe", "flow_urans_smoke")
    urans = urans.replace("wall_safe", "wall_urans_smoke")
    urans = urans.replace("OUTPUT_WRT_FREQ= 400", "OUTPUT_WRT_FREQ= 10")
    urans = urans.replace(
        "SCREEN_OUTPUT= ( INNER_ITER, RMS_DENSITY, RMS_ENERGY )",
        "SCREEN_OUTPUT= ( TIME_ITER, INNER_ITER, RMS_DENSITY, RMS_ENERGY )",
    )
    urans = urans.replace(
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_urans_smoke",
        "SOLUTION_FILENAME= ../sensor_study/sea_level_hybrid_lut_screen/restart_safe",
    )
    (HERE / "sea_level_lut_urans_smoke.cfg").write_text(urans, encoding="ascii")
    print("Wrote sea-level steady and URANS screening configs")


if __name__ == "__main__":
    main()
