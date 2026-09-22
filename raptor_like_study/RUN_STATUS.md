# Run status

Updated: 2026-09-22 UTC

## Solver

Eilmer `v5.0.0`, commit
`f53f4609a0331d48efee69a4e4f3c3598378cc03`, is installed and verified in
WSL2. The optimized build includes OpenMPI, multiespecies, multitemperature and
turbulence capabilities.

Installation checks completed:

| Test | Ranks | Result |
|---|---:|---|
| Official convex corner, shared | 1 | converged, VTK written |
| Official convex corner, MPI JFNK | 2 | converged, VTK written |
| Official underexpanded jet, real transient | 6 | normal stop, VTK written |
| Products/air benchmark v1 | 6 | screen passed, VTK written |

Exact provenance is in `eilmer/installation_report.json`.

## Repository cleanup

The former solver campaigns and their generated meshes, restarts, VTK, logs,
plots, LUTs and provisional results were removed. Their results are not part of
the new evidence chain. NASA CEA data, the DLR-PAR contour, DOE, literature,
sensor definitions, ML gates and Eilmer installation files were retained.

## Physics readiness

- Physics-accepted labels: **0**.
- Products/air benchmark: **screen passed**; 36,000 cells, six ranks, 18.0 min
  solver time, mass imbalance 0.0410%, total-energy imbalance 0.0127%.
- DLR-PAR geometry: **geometry screen passed**; 385-point contour translated
  to metres and 92,160 positive-area cells generated in six conformal blocks.
  This is an inspection grid, not a wall-resolved validation mesh.
- DLR source audit: the contour matches the published throat, area ratio and
  rounded 34/10 degree wall-angle controls.  NASA report 20100017649 was
  rejected as a DLR anchor because it used different hardware, gas and test
  environment. The supplied primary PDF passed its SHA-256 check; 190 mean
  wall-pressure points plus Fig. 7 physical-separation and incipient-pressure
  curves were extracted directly from vector paths and frozen in the repo.
  Numeric ambient pressure and matched run conditions remain missing. The user
  authorized provisional assumed T0, wall and inlet-turbulence ranges plus a
  digitization uncertainty of +/-0.055 rt for `x_sep`; this is not an
  experimental uncertainty.
- Cold-N2 mesh family: **geometry gates passed** at 51,840, 103,680 and
  207,360 cells in six conformal blocks. Flow-based `y+`, separation resolution
  and convergence remain unqualified.
- Cold-N2 internal-domain numerical screen: **NO_GO**. The NPR=35 coarse baseline crashed at
  Newton step 1 in `decompILU0` with a floating-point divide-by-zero. The one
  permitted retry (ILU fill 1, diagonal perturbation, scaling and disabled
  extrema clipping) reproduced the identical failure. No completed iteration,
  VTK, wall profile, state audit, `x_sep`, shock, `y+`, or conservation result
  exists. Medium, NPR sweep, OFAT and LOX screens were gated off.
- Cold-N2 DLR-PAR validation: not yet reproduced with Eilmer.
- Hot DLR-PAR/methalox production: blocked.
- Final ML training: blocked.

## Official-basis external screen (new separate lane)

The four requested official examples were reproduced from the installed
`f53f4609a0331d48efee69a4e4f3c3598378cc03` tree. METIS 5.1.0 was added as the
missing installation dependency required by the official `ugrid_partition`
check; no official source or CFD control was edited. Compact positivity/VTK
audits are under
`cases/cold_n2_external_screen/results/official_basis/`.

The new `cold_n2_external_screen` uses an underexpanded-jet-derived exterior
axisymmetric plume and completed its inviscid, laminar/no-slip, and
`k_log_omega` transient stages. Startup NPR 30/33/35/37/40 all reached 1 ms
normally with positive finite states, VTK and wall loads. The screen decision
is **GO_FOR_LOX_SCREEN_ONLY**; this is not a production or validation gate.
The external screen's large y+ and unavailable open-transient global balance
remain explicit limitations.

The subsequent wall-resolution qualification supersedes permission to launch
LOX immediately. Three external meshes pass geometry at 61,440, 72,960 and
84,480 cells. The steady `SIGSEGV` was traced to mixing transient derivative
settings with Newton's WLSQ Jacobian and was corrected with the exact official
Mabey gradient configuration. The official `lmrZ` path then converged the
screen continuation in 1,421 steps to residual `9.23e-11`, with positive
states, VTK and loads. Its `y+` is still 6,811.9.

Direct continuation to wall-coarse failed at step 56 after turbulence
residual growth and repeated rejected steps drove CFL below the unchanged
official minimum. A decade-by-decade, coarse-to-fine bridge queue is now
running without a wall-time limit. No wall-mesh `y+` exists yet; medium/fine
and LOX remain gated off.

## Immediate order

1. Complete the decade wall-spacing continuation ladder without changing
   numerical controls.
2. Require wall-coarse normal convergence plus state, VTK, load and `y+`
   audits before launching medium and fine.
3. Quantify mesh dependence only after all three wall meshes pass.
4. Keep LOX/CH4 screening disabled until a wall-resolved cold-N2 flow proves
   `y+ <= 1` and the robust separation detector can be evaluated.
5. Reproduce the frozen experimental anchors before any physics acceptance.

The benchmark evidence is in
`cases/products_air_benchmark/results/`. Heavy artifacts remain at
`/home/adan/eilmer-artifacts/products-air-benchmark-20260920-03` and are not
tracked by Git. This screen closes no production-physics gate other than the
preliminary products/air software and conservation blocker.

Geometry-screen evidence is in `cases/dlr_par_geometry/results/`.  Its heavy
artifacts remain at `/home/adan/eilmer-artifacts/dlr-par-geometry-20260921-02`.
It closes the geometry-port task only; it does not close experimental,
wall-resolution, turbulence or separation-validation gates.

The literature eligibility audit, frozen vector-derived targets and explicit
missing boundary conditions are in `cases/cold_n2_validation/`. No NASA/MSFC
pressure curve was relabeled as a DLR measurement. Digitization uncertainty is
reported separately from the unavailable experimental uncertainty.

Cold-N2 mesh-family evidence is in
`cases/cold_n2_validation/mesh_family/results/`. Heavy grids remain at
`/home/adan/eilmer-artifacts/dlr-par-cold-n2-mesh-family-20260921-01`.

The numerical-screen decision is in `COLD_N2_SCREEN_DECISION.md`; its compact
evidence is in `cases/cold_n2_validation/results/screen_campaign_summary.json`.
Heavy failure artifacts remain under
`/home/adan/eilmer-artifacts/cold-n2-screen-20260921`.
