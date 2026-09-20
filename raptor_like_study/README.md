# DLR-PAR sparse-sensor nozzle separation study

This project is a reproducible research scaffold, not a reconstruction of the
proprietary SpaceX Raptor engine. Publicly reported operating values are used as
a reference envelope and every assumed value is recorded.

## Current physical envelope

- Propellants: liquid oxygen and liquid methane.
- Chamber pressure: 5.1-5.4 MPa for the NASA-LLAMA-scale nominal campaign.
- O/F: 3.1-3.3, with NASA CEA computing chamber temperature case by case.
- Geometry: fixed DLR-PAR contour, area ratio 30.
- Ambient pressure: 50-101.325 kPa for the nominal open-atmosphere campaign.
- Exploratory ground throttling: 2.0-5.4 MPa at 101.325 kPa.
- Chemistry: NASA CEA equilibrium and frozen comparisons.
- CFD labels: compressible RANS/URANS nozzle solutions, wall `Cf_t`, pressure,
  separation and reattachment locations.

These values define a synthetic DLR-PAR/methalox methodology study. They must
not be described as Raptor geometry, proprietary engine data, or a recreation
of the original cold-nitrogen DLR experiment.

The corrected 48-point chemistry batch is in `cases/physical_doe.csv`. NASA
CEA results are joined in `cases/cea/physical_cea_summary.csv`, with chamber
temperatures from `3365.9` to `3501.7 K`; species are stored in
`cases/cea/physical_products_long.csv`. These are case inputs, not CFD labels.

## Study stages

1. Run NASA CEA for combustion products and thermodynamic properties.
2. Generate a parameterized axisymmetric nozzle mesh.
3. Run a robust RANS continuation, then URANS where the separated shock moves.
4. Extract `x_sep`, `x_reattach`, shock location and wall-pressure features.
5. Build a case-level dataset and train/test a neural surrogate by geometry.
6. Validate against published separated-nozzle data before claiming engine-level
   predictive accuracy.

## Tools

NASA CEA v3.3.4 binaries are in `tools/cea-3.3.4`. The Linux executable is run
from WSL because the Windows gfortran executable needs an external Fortran
runtime. SU2 and MPI remain the CFD solver layer.

## Reproduce the chemistry stage

From PowerShell in this directory:

```powershell
.\scripts\run_cea_baseline.ps1
wsl.exe -d Ubuntu -- bash '/mnt/d/PRUEBA SU2_2026/raptor_like_study/scripts/run_cea_doe.sh'
python .\scripts\parse_cea_doe.py
```

The CEA inputs use liquid `O2(L)` and `CH4(L)`, chamber pressure, O/F, and
area ratio. The resulting equilibrium burned-gas state is supplied to the
nozzle CFD inlet; this stage does not resolve injectors or combustion.

## CFD pilot

`cases/su2/case_0001` is generated directly from the CEA summary. Its mesh and
configuration have been exercised in both single-process and two-process MPI
mode. The short pilot is not treated as a converged physical result; production
cases need continuation and convergence checks before their separation labels
enter the dataset.

```powershell
wsl.exe -d Ubuntu -- bash '/mnt/d/PRUEBA SU2_2026/raptor_like_study/scripts/run_su2_case.sh' case_0001 2
```

CEA is a local command-line Fortran program, not a hosted API. The automation
writes its text input, executes the official binary, and parses its text output.
SU2 is likewise a local executable driven by a `.cfg` file, keeping each case
reproducible without depending on an undocumented web service.
