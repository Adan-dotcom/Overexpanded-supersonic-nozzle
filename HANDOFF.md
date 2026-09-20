# CFD project handoff

## Read this first

This repository contains the reproducible source, configurations, NASA CEA
outputs, thermochemistry LUT, diagnostics, plots, and decision history. Raw
solver fields/restarts/generated meshes are intentionally excluded because the
local workspace contains about 31 GiB and individual VTK files exceed GitHub's
100 MB limit. `LOCAL_ARTIFACTS_MANIFEST.csv` inventories those local artifacts.

There are currently **zero physics-accepted ML labels**. Do not train or report
the final sensor model until production cases pass every gate.

## Current scientific state

- Geometry: fixed DLR-PAR contour, area ratio 30.
- Primary application: synthetic DLR-PAR nozzle with LOX/CH4 products. It is
  not a Raptor reconstruction and not the original DLR cold-N2 experiment.
- Correct open-atmosphere anchor: `Pc=5.2 MPa`, `Pa=101.325 kPa`,
  `NPR=51.32`, `O/F=3.2`, `T0` from NASA CEA.
- `Pa=260 kPa` came from `Pc/NPR=5.2 MPa/20`; it is a pressurized-chamber
  diagnostic only.
- NASA CEA completed 48 corrected DOE points. See
  `raptor_like_study/cases/cea/physical_cea_summary.csv`.
- Five internal-nozzle screens failed the physics gate. A supersonic outlet
  remained near 18-21 kPa and did not transmit imposed backpressure upstream.
- The surviving path is the nozzle-plus-plume LUT/SST/HLLC case at one
  atmosphere. The steady branch was nonconvergent; the first-order URANS smoke
  test completed 10 steps at `dt=25 ns`, 30 inner iterations, on six MPI ranks.
- That smoke test remained finite, positive, and inside the LUT, but covered
  only `0.25 us`, had `y+ p95=2.847`, and showed no persistent separation. It
  is software feasibility, not a label.
- The external domain currently uses cold equilibrium combustion products,
  not air, because one data-driven fluid occupies the zone. This model-form
  limitation must remain explicit.

The detailed chronology is in `raptor_like_study/RUN_STATUS.md`. Assumptions
and literature are in `ASSUMPTIONS_AND_EVIDENCE.md` and
`LITERATURE_REVIEW.md`.

## Recreate on another Windows machine

The existing scripts assume the clone is at `D:\PRUEBA SU2_2026` and SU2 8.5.0
is at `D:\SU2\v8.5.0`. Either use those paths or update the scripts.

1. Install WSL2 Ubuntu, OpenMPI, SU2 8.5.0 with MPI, Python 3.12, and Gmsh.
2. Create a Python environment and install:

```powershell
cd 'D:\PRUEBA SU2_2026\raptor_like_study'
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Regenerate the hybrid pilot mesh:

```powershell
.\.venv\Scripts\python.exe ambient_mesh\generate_hybrid_mesh.py --profile pilot
```

4. Regenerate the corrected one-atmosphere LUT seed and configs:

```powershell
wsl.exe --cd "/mnt/d/PRUEBA SU2_2026/raptor_like_study/screening_campaign" `
  -e python3 generate_hybrid_lut_seed.py --ambient-pressure 101325 `
  --case-name sea_level_hybrid_lut_screen
.\.venv\Scripts\python.exe screening_campaign\make_sea_level_lut_configs.py
```

The WSL Python used previously had Cantera, NumPy, SciPy, Matplotlib, and
meshio. Adjust the executable path if those packages are installed elsewhere.

5. Recreate the stable checkpoint in this order from `screening_campaign`:

```bash
export OMPI_MCA_osc=pt2pt
SU2=/mnt/d/SU2/v8.5.0/bin/SU2_CFD
mpirun -np 6 "$SU2" sea_level_lut_smoke.cfg
mpirun -np 6 "$SU2" sea_level_lut_continue.cfg
mpirun -np 6 "$SU2" sea_level_lut_relax_safe.cfg
```

For the temporal smoke, copy `restart_safe.dat` to
`restart_safe_00000.dat`, then run `sea_level_lut_urans_smoke.cfg`.

## Next experiment

Continue the one-atmosphere case with segmented URANS rather than additional
steady pseudo-iterations. The estimated convective time is `42.842 us`.
At `dt=25 ns`, one flow-through time is about 1,714 steps and the minimum
three-flow-through observation window is about 5,142 steps. Use segments of
100-250 steps, retain restart files locally, and write full VTK fields only at
checkpoints to control disk usage.

Before accepting a label, require:

- finite positive states and zero LUT extrapolation points;
- relative mass imbalance <= 0.5% and energy imbalance <= 1%;
- local total-enthalpy excess <= 1%;
- adequate inner convergence or demonstrated time-step independence;
- `y+ p95 <= 1` and `y+ max <= 2`;
- negative wall shear persisting at least 1 mm;
- at least three flow-through times and final `x_sep` drift <= 0.1 mm;
- medium/fine `x_sep` difference <= 0.3 mm;
- turbulence and thermal/chemistry sensitivity reporting.

Also begin the cold-N2 DLR-PAR anchors around NPR 20, 23.7/23.8, 40, 52.8,
57.2, and 65. Those provide the experimental validation; the hot methalox
campaign alone cannot validate the method.

## ML state

`raptor_like_study/ml_pipeline/case_registry.csv` contains 48 planned physical
cases and zero accepted profiles. `build_training_dataset.py` intentionally
refuses to create a final dataset until `physics_accepted=true` profiles exist.
Mock-data plots are development-only and always nonpublishable.

