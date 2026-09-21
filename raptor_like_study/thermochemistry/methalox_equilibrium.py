"""Equilibrium methalox-products phase backed by NASA Glenn polynomials."""

from __future__ import annotations

import cantera as ct


THERMO_DATABASE = "nasa_gas.yaml"
THERMO_TEMPERATURE_RANGE_K = (200.0, 6000.0)

# These are the gaseous species above the CEA trace threshold in the nominal
# chamber/throat/exit calculation, plus CH4 to establish the elemental ratio.
PRODUCT_SPECIES = (
    "CO",
    "CO2",
    "COOH",
    "H",
    "H2",
    "H2O",
    "H2O2",
    "HCHO,formaldehy",
    "HCO",
    "HCOOH",
    "HO2",
    "O",
    "O2",
    "O3",
    "OH",
    "CH4",
)


def new_equilibrium_products(of_ratio: float) -> ct.Solution:
    """Return a gas phase with the requested CH4/O2 elemental composition."""
    available = {species.name: species for species in ct.Species.list_from_file(THERMO_DATABASE)}
    missing = sorted(set(PRODUCT_SPECIES) - set(available))
    if missing:
        raise RuntimeError(f"Missing NASA gas species: {', '.join(missing)}")

    gas = ct.Solution(
        thermo="ideal-gas",
        kinetics=None,
        species=[available[name] for name in PRODUCT_SPECIES],
    )
    gas.TP = 300.0, 101325.0
    gas.set_equivalence_ratio(4.0 / of_ratio, "CH4", "O2")
    return gas


def assert_thermo_range(gas: ct.Solution) -> None:
    if not gas.min_temp <= gas.T <= gas.max_temp:
        raise ValueError(
            f"Equilibrium temperature {gas.T:.6g} K is outside the NASA-polynomial "
            f"range [{gas.min_temp:.6g}, {gas.max_temp:.6g}] K"
        )
