# CFD project handoff

## Read this first

There are **zero physics-accepted CFD labels** in this repository. Solver
completion, numerical convergence and physical acceptance are separate states.
Never train or publish the final sensor model from smoke, screen, mock or
failed-gate data.

The authoritative readiness file is
`raptor_like_study/physics_model_status.yaml`. Before launching a case, run:

```powershell
cd 'D:\PRUEBA SU2_2026\raptor_like_study'
.\.venv\Scripts\python.exe scripts\check_model_readiness.py cold_n2_validation --stage screen
.\.venv\Scripts\python.exe scripts\check_model_readiness.py hot_methalox_products_air_plume --stage production
```

The second command must currently exit with code 2 and list the physical
blockers. Do not bypass it by relabeling the run.

## Scientific tracks

### Cold-N2 validation

The DLR-PAR experiment used gaseous nitrogen. SU2 compressible RANS/URANS is a
reasonable solver family for this validation lane, but the published boundary
conditions, test-chamber setup, wall condition and uncertainty still need to be
digitized and reproduced. Cheap setup screens are allowed. Production
acceptance is not.

### Hot methalox application

The geometry is DLR-PAR while the chamber envelope comes from public NASA
LOX/LCH4 work. This is a synthetic methodology study, not Raptor hardware and
not the original DLR experiment.

The corrected open-atmosphere nominal point is `Pc=5.2 MPa`,
`Pa=101.325 kPa`, `NPR=51.32`, `O/F=3.2`; NASA CEA supplies `T0` from liquid
reactant enthalpies. `Pc=5.2 MPa` with `NPR=20` implies `Pa=260 kPa` and is only
a pressurized test-chamber condition.

The previous one-atmosphere hybrid LUT run is rejected as a physical model:
one methalox-products table represented both nozzle exhaust and the exterior.
The exterior was neither air nor pure CO2. It proved only that SU2 could load
the table and march a short URANS segment.

## SU2 capability decision

Source inspection of local SU2 8.5.0 established:

- `DATADRIVEN_FLUID` is a compressible EOS table with exactly two inputs,
  density and internal energy. It has no mixture-fraction dimension.
- `FLUID_MIXTURE` and `FLUID_FLAMELET` are incompressible-solver features.
- Compressible `SPECIES_TRANSPORT` transports scalars but does not couple a
  multicomponent reacting EOS to RANS.
- NEMO provides thermochemical nonequilibrium Euler/Navier-Stokes, but this
  release has no NEMO-RANS turbulence model.

Therefore the current stock-SU2 path cannot yet support the required
compressible turbulent products/air plume as modeled here. Resolve this with a
validated solver/formulation before long hot production runs. SU2 remains
useful for cold-N2 validation and single-composition internal sensitivity.

## Eilmer 5 candidate installation

Eilmer 5.0.0, commit `f53f4609a0331d48efee69a4e4f3c3598378cc03`,
is installed in WSL2 at `/home/adan/gdtkinst` from source in
`/home/adan/gdtk`. It was built optimized with OpenMPI, multiespecies,
multitemperature and turbulence support. Official serial and two-rank MPI
steady tests converged and exported VTK; a real-number, transient six-rank MPI
jet smoke test also completed. See `raptor_like_study/eilmer/README.md` and
`installation_report.json`.

This resolves software installation only. Hot production remains blocked on
the products/air benchmark, methalox mechanism, transport, turbulence, wall,
conservation, discretization, stationarity and experimental-validation gates.

## Thermochemistry repair

The old `LUT_lox_ch4_equilibrium.drg` and coarse companion are retained only
for historical reproduction. Their GRI-Mech thermodynamics were evaluated
outside the declared polynomial temperature range and are rejected.

The candidate replacement is:

`raptor_like_study/thermochemistry/LUT_lox_ch4_equilibrium_nasa_refined.drg`

It uses NASA Glenn gas-species polynomials, 72 x 192 = 13,824 nodes, and spans
`rho=0.02..6 kg/m3`, `e=-10.78..-1.5 MJ/kg`. A 2,000-point independent audit
gave maximum interpolation errors of 0.257% for temperature, 0.212% for
pressure and 0.198% for equilibrium sound-speed squared, with no invalid
sound-speed squares or temperatures outside 200-6000 K.

That passes only the interpolation gate. It remains blocked on separation-QoI
convergence across LUT resolutions, products/air treatment, transport, wall
thermal model and chemistry sensitivity.

## Correct energy interpretation

`Tmax < inlet T0` is not a universal reacting-flow acceptance rule. Chemical
recombination can trade chemical and sensible enthalpy. Production acceptance
requires global mass and total-energy-flux closure plus local total enthalpy
using consistent chemical reference states at every inlet. Historical
constant-gamma total-temperature plots apply only to the rejected effective
ideal-gas surrogate.

The fail-closed evaluator is `raptor_like_study/scripts/evaluate_physics_gate.py`.
It requires numerical, model-form, thermochemistry, transport, wall,
turbulence and experimental gates. Screens can survive numerically but can
never become training labels.

## Immediate work order

1. Complete cold-N2 literature digitization and reproduce several published
   DLR-PAR NPR anchors with SST and SA.
2. Validate mass/energy conservation, wall resolution, time step and mesh
   convergence against the cold-flow separation measurements.
3. Qualify the installed Eilmer candidate with a tiny compressible turbulent
   multicomponent products/air benchmark before any full mesh run.
4. Compare equilibrium, frozen and an appropriate finite-rate model; validate
   viscosity, conductivity and the wall thermal condition.
5. Only then reopen hot production and build labels that pass every gate.

## Recreate the environment

The scripts currently assume the clone is at `D:\PRUEBA SU2_2026` and SU2
8.5.0 is at `D:\SU2\v8.5.0`.

```powershell
cd 'D:\PRUEBA SU2_2026\raptor_like_study'
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Large VTK, restart and generated mesh files remain local and are inventoried in
`LOCAL_ARTIFACTS_MANIFEST.csv`. Git contains source, configs, compact results,
the active portable checkpoint and provenance. `RUN_STATUS.md` preserves the
full chronology; its top correction supersedes older recommendations.

`UI_SPEC.md` is the implementation brief for a future monitoring and analysis
interface. It explicitly separates execution status from evidence status and
must import the current repository as zero physics-accepted labels.
