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

The final wall-coarse mesh was then run from the saved 1 ms external solution
with the official Mabey `k_log_omega` steady Newton/Krylov configuration. All
six ranks received `SIGSEGV` during the first Jacobian evaluation in
`gradients_leastsq`; no Newton step completed. No solver knob, ILU setting,
limiter or boundary was adjusted after this repeated failure. Medium and fine
flow runs were gated off.

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

Reauditing the old 1 ms NPR=35 screen changes its result from a false lip
separation to `x_sep=null`; the independently measured provisional shock is
`x_shock=0.10808978 m`. Its nozzle maximum remains `y+=7183.1`, so neither
number is a paper-ready separation result.

Compact evidence is in
`raptor_like_study/cases/cold_n2_external_screen/results/wall_mesh_family_summary.json`.
LOX/CH4 remains blocked until a wall-resolved cold-N2 flow completes and
demonstrates the `y+` gate.
