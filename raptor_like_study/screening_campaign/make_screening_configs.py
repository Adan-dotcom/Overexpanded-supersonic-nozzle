from pathlib import Path


HERE = Path(__file__).resolve().parent

CASES = {
    "ideal_sst_hllc": {"fluid": "ideal", "turbulence": "SST", "flux": "HLLC"},
    "ideal_sst_slau2": {"fluid": "ideal", "turbulence": "SST", "flux": "SLAU2"},
    "ideal_sa_hllc": {"fluid": "ideal", "turbulence": "SA", "flux": "HLLC"},
    "lut_sst_hllc": {"fluid": "lut", "turbulence": "SST", "flux": "HLLC"},
    "lut_sa_hllc": {"fluid": "lut", "turbulence": "SA", "flux": "HLLC"},
}

CONTINUATION_CASES = ("ideal_sst_hllc", "ideal_sa_hllc", "lut_sst_hllc")


def fluid_block(kind):
    if kind == "lut":
        return """FLUID_MODEL= DATADRIVEN_FLUID
INTERPOLATION_METHOD= LUT
FILENAMES_INTERPOLATOR= ( ../thermochemistry/LUT_lox_ch4_equilibrium.drg )
USE_PINN= NO"""
    return """FLUID_MODEL= IDEAL_GAS
GAMMA_VALUE= 1.1982940938
GAS_CONSTANT= 390.5997546790"""


def turbulence_block(kind):
    if kind == "SST":
        return """KIND_TURB_MODEL= SST
SST_OPTIONS= V2003m, COMPRESSIBILITY-SARKAR"""
    return "KIND_TURB_MODEL= SA"


def config(name, case):
    seed = f"seed_{case['fluid']}_{case['turbulence'].lower()}"
    return f"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Rapid screening only. This configuration cannot generate accepted labels.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
SOLVER= RANS
{turbulence_block(case['turbulence'])}
MATH_PROBLEM= DIRECT
RESTART_SOL= YES
READ_BINARY_RESTART= NO
AXISYMMETRIC= YES

MACH_NUMBER= 0.001
AOA= 0.0
INIT_OPTION= TD_CONDITIONS
FREESTREAM_OPTION= TEMPERATURE_FS
FREESTREAM_PRESSURE= 260000.0
FREESTREAM_TEMPERATURE= 300.0
FREESTREAM_TURBULENCEINTENSITY= 0.01
FREESTREAM_TURB2LAMVISCRATIO= 10.0
REF_DIMENSIONALIZATION= DIMENSIONAL

{fluid_block(case['fluid'])}

VISCOSITY_MODEL= SUTHERLAND
MU_REF= 1.0707E-4
MU_T_REF= 3312.09
SUTHERLAND_CONSTANT= 683.0362
CONDUCTIVITY_MODEL= CONSTANT_PRANDTL
PRANDTL_LAM= 0.6738
TURBULENT_CONDUCTIVITY_MODEL= CONSTANT_PRANDTL_TURB
PRANDTL_TURB= 0.90

MARKER_HEATFLUX= ( WALL, 0.0 )
MARKER_SYM= ( AXIS )
MARKER_RIEMANN= ( INLET, TOTAL_CONDITIONS_PT, 5200000.0, 3485.33, 1.0, 0.0, 0.0, \\
                  OUTLET, STATIC_PRESSURE, 260000.0, 0.0, 0.0, 0.0, 0.0 )
MARKER_MONITORING= ( WALL )
MARKER_PLOTTING= ( WALL )

NUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES
CFL_NUMBER= 0.01
CFL_ADAPT= NO
MAX_DELTA_TIME= 1E6
MUSCL_FLOW= NO
SLOPE_LIMITER_FLOW= VENKATAKRISHNAN_WANG
SLOPE_LIMITER_TURB= NONE
VENKAT_LIMITER_COEFF= 0.001
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_PREC= ILU
LINEAR_SOLVER_ILU_FILL_IN= 0
LINEAR_SOLVER_ERROR= 1E-4
LINEAR_SOLVER_ITER= 10
CONV_NUM_METHOD_FLOW= {case['flux']}
TIME_DISCRE_FLOW= EULER_IMPLICIT
CONV_NUM_METHOD_TURB= SCALAR_UPWIND
TIME_DISCRE_TURB= EULER_IMPLICIT
CFL_REDUCTION_TURB= 0.5

ITER= 100
CONV_RESIDUAL_MINVAL= -20
CONV_STARTITER= 200

MESH_FILENAME= ../internal_mesh/screen/dlr_par_internal.su2
MESH_FORMAT= SU2
SOLUTION_FILENAME= {seed}
CONV_FILENAME= {name}/history
RESTART_FILENAME= {name}/restart
VOLUME_FILENAME= {name}/flow
SURFACE_FILENAME= {name}/wall
OUTPUT_FILES= ( RESTART, PARAVIEW_ASCII, SURFACE_CSV )
VOLUME_OUTPUT= ( COORDINATES, SOLUTION, PRIMITIVE )
OUTPUT_WRT_FREQ= 100
HISTORY_WRT_FREQ_INNER= 1
SCREEN_WRT_FREQ_INNER= 10
SCREEN_OUTPUT= ( INNER_ITER, RMS_DENSITY, RMS_ENERGY )
"""


def main():
    for name, case in CASES.items():
        (HERE / name).mkdir(parents=True, exist_ok=True)
        startup = config(name, case)
        (HERE / f"{name}.cfg").write_text(startup, encoding="ascii")
        settle = startup.replace("READ_BINARY_RESTART= NO", "READ_BINARY_RESTART= YES")
        settle = settle.replace(
            f"SOLUTION_FILENAME= seed_{case['fluid']}_{case['turbulence'].lower()}",
            f"SOLUTION_FILENAME= {name}/restart",
        )
        settle = settle.replace("CFL_NUMBER= 0.01", "CFL_NUMBER= 0.05")
        settle = settle.replace("ITER= 100", "ITER= 300")
        settle = settle.replace(f"CONV_FILENAME= {name}/history", f"CONV_FILENAME= {name}/history_settle")
        settle = settle.replace(f"RESTART_FILENAME= {name}/restart", f"RESTART_FILENAME= {name}/restart_settle")
        settle = settle.replace(f"VOLUME_FILENAME= {name}/flow", f"VOLUME_FILENAME= {name}/flow_settle")
        settle = settle.replace(f"SURFACE_FILENAME= {name}/wall", f"SURFACE_FILENAME= {name}/wall_settle")
        settle = settle.replace("OUTPUT_WRT_FREQ= 100", "OUTPUT_WRT_FREQ= 300")
        (HERE / f"{name}_settle.cfg").write_text(settle, encoding="ascii")

        if name in CONTINUATION_CASES:
            continuation = settle.replace(
                f"SOLUTION_FILENAME= {name}/restart",
                f"SOLUTION_FILENAME= {name}/restart_settle",
            )
            continuation = continuation.replace("CFL_NUMBER= 0.05", "CFL_NUMBER= 0.25")
            continuation = continuation.replace("ITER= 300", "ITER= 1200")
            continuation = continuation.replace(
                f"CONV_FILENAME= {name}/history_settle",
                f"CONV_FILENAME= {name}/history_continue",
            )
            continuation = continuation.replace(
                f"RESTART_FILENAME= {name}/restart_settle",
                f"RESTART_FILENAME= {name}/restart_continue",
            )
            continuation = continuation.replace(
                f"VOLUME_FILENAME= {name}/flow_settle",
                f"VOLUME_FILENAME= {name}/flow_continue",
            )
            continuation = continuation.replace(
                f"SURFACE_FILENAME= {name}/wall_settle",
                f"SURFACE_FILENAME= {name}/wall_continue",
            )
            continuation = continuation.replace("OUTPUT_WRT_FREQ= 300", "OUTPUT_WRT_FREQ= 1200")
            (HERE / f"{name}_continue.cfg").write_text(continuation, encoding="ascii")


if __name__ == "__main__":
    main()
