# Equilibrium LOX/CH4 thermochemistry prototype

This directory couples a gaseous equilibrium-products model to SU2's
`DATADRIVEN_FLUID` lookup-table interface. It is a reproducible integration
prototype, not yet a paper-qualified chemistry model.

## Contents

- `probe_cantera_against_cea.py`: nominal chamber cross-check against NASA CEA.
- `generate_equilibrium_lut.py`: generates the eight-variable SU2 Dragon LUT.
- `LUT_lox_ch4_equilibrium.drg`: 36 x 72 production-resolution prototype table.
- `validate_equilibrium_lut.py`: independent off-node interpolation validation.
- `LUT_lox_ch4_equilibrium.validation.json`: numerical validation metrics.
- `npr20_datadriven_lut_smoke.cfg`: integration test on the old ambient mesh.

The table coordinates are density and specific internal energy. It contains
entropy and its first and second derivatives, from which SU2 reconstructs
temperature, pressure, and speed of sound. The elemental mixture is LOX/CH4 at
`O/F=3.2` (`phi=1.25`) and is equilibrated at constant `U,V` with Cantera 3.2
and GRI-Mech 3.0.

## Reproduce

From WSL:

```bash
cd '/mnt/d/PRUEBA SU2_2026/raptor_like_study/thermochemistry'
PY='/mnt/d/SU2/SU2_DataMiner/.venv312/bin/python'
$PY generate_equilibrium_lut.py --workers 6 --output LUT_lox_ch4_equilibrium.drg
$PY validate_equilibrium_lut.py LUT_lox_ch4_equilibrium.drg --samples 200 --workers 6
export OMPI_MCA_osc=pt2pt
mpirun -np 6 /mnt/d/SU2/v8.5.0/bin/SU2_CFD npr20_datadriven_lut_smoke.cfg
```

The final table spans `rho=0.02..8 kg/m^3` and
`e=-10.78..12 MJ/kg`. Its 200-point off-node test gave p95 errors of `0.31%`
for temperature and `0.71%` for pressure; all interpolated sound-speed squares
were positive. See the JSON and PNG for the full distribution.

## Scientific limits

1. GRI-Mech is being used as a convenient gaseous thermodynamic mechanism.
   NASA CEA 3.3.4 remains the reference and must be used to cross-check a grid
   of states, especially above 3500 K.
2. The table describes one equilibrium products mixture. It does not describe
   ambient air or products/air mixing. Production calculations therefore use
   the internal nozzle mesh and a static-pressure outlet.
3. Transport is still the nominal Sutherland/constant-Prandtl surrogate. A
   paper model needs state-dependent viscosity and conductivity validation.
4. Equilibrium chemistry is an assumption. Frozen and finite-rate sensitivity
   cases are still required before making a general hypersonic chemistry claim.
5. The effective-gas ideal-model restart files are thermodynamically
   incompatible with this LUT because their internal-energy reference differs.

The smoke tests prove software integration only. They must never be exported as
training labels.
