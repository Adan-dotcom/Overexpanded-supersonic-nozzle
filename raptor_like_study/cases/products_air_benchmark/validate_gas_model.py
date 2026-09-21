#!/usr/bin/env python3
"""Check thermodynamic, transport and diffusion finiteness over the screen envelope."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from gdtk.gas import GasModel, GasState


PRODUCTS_MASSF = {
    "H2O": 0.439433324785,
    "CO2": 0.367490271612,
    "CO": 0.182304134741,
    "H2": 0.0107250079269,
    "OH": 3.93300290688e-5,
    "O2": 1.49400110422e-7,
    "O": 3.65000269772e-8,
    "H": 7.74500572433e-6,
    "N2": 0.0,
}
AIR_MASSF = {"N2": 0.767, "O2": 0.233}
TEMPERATURES_K = (200.0, 300.0, 1738.69, 2500.0, 4000.0)
PRESSURES_PA = (1.0e4, 100836.186539, 5.2e6)


def validate(gas_model_path: Path) -> dict:
    model = GasModel(str(gas_model_path))
    records = []
    all_thermo_pass = True
    all_transport_pass = True
    all_diffusion_pass = True

    for mixture_name, massf in (("products", PRODUCTS_MASSF), ("air", AIR_MASSF)):
        for pressure in PRESSURES_PA:
            for temperature in TEMPERATURES_K:
                state = GasState(model)
                state.massf = massf
                state.p = pressure
                state.T = temperature
                state.update_thermo_from_pT()
                state.update_trans_coeffs()
                diffusion = model.binary_diffusion_coefficients(state)
                off_diagonal = [
                    value
                    for i, row in enumerate(diffusion)
                    for j, value in enumerate(row)
                    if i != j
                ]
                thermo_pass = (
                    all(math.isfinite(value) for value in (state.rho, state.u, state.a))
                    and state.rho > 0.0
                    and state.a > 0.0
                )
                transport_pass = (
                    all(math.isfinite(value) for value in (state.mu, state.k))
                    and state.mu > 0.0
                    and state.k > 0.0
                )
                diffusion_pass = all(
                    math.isfinite(value) and value > 0.0 for value in off_diagonal
                )
                passed = thermo_pass and transport_pass and diffusion_pass
                all_thermo_pass = all_thermo_pass and thermo_pass
                all_transport_pass = all_transport_pass and transport_pass
                all_diffusion_pass = all_diffusion_pass and diffusion_pass
                records.append(
                    {
                        "mixture": mixture_name,
                        "pressure_pa": pressure,
                        "temperature_k": temperature,
                        "density_kg_m3": state.rho,
                        "sound_speed_m_s": state.a,
                        "viscosity_pa_s": state.mu,
                        "conductivity_w_m_k": state.k,
                        "binary_diffusion_min_m2_s": min(off_diagonal),
                        "binary_diffusion_max_m2_s": max(off_diagonal),
                        "passed": passed,
                    }
                )

    return {
        "gas_model": str(gas_model_path.resolve()),
        "species": model.species_names,
        "temperature_range_k": [min(TEMPERATURES_K), max(TEMPERATURES_K)],
        "pressure_range_pa": [min(PRESSURES_PA), max(PRESSURES_PA)],
        "state_count": len(records),
        "thermodynamics_finite_positive": all_thermo_pass,
        "transport_finite_positive": all_transport_pass,
        "binary_diffusion_finite_positive": all_diffusion_pass,
        "all_checks_pass": (
            all_thermo_pass and all_transport_pass and all_diffusion_pass
        ),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gas_model", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = validate(args.gas_model)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if payload["all_checks_pass"] else 2)


if __name__ == "__main__":
    main()
