import json
from pathlib import Path

from methalox_equilibrium import PRODUCT_SPECIES, THERMO_DATABASE, new_equilibrium_products


HERE = Path(__file__).resolve().parent
OF_RATIO = 3.20
PHI = 4.0 / OF_RATIO


def equilibrium_products():
    # CEA determines the chamber temperature using the liquid-propellant
    # enthalpies. Here we cross-check only the gaseous products EOS at that
    # already-established T,P state.
    gas = new_equilibrium_products(OF_RATIO)
    gas.TP = 3485.33, 5.2e6
    gas.equilibrate("TP")
    return gas


gas = equilibrium_products()
cantera_chamber = {
    "temperature_k": gas.T,
    "pressure_pa": gas.P,
    "density_kg_m3": gas.density,
    "internal_energy_j_kg": gas.int_energy_mass,
    "enthalpy_j_kg": gas.enthalpy_mass,
    "entropy_j_kg_k": gas.entropy_mass,
    "cp_j_kg_k": gas.cp_mass,
    "cv_j_kg_k": gas.cv_mass,
    "gamma_frozen": gas.cp_mass / gas.cv_mass,
    "molecular_weight_kg_kmol": gas.mean_molecular_weight,
    "sound_speed_frozen_m_s": gas.sound_speed,
}
cantera_chamber["major_mole_fractions"] = {
    species: gas[species].X[0]
    for species in ("H2O", "CO2", "CO", "H2", "OH", "O2", "O", "H")
}

cea_chamber = {
    "temperature_k": 3485.33,
    "pressure_pa": 5.2e6,
    "density_kg_m3": 3.772,
    "internal_energy_j_kg": -3.012033e6,
    "enthalpy_j_kg": -1.633393e6,
    "entropy_j_kg_k": 12499.0,
    "cp_equilibrium_j_kg_k": 6853.1,
    "cp_frozen_j_kg_k": 2373.2,
    "gamma_equilibrium": 1.1326,
    "molecular_weight_kg_kmol": 21.0198,
    "sound_speed_equilibrium_m_s": 1249.59,
}

relative_errors_percent = {}
for key in ("temperature_k", "density_kg_m3", "molecular_weight_kg_kmol"):
    relative_errors_percent[key] = 100.0 * (cantera_chamber[key] / cea_chamber[key] - 1.0)

result = {
    "model": "Cantera equilibrium using NASA Glenn gaseous-species polynomials",
    "thermo_database": THERMO_DATABASE,
    "thermo_species": list(PRODUCT_SPECIES),
    "of_ratio": OF_RATIO,
    "equivalence_ratio": PHI,
    "cantera_chamber": cantera_chamber,
    "cea_chamber_reference": cea_chamber,
    "relative_errors_percent": relative_errors_percent,
    "limitations": [
        "CEA, not Cantera, sets the adiabatic chamber state from the liquid reactants.",
        "Absolute energy and enthalpy are not compared until the two codes' reference conventions are reconciled.",
        "Cantera sound speed and cp reported here are frozen-composition derivatives.",
        "Condensed carbon and liquid water are excluded by the gas-phase mechanism.",
    ],
}
(HERE / "cantera_cea_probe.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
print(json.dumps(result, indent=2))
