# Eilmer 5 solver lane

Eilmer 5.0.0 is the selected open-source candidate for the hot
methalox-products/air plume track. It is installed in WSL2 because that is the
upstream-supported Linux workflow and supplies MPI cleanly.

This selection does **not** make any existing CFD output a physics-accepted ML
label. Eilmer supplies the required building blocks: compressible viscous flow,
RANS, multiple species and energy modes, finite-rate chemistry, structured and
unstructured grids, transient marching, steady JFNK, and MPI.
We still have to qualify the exact LOX/CH4 products-air mechanism, transport,
turbulence model, wall thermal condition, conservation, discretization and
experimental separation prediction.

## Pinned local installation

| Component | Version | Location |
|---|---|---|
| GDTk/Eilmer | `v5.0.0`, commit `f53f4609a0331d48efee69a4e4f3c3598378cc03` | `/home/adan/gdtk` |
| Installed binaries/data | optimized, MPI-enabled | `/home/adan/gdtkinst` |
| LDC compiler | `1.42.0` | `/home/adan/opt/ldc2-1.42.0-linux-x86_64` |

Load the environment and verify it from WSL:

```bash
source raptor_like_study/eilmer/eilmer5-env.sh
bash raptor_like_study/eilmer/check_eilmer_install.sh
```

`install_eilmer5_wsl.sh` reproduces the pinned build on another Ubuntu/WSL2
machine. It does not replace an existing `~/gdtk` checkout with a different
commit.

## What gets automated

An Eilmer case is plain text plus commands, so a DOE runner can generate one
isolated case directory per row and execute these stages:

```bash
lmr prep-gas -i gas-model.inp -o gas-model.lua
lmr prep-grid
lmr prep-sim
mpirun -np 6 lmr-mpi-run
lmr snapshot2vtk --all
```

The Lua inputs define geometry/grid, initial and boundary states, gas model,
chemistry, wall model, numerics and output cadence. Python should own the DOE,
provenance, validation gates, feature extraction and database/CSV summaries.
ParaView reads the VTK fields for interactive inspection; Python/Matplotlib is
better for repeatable paper plots and wall-sensor features. They are
complementary, not competing solvers.

## Required qualification sequence

1. Run the official serial/MPI smoke case and record solver provenance.
2. Reproduce published cold-N2 DLR-PAR anchors with Eilmer.
3. Benchmark an Eilmer multicomponent products/air mixing case before using the
   full nozzle mesh.
4. Select and document equilibrium, frozen and finite-rate LOX/CH4 chemistry.
5. Validate species thermodynamics and transport over the actual state domain.
6. Run supported turbulence sensitivities and justify the wall model.
7. Pass conservation, mesh, time-step, domain and statistical-stationarity
   gates before setting `physics_accepted=true`.

Never promote an installation test, smoke test or cheap screen into the final
training set.
