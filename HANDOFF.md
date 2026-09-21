# Eilmer nozzle-study handoff

## Current state

This repository has been cleaned of the former solver campaigns, meshes,
checkpoints, LUTs, logs and provisional results. Eilmer 5 is the only active
CFD backend. There are zero physics-accepted CFD labels.

Eilmer `v5.0.0` at commit
`f53f4609a0331d48efee69a4e4f3c3598378cc03` is installed under WSL2:

- source: `/home/adan/gdtk`
- install: `/home/adan/gdtkinst`
- compiler: `/home/adan/opt/ldc2-1.42.0-linux-x86_64`
- build: optimized, OpenMPI, multiespecies, multitemperature, turbulence

Serial, two-rank steady MPI, and six-rank real transient installation tests
passed. These tests verify software only, not nozzle physics.

The six-rank, 36,000-cell products/air benchmark also passed its software and
conservation screen in 18.0 minutes of solver wall time. Its small evidence is
under `raptor_like_study/cases/products_air_benchmark/results/`; it is not a
physics-accepted result or an ML label.

The complete fresh-machine procedure and execution order are in
`instrucciones iniciales.md`. The separate development-only ML task is in
`instrucciones para claude.md`.

## Retained evidence

- `DLR_PAR_full_contour.csv`: user-supplied working contour.
- `raptor_like_study/cases/cea`: NASA CEA inputs, outputs and parsed species.
- `raptor_like_study/cases/physical_doe.csv`: corrected DOE with NPR derived.
- `raptor_like_study/LITERATURE_REVIEW.md`: relevant public literature.
- `raptor_like_study/eilmer`: pinned installation and workflow files.
- `experiment_spec_final_hot_lox_ch4.yaml`: active study specification.

The geometry plus hot NASA methalox envelope is synthetic. It is not Raptor
hardware and is not the original DLR cold-N2 experiment.

## Next execution

Port the DLR-PAR contour and perform a geometry and mesh-quality-only check.
Then freeze the cold-N2 experimental inputs, generate a wall-resolved
axisymmetric grid, and reproduce the literature anchors before attempting the
hot application campaign. Do not interpret the passed mixing benchmark as
validation of nozzle separation, turbulence or finite-rate chemistry.

## Verification

```bash
bash raptor_like_study/eilmer/check_eilmer_install.sh
```

Read `physics_model_status.yaml` before launching. Production is intentionally
blocked until every listed model-form and validation gate is closed.
