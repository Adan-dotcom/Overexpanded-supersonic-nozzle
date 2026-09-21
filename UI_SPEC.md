# Eilmer CFD study interface specification

## Purpose

Build a local-first interface that lets a researcher configure, launch,
monitor and audit Eilmer nozzle studies without hiding the equations, gas
model, mesh or evidence gates. The UI must make it difficult to confuse a
successful process with validated physics.

## Technology

- Backend: Python FastAPI, Pydantic and SQLite.
- Worker: durable local job queue launching WSL2 processes without shell-string
  interpolation.
- Frontend: React/TypeScript with a compact engineering dashboard.
- Fields: ParaView-compatible VTK plus decimated browser previews.
- Plots: Plotly for residuals, wall pressure/shear and sensor comparisons.

## Core views

### Dashboard

Show solver health, active/queued runs, CPU/RAM/disk, accepted-label count and
failed evidence gates. Installation tests must be visually distinct from CFD
cases.

### Case editor

Expose geometry, `Pc`, `Pa`, derived NPR, O/F, CEA state, species, reactions,
transport, wall model, turbulence, numerics, grid controls, MPI blocks/ranks
and output cadence. Units are mandatory and all derived values are read-only.

### Mesh inspector

Show block topology, dimensions, cell count, first wall spacing, growth ratio,
orthogonality/skewness and refinement regions. Provide wall-normal and throat/
shock-region zooms. Generated grids remain outside Git.

### Run monitor

Represent `prep-gas`, `prep-chem`, `prep-grid`, `prep-sim`, solver and
`snapshot2vtk` as separate stages. Stream logs and plot residual, CFL, time,
mass/energy imbalance, extrema and species closure. Parse `STOP-REASON`,
`FINAL-STEP`, `FINAL-TIME`, build flavour, number type and MPI flavour.

### Results

Provide interactive Mach, pressure, temperature, density, velocity, species
and turbulence fields. Plot wall pressure, wall shear, `Cf`, shock and
separation/reattachment locations. Link every scalar result to its source
snapshot and extraction method.

### Evidence gates

Show numerical completion, positivity, species closure, conservation,
thermochemical range, transport, wall, turbulence, mesh, time-step,
stationarity and experimental validation independently. Only an explicit
all-pass state may set `physics_accepted=true`.

### Sensors and ML

Allow fixed candidate stations, sensor range/noise/bandwidth, layout comparison
and grouped dataset construction. Block final training when the accepted-label
count is zero. Keep provisional experiments clearly non-publishable.

## Eilmer backend contract

- Commands are argument arrays with registered working directories.
- Support `lmr-run`, `lmr-mpi-run`, `lmrZ-run` and `lmrZ-mpi-run` explicitly.
- Default local production preset is six ranks, subject to case benchmarks.
- Capture Eilmer commit, effective Lua inputs, gas/reaction file hashes,
  environment, command, start/end time and exit reason.
- Cancellation terminates the complete MPI process group.
- Two runs never share an output directory.

## File policy

Inputs, compact metadata and paper figures may be versioned. `lmrsim`, VTK,
restarts, generated grids and full logs live in a registered artifact root.
Display disk warnings and stop cleanly before exhaustion.

## Acceptance criteria

- Importing this repository shows zero physics-accepted labels.
- The UI derives NPR from `Pc/Pa` and detects unit mistakes.
- A six-rank smoke case can be launched, monitored and cancelled safely.
- Restarting the UI does not lose job state.
- No user-controlled name or path can inject commands or escape registered
  roots.
- The researcher can reach any failed gate and its evidence in three actions.
