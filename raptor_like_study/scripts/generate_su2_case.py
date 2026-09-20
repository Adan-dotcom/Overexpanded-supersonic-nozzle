import argparse
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "cases" / "cea" / "cea_summary.csv"
OUT_ROOT = ROOT / "cases" / "su2"
NC = 60
ND = 220
NO = 160
NR = 100


def radius(x, xin, xt, xe, rin, rt, re):
    if x <= xt:
        s = (x - xin) / (xt - xin)
        return rt + 0.5 * (rin - rt) * (1.0 + math.cos(math.pi * s))
    if x >= xe:
        return re
    s = (x - xt) / (xe - xt)
    q = 3.0 * s * s - 2.0 * s * s * s
    return rt + (re - rt) * q


def mesh(path, xin, xt, xe, xout, rin, rt, re):
    xs = ([xin + (xt - xin) * i / NC for i in range(NC)] +
          [xt + (xe - xt) * i / ND for i in range(ND + 1)] +
          [xe + (xout - xe) * i / NO for i in range(1, NO + 1)])
    na = len(xs) - 1
    node = lambda i, j: i * (NR + 1) + j
    def rf(j):
        d = (NR - j) / NR
        return 1.0 - (math.exp(7.0 * d) - 1.0) / (math.exp(7.0) - 1.0)
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write("NDIME= 2\nNELEM= %d\n" % (na * NR))
        eid = 0
        for i in range(na):
            for j in range(NR):
                f.write(f"9 {node(i,j)} {node(i+1,j)} {node(i+1,j+1)} {node(i,j+1)} {eid}\n")
                eid += 1
        f.write("NPOIN= %d\n" % (len(xs) * (NR + 1)))
        for i, x in enumerate(xs):
            for j in range(NR + 1):
                f.write(f"{x:.12e} {radius(x,xin,xt,xe,rin,rt,re)*rf(j):.12e} {node(i,j)}\n")
        f.write("NMARK= 4\nMARKER_TAG= WALL\nMARKER_ELEMS= %d\n" % na)
        for i in range(na):
            f.write(f"3 {node(i,NR)} {node(i+1,NR)}\n")
        f.write("MARKER_TAG= INLET\nMARKER_ELEMS= %d\n" % NR)
        for j in range(NR):
            f.write(f"3 {node(0,j+1)} {node(0,j)}\n")
        f.write("MARKER_TAG= OUTLET\nMARKER_ELEMS= %d\n" % NR)
        for j in range(NR):
            f.write(f"3 {node(na,j)} {node(na,j+1)}\n")
        f.write("MARKER_TAG= AXIS\nMARKER_ELEMS= %d\n" % na)
        for i in range(na):
            f.write(f"3 {node(i+1,0)} {node(i,0)}\n")


def config(path, row):
    pc = float(row["chamber_pressure_pa"])
    pb = float(row["back_pressure_pa"])
    tc = float(row["temperature_chamber_k"])
    gamma = float(row["gamma_chamber"])
    mw = float(row["molecular_weight_chamber"])
    gas_r = 8314.462618 / mw
    text = f"""% Generated from CEA case {row['case_id']}\nSOLVER= RANS\nKIND_TURB_MODEL= SST\nSST_OPTIONS= V2003m, COMPRESSIBILITY-SARKAR\nMATH_PROBLEM= DIRECT\nRESTART_SOL= NO\nAXISYMMETRIC= YES\nMACH_NUMBER= 0.01\nAOA= 0.0\nINIT_OPTION= TD_CONDITIONS\nFREESTREAM_OPTION= TEMPERATURE_FS\nFREESTREAM_PRESSURE= {pb:.8f}\nFREESTREAM_TEMPERATURE= {tc:.8f}\nREF_DIMENSIONALIZATION= DIMENSIONAL\nFLUID_MODEL= IDEAL_GAS\nGAMMA_VALUE= {gamma:.10f}\nGAS_CONSTANT= {gas_r:.10f}\nVISCOSITY_MODEL= SUTHERLAND\nMU_REF= 1.716E-5\nMU_T_REF= 273.15\nSUTHERLAND_CONSTANT= 110.4\nCONDUCTIVITY_MODEL= CONSTANT_PRANDTL\nPRANDTL_LAM= 0.72\nTURBULENT_CONDUCTIVITY_MODEL= CONSTANT_PRANDTL_TURB\nPRANDTL_TURB= 0.90\nMARKER_HEATFLUX= ( WALL, 0.0 )\nMARKER_SYM= ( AXIS )\nMARKER_RIEMANN= ( INLET, TOTAL_CONDITIONS_PT, {pc:.8f}, {tc:.8f}, 1.0, 0.0, 0.0, OUTLET, STATIC_PRESSURE, {pb:.8f}, 0.0, 0.0, 0.0, 0.0 )\nMARKER_MONITORING= ( WALL )\nMARKER_PLOTTING= ( WALL )\nNUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES\nCFL_NUMBER= 0.05\nCFL_ADAPT= YES\nCFL_ADAPT_PARAM= ( 0.5, 1.05, 0.02, 1.0 )\nMUSCL_FLOW= NO\nSLOPE_LIMITER_FLOW= VENKATAKRISHNAN_WANG\nVENKAT_LIMITER_COEFF= 0.05\nLINEAR_SOLVER= FGMRES\nLINEAR_SOLVER_PREC= ILU\nLINEAR_SOLVER_ERROR= 1E-4\nLINEAR_SOLVER_ITER= 8\nCONV_NUM_METHOD_FLOW= ROE\nENTROPY_FIX_COEFF= 0.1\nTIME_DISCRE_FLOW= EULER_IMPLICIT\nCONV_NUM_METHOD_TURB= SCALAR_UPWIND\nTIME_DISCRE_TURB= EULER_IMPLICIT\nCFL_REDUCTION_TURB= 0.5\nITER= 3000\nCONV_RESIDUAL_MINVAL= -7\nCONV_STARTITER= 100\nCONV_CAUCHY_ELEMS= 100\nCONV_CAUCHY_EPS= 1E-6\nMESH_FILENAME= nozzle.su2\nMESH_FORMAT= SU2\nSOLUTION_FILENAME= restart\nCONV_FILENAME= history\nRESTART_FILENAME= restart\nVOLUME_FILENAME= flow\nSURFACE_FILENAME= wall\nOUTPUT_FILES= ( RESTART, PARAVIEW_ASCII, SURFACE_PARAVIEW_ASCII, SURFACE_CSV )\nVOLUME_OUTPUT= ( COORDINATES, SOLUTION, PRIMITIVE )\nOUTPUT_WRT_FREQ= 500\nHISTORY_WRT_FREQ_INNER= 1\nSCREEN_WRT_FREQ_INNER= 20\nSCREEN_OUTPUT= ( INNER_ITER, RMS_DENSITY, RMS_ENERGY, RMS_TKE, RMS_DISSIPATION )\n"""
    path.write_text(text, encoding="ascii", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-id", default="case_0001")
    case_id = ap.parse_args().case_id
    with SUMMARY.open(newline="", encoding="ascii") as f:
        rows = {r["case_id"]: r for r in csv.DictReader(f)}
    row = rows[case_id]
    out = OUT_ROOT / case_id
    out.mkdir(parents=True, exist_ok=True)
    rt = float(row["throat_radius_m"])
    ar = float(row["area_ratio"])
    ld = float(row["divergent_length_m"])
    re = rt * math.sqrt(ar)
    mesh(out / "nozzle.su2", -0.20, 0.0, ld, ld + 0.30, 2.5 * rt, rt, re)
    config(out / "nozzle.cfg", row)
    mw = float(row["molecular_weight_chamber"])
    (out / "metadata.txt").write_text(
        f"case_id={case_id}\narea_ratio={ar}\nthroat_radius_m={rt}\nexit_radius_m={re}\n"
        f"gas_constant={8314.462618 / mw}\n", encoding="ascii")
    print(f"Generated {out}; Ae/At={ar:.3f}, exit radius={re:.5f} m")


if __name__ == "__main__":
    main()
