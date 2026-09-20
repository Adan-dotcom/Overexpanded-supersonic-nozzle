import argparse
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_geometry():
    with (ROOT / "geometry.csv").open(newline="", encoding="ascii") as f:
        return [(float(r["x"]), float(r["r"])) for r in csv.DictReader(f)]


def interp(x, geom):
    for (x0, r0), (x1, r1) in zip(geom, geom[1:]):
        if x0 <= x <= x1:
            q = (x - x0) / (x1 - x0)
            return r0 + q * (r1 - r0)
    return geom[0][1] if x < geom[0][0] else geom[-1][1]


def make_mesh(path, level):
    counts = {"coarse": (80, 35), "medium": (160, 60), "fine": (320, 100)}
    nx, nr = counts[level]
    geom = read_geometry()
    xmin, xmax = geom[0][0], geom[-1][0]
    xs = [xmin + (xmax - xmin) * i / nx for i in range(nx + 1)]
    node = lambda i, j: i * (nr + 1) + j
    def rf(j):
        d = (nr - j) / nr
        return 1.0 - (math.exp(6.0 * d) - 1.0) / (math.exp(6.0) - 1.0)
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write("NDIME= 2\nNELEM= %d\n" % (nx * nr))
        eid = 0
        for i in range(nx):
            for j in range(nr):
                f.write(f"9 {node(i,j)} {node(i+1,j)} {node(i+1,j+1)} {node(i,j+1)} {eid}\n")
                eid += 1
        f.write("NPOIN= %d\n" % ((nx + 1) * (nr + 1)))
        for i, x in enumerate(xs):
            r = interp(x, geom)
            for j in range(nr + 1):
                f.write(f"{x:.10e} {r * rf(j):.10e} {node(i,j)}\n")
        f.write("NMARK= 4\n")
        f.write("MARKER_TAG= WALL\nMARKER_ELEMS= %d\n" % nx)
        for i in range(nx): f.write(f"3 {node(i,nr)} {node(i+1,nr)}\n")
        f.write("MARKER_TAG= INLET\nMARKER_ELEMS= %d\n" % nr)
        for j in range(nr): f.write(f"3 {node(0,j+1)} {node(0,j)}\n")
        f.write("MARKER_TAG= OUTLET\nMARKER_ELEMS= %d\n" % nr)
        for j in range(nr): f.write(f"3 {node(nx,j)} {node(nx,j+1)}\n")
        f.write("MARKER_TAG= AXIS\nMARKER_ELEMS= %d\n" % nx)
        for i in range(nx): f.write(f"3 {node(i+1,0)} {node(i,0)}\n")


def make_cfg(path, level, solver):
    turbulent = solver == "rans"
    turbulence = "KIND_TURB_MODEL= SST" if turbulent else ""
    model = "RANS" if turbulent else "EULER"
    extra = ""
    wall_bc = "MARKER_HEATFLUX= ( WALL, 0.0 )" if turbulent else "MARKER_EULER= ( WALL )"
    template = f"""% Tutorial nozzle: {solver}, {level}\nSOLVER= {model}\n{turbulence}\nMATH_PROBLEM= DIRECT\nRESTART_SOL= NO\nAXISYMMETRIC= YES\nMACH_NUMBER= 0.01\nAOA= 0.0\nINIT_OPTION= TD_CONDITIONS\nFREESTREAM_OPTION= TEMPERATURE_FS\nFREESTREAM_PRESSURE= 75000.0\nFREESTREAM_TEMPERATURE= 600.0\nREF_DIMENSIONALIZATION= DIMENSIONAL\nFLUID_MODEL= IDEAL_GAS\nGAMMA_VALUE= 1.4\nGAS_CONSTANT= 287.058\nVISCOSITY_MODEL= SUTHERLAND\nMU_REF= 1.716E-5\nMU_T_REF= 273.15\nSUTHERLAND_CONSTANT= 110.4\nCONDUCTIVITY_MODEL= CONSTANT_PRANDTL\nPRANDTL_LAM= 0.72\nTURBULENT_CONDUCTIVITY_MODEL= CONSTANT_PRANDTL_TURB\nPRANDTL_TURB= 0.90\n{wall_bc}\nMARKER_SYM= ( AXIS )\nMARKER_RIEMANN= ( INLET, TOTAL_CONDITIONS_PT, 2000000.0, 600.0, 1.0, 0.0, 0.0, OUTLET, STATIC_PRESSURE, 75000.0, 0.0, 0.0, 0.0, 0.0 )\nMARKER_MONITORING= ( WALL )\nMARKER_PLOTTING= ( WALL )\nNUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES\nCFL_NUMBER= 0.1\nCFL_ADAPT= YES\nCFL_ADAPT_PARAM= ( 0.5, 1.05, 0.02, 1.0 )\nMUSCL_FLOW= NO\nCONV_NUM_METHOD_FLOW= ROE\nENTROPY_FIX_COEFF= 0.1\nTIME_DISCRE_FLOW= EULER_IMPLICIT\n{extra}\nITER= 1000\nCONV_RESIDUAL_MINVAL= -7\nCONV_STARTITER= 100\nCONV_CAUCHY_ELEMS= 100\nCONV_CAUCHY_EPS= 1E-6\nMESH_FILENAME= mesh.su2\nMESH_FORMAT= SU2\nCONV_FILENAME= history\nVOLUME_FILENAME= flow\nSURFACE_FILENAME= wall\nOUTPUT_FILES= ( RESTART, PARAVIEW_ASCII, SURFACE_PARAVIEW_ASCII, SURFACE_CSV )\nVOLUME_OUTPUT= ( COORDINATES, SOLUTION, PRIMITIVE )\nOUTPUT_WRT_FREQ= 500\nHISTORY_WRT_FREQ_INNER= 1\nSCREEN_WRT_FREQ_INNER= 20\nSCREEN_OUTPUT= ( INNER_ITER, RMS_DENSITY, RMS_ENERGY )\n"""
    path.write_text(template, encoding="ascii", newline="\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--level", choices=("coarse", "medium", "fine"), default="coarse")
    p.add_argument("--solver", choices=("euler", "rans"), default="euler")
    a = p.parse_args()
    out = ROOT / "runs" / f"{a.solver}_{a.level}"
    out.mkdir(parents=True, exist_ok=True)
    make_mesh(out / "mesh.su2", a.level)
    make_cfg(out / "nozzle.cfg", a.level, a.solver)
    print(f"Created {out}")


if __name__ == "__main__":
    main()
