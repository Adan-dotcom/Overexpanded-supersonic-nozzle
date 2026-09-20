import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent


def row(lines, label, count=3):
    for line in lines:
        if line.strip().startswith(label):
            values = []
            for token in line.split()[::-1]:
                try:
                    values.append(float(token.replace("E", "e")))
                except ValueError:
                    if values:
                        break
            return list(reversed(values[:count]))
    raise KeyError(label)


def parse(path):
    lines = path.read_text(encoding="ascii").splitlines()
    nstations = 3 if any("CHAMBER       THROAT         EXIT" in line for line in lines) else 2
    data = {
        "pressure_bar": row(lines, "P, bar", nstations),
        "temperature_k": row(lines, "T, K", nstations),
        "density_kg_m3": row(lines, "Density,", nstations),
        "molecular_weight_kg_kmol": row(lines, "M, (1/n)", nstations),
        "gamma_s": row(lines, "Gamma_s", nstations),
        "mach": row(lines, "Mach", nstations),
        "viscosity_millipoise": row(lines, "Visc,", nstations),
    }
    return data


def main():
    equilibrium = parse(HERE / "equilibrium.out")
    frozen = parse(HERE / "frozen_throat.out")
    # The second Cp row in the frozen output is the fixed-composition value.
    lines = (HERE / "frozen_throat.out").read_text(encoding="ascii").splitlines()
    frozen_marker = next(i for i, line in enumerate(lines) if "WITH FROZEN REACTIONS" in line)
    frozen_cp = [float(v) for v in lines[frozen_marker + 1].split()[-3:]]
    frozen_k = [float(v) for v in lines[frozen_marker + 2].split()[-3:]]
    frozen_pr = [float(v) for v in lines[frozen_marker + 3].split()[-3:]]
    frozen.update({
        "cp_frozen_kj_kg_k": frozen_cp,
        "conductivity_frozen_mw_cm_k": frozen_k,
        "prandtl_frozen": frozen_pr,
    })
    mw_throat = frozen["molecular_weight_kg_kmol"][1]
    gas_r = 8314.462618 / mw_throat
    cp_throat = 1000.0 * frozen_cp[1]
    gamma = cp_throat / (cp_throat - gas_r)
    t1, t2 = frozen["temperature_k"][1], frozen["temperature_k"][2]
    mu1 = frozen["viscosity_millipoise"][1] * 1e-4
    mu2 = frozen["viscosity_millipoise"][2] * 1e-4
    ratio = (mu2 / mu1) / (t2 / t1) ** 1.5
    sutherland = (t1 - ratio * t2) / (ratio - 1.0)
    result = {
        "case": {"pc_pa": 5.2e6, "of_ratio": 3.2, "area_ratio": 30.0},
        "equilibrium": equilibrium,
        "frozen_at_throat": frozen,
        "su2_effective_frozen_gas": {
            "gas_constant_j_kg_k": gas_r,
            "gamma": gamma,
            "mu_ref_pa_s": mu1,
            "mu_ref_temperature_k": t1,
            "sutherland_constant_k": sutherland,
            "prandtl_laminar": frozen_pr[1],
            "total_temperature_k": equilibrium["temperature_k"][0],
        },
    }
    (HERE / "nominal_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result["su2_effective_frozen_gas"], indent=2))


if __name__ == "__main__":
    main()
