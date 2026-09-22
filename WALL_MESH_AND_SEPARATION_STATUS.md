# Wall mesh and separation-detector status

## Scope

This is a synthetic cold-N2 numerical qualification, not matched DLR
validation. No result is physics accepted or training eligible. The work is
limited to the wall mesh and the definitions of separation and shock.

## Three wall meshes

All meshes retain the same reconstructed contour, external plume topology,
six MPI ranks, `k_log_omega`, fixed 300 K wall and `wall_function=false`.
Wall-normal clustering uses Eilmer's documented `GeometricFunction`; the
growth ratio `r=1.3` is inherited from the official laminar-flat-plate
example. The grid audit measures the generated spacing rather than trusting
the nominal edge input.

| mesh | cells | normal cells | actual first-cell range | geometry |
|---|---:|---:|---:|---|
| wall-coarse | 61,440 | 112 | 0.0359--0.0925 micrometres | pass |
| wall-medium | 72,960 | 136 | 0.0179--0.0463 micrometres | pass |
| wall-fine | 84,480 | 160 | 0.0090--0.0231 micrometres | pass |

All coordinates are finite and all signed cell areas are positive. Heavy grid
artifacts and individual `mesh-audit.json` files are under
`/home/adan/eilmer-artifacts/cold-n2-wall-mesh-family-20260921-04/`.

Geometry passing does not establish `y+ <= 1`; that requires a completed flow
solution.

## Flow attempts and gate

The official Hakkinen explicit transient formulation, initialized through the
official `FlowSolution` fine-grid continuation pattern, reached only
`t=5.206e-11 s` at step 140 with `dt=5.123e-13 s`. It was stopped because it
could not reach even the 1 microsecond qualification interval within the hard
60-minute limit.

The original steady continuation retained Hakkinen's transient
`vertices/divergence` viscous derivatives while Newton's Jacobian evaluated
the least-squares path. A debug build located the resulting `SIGSEGV` at
`flowgradients.d:699`, where the two-dimensional WLSQ velocity workspace was
not allocated. Steady mode now uses the exact official Mabey settings:
cell-centred least squares, weighted QR, and boundary-face correction. No ILU,
Newton, CFL, limiter or boundary control was changed.

With that correction, the official complex-Frechet `lmrZ-mpi-run` executable
converged the 23,040-cell screen continuation in 1,421 steps and 2,131 solver
seconds. The relative global residual reached `9.234486e-11`; pressure,
density and temperature remained finite and positive, and VTK plus wall loads
were exported. This verifies the corrected steady workflow, not wall
resolution.

A direct interpolation from that screen to `wall-coarse` still failed. The
first-cell height changes from 0.2--1.1 mm to at most 0.0925 micrometres. At
step 47 the `k` and `omega` residuals rose sharply; repeated rejected steps
reduced CFL below the unchanged official minimum at step 56. This was a clean
numerical continuation failure, not a nonphysical state or experimental
disagreement. Medium and fine were gated off.

Three continuation-only grids (`bridge-100um`, `bridge-10um`, and
`bridge-1um`) now reduce first-cell height one decade at a time using the
official coarse-to-fine `FlowSolution` pattern. They do not belong to the
three-grid convergence family and cannot supply measurements or labels. The
bridge queue is still in progress under
`/home/adan/eilmer-artifacts/wall-mesh-bridge-no-limit-20260922-01/`.

Therefore the current wall-resolution decision is **NO-GO**: the mesh family
exists and passes geometry, but `y+ <= 1` has not been demonstrated and no
separation result from it is defensible.

## Separation and shock definitions

The new detector:

- discards the first 2 mm after the throat and the last 2 mm before the lip;
- projects wall shear onto the downstream wall tangent;
- applies a three-point running median;
- requires four consecutive positive samples before and four consecutive
  negative samples after the crossing;
- linearly interpolates only that persistent shear crossing for `x_sep`;
- locates shock independently at the largest positive centred wall-pressure
  gradient in the same usable divergent region.

Reauditing the old 1 ms NPR=35 transient screen changes its result from a false
lip separation to `x_sep=null`; the independently measured provisional shock
is `x_shock=0.10808978 m`. The converged steady screen reports provisional
`x_sep=0.08907412 m` and independent `x_shock=0.08268924 m`, but its nozzle
maximum remains `y+=6811.9`. The disagreement between the transient and steady
screens reinforces that neither is a paper-ready separation result.

Compact evidence is in
`raptor_like_study/cases/cold_n2_external_screen/results/wall_mesh_family_summary.json`.
LOX/CH4 remains blocked until a wall-resolved cold-N2 flow completes and
demonstrates the `y+` gate.
