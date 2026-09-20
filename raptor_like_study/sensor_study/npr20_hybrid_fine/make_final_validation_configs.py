from pathlib import Path


here = Path(__file__).resolve().parent
template = (here / "npr20_fine_bdf1_dt000625us.cfg").read_text(encoding="ascii")

bdf1 = template
for old, new in {
    "RESTART_ITER= 101": "RESTART_ITER= 5614",
    "TIME_ITER= 103": "TIME_ITER= 5616",
    "INNER_ITER= 100": "INNER_ITER= 50",
    "VENKAT_LIMITER_COEFF= 0.005": "VENKAT_LIMITER_COEFF= 0.001",
    "CONV_NUM_METHOD_FLOW= HLLC": "CONV_NUM_METHOD_FLOW= SLAU2",
    "SOLUTION_FILENAME= ../npr20_hybrid_pilot/restart_npr20_bdf2_stable_to100": (
        "SOLUTION_FILENAME= ../npr20_hybrid_pilot/restart_npr20_production_cfl2_i30_from520"
    ),
    "CONV_FILENAME= history_npr20_fine_bdf1": "CONV_FILENAME= history_npr20_final_transfer_bdf1",
    "RESTART_FILENAME= restart_npr20_fine_bdf1": "RESTART_FILENAME= restart_npr20_final_transfer_bdf1",
    "VOLUME_FILENAME= flow_npr20_fine_bdf1": "VOLUME_FILENAME= flow_npr20_final_transfer_bdf1",
    "SURFACE_FILENAME= wall_npr20_fine_bdf1": "SURFACE_FILENAME= wall_npr20_final_transfer_bdf1",
    "OUTPUT_WRT_FREQ= 1, 1000, 1000, 1000": "OUTPUT_WRT_FREQ= 1, 2, 2, 2",
}.items():
    if old not in bdf1:
        raise ValueError(f"Missing template text: {old}")
    bdf1 = bdf1.replace(old, new)
(here / "npr20_final_transfer_bdf1.cfg").write_text(bdf1, encoding="ascii")

bdf2 = bdf1
for old, new in {
    "RESTART_ITER= 5614": "RESTART_ITER= 5616",
    "TIME_MARCHING= DUAL_TIME_STEPPING-1ST_ORDER": "TIME_MARCHING= DUAL_TIME_STEPPING-2ND_ORDER",
    "TIME_ITER= 5616": "TIME_ITER= 5666",
    "INNER_ITER= 50": "INNER_ITER= 30",
    "CFL_NUMBER= 0.5": "CFL_NUMBER= 2.0",
    "SOLUTION_FILENAME= ../npr20_hybrid_pilot/restart_npr20_production_cfl2_i30_from520": (
        "SOLUTION_FILENAME= restart_npr20_final_transfer_bdf1"
    ),
    "CONV_FILENAME= history_npr20_final_transfer_bdf1": "CONV_FILENAME= history_npr20_final_validation_bdf2",
    "RESTART_FILENAME= restart_npr20_final_transfer_bdf1": "RESTART_FILENAME= restart_npr20_final_validation_bdf2",
    "VOLUME_FILENAME= flow_npr20_final_transfer_bdf1": "VOLUME_FILENAME= flow_npr20_final_validation_bdf2",
    "SURFACE_FILENAME= wall_npr20_final_transfer_bdf1": "SURFACE_FILENAME= wall_npr20_final_validation_bdf2",
    "OUTPUT_WRT_FREQ= 1, 2, 2, 2": "OUTPUT_WRT_FREQ= 10, 10, 10, 10",
}.items():
    if old not in bdf2:
        raise ValueError(f"Missing BDF1 text: {old}")
    bdf2 = bdf2.replace(old, new)
(here / "npr20_final_validation_bdf2.cfg").write_text(bdf2, encoding="ascii")
