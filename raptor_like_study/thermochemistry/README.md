# Equilibrium LOX/CH4 thermochemistry

This directory contains the thermodynamic-property prototype used with SU2's
compressible `DATADRIVEN_FLUID` model. It is not a reacting products/air model
and it is not yet qualified to produce paper or ML labels.

## Current candidate

`LUT_lox_ch4_equilibrium_nasa_refined.drg` is the only current LUT candidate.
It contains 72 x 192 = 13,824 density/internal-energy nodes for one fixed
elemental mixture at O/F 3.2. The equilibrium products use NASA Glenn
polynomials from Cantera's `nasa_gas.yaml`, valid from 200 to 6000 K for the
selected species. NASA CEA, using liquid LOX/LCH4 reactant enthalpies, remains
the source of chamber temperature.

The independent 2,000-point holdout audit reports:

| Reconstructed quantity | p99 error | maximum error |
|---|---:|---:|
| Temperature | 0.1323% | 0.2565% |
| Pressure | 0.1599% | 0.2115% |
| Equilibrium sound speed squared | 0.1187% | 0.1977% |

No holdout point was outside 200-6000 K and no interpolated sound-speed square
was nonpositive. This passes the interpolation gate only. It does not establish
LUT-resolution convergence of separation location.

## Reproduce

From the repository Python environment:

```powershell
cd 'D:\PRUEBA SU2_2026\raptor_like_study\thermochemistry'
..\.venv\Scripts\python.exe generate_equilibrium_lut.py --workers 6
..\.venv\Scripts\python.exe validate_equilibrium_lut.py LUT_lox_ch4_equilibrium_nasa_refined.drg --samples 2000 --workers 6
..\.venv\Scripts\python.exe assess_lut_quality.py LUT_lox_ch4_equilibrium_nasa_refined.validation.json
```

The generator fails if a state leaves the declared thermodynamic-temperature
range. `assess_lut_quality.py` deliberately leaves `production_ready=false`
until the flow quantity of interest and the products/air formulation are also
validated.

## Rejected legacy tables

`LUT_lox_ch4_equilibrium.drg` and `LUT_lox_ch4_equilibrium_coarse.drg` are
retained only to reproduce historical software-integration runs. They were
generated with GRI-Mech thermodynamics, include states above the declared
polynomial range, and must not be used for new CFD or labels.

## Physical limits

1. SU2 `DATADRIVEN_FLUID` accepts density and internal energy as its two table
   inputs. It has no mixture-fraction coordinate, so one table cannot represent
   both methalox exhaust and ambient air.
2. The table assumes instantaneous equilibrium at a fixed elemental mixture.
   Frozen and finite-rate sensitivity remains required.
3. State-dependent viscosity and conductivity are not supplied by this table;
   the current Sutherland/Prandtl treatment is an unvalidated surrogate.
4. Condensed species are omitted. The chosen gas phase matches the nominal CEA
   chamber density and molecular weight within about 0.051% and 0.047%, but
   further state-grid comparison is still required.
5. A reacting-flow energy audit must use total enthalpy, including chemical
   energy and a consistent reference state. `Tmax < T0` is not a universal
   acceptance criterion.

Smoke tests prove file-format and solver integration only. They are never
training data.
