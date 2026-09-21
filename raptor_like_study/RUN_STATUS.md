# Run status

Updated: 2026-09-21 UTC

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
- Cold-N2 DLR-PAR validation: not yet reproduced with Eilmer.
- Hot DLR-PAR/methalox production: blocked.
- Final ML training: blocked.

## Immediate order

1. Verify the reconstructed contour against the published geometry.
2. Digitize and freeze the published cold-N2 boundary conditions and anchors.
3. Generate the three-level wall-resolved cold-N2 mesh family.
4. Reproduce published cold-N2 separation anchors.
5. Perform time-step, domain, turbulence and wall-model qualification.
6. Qualify hot chemistry and transport before any hot production case.

The benchmark evidence is in
`cases/products_air_benchmark/results/`. Heavy artifacts remain at
`/home/adan/eilmer-artifacts/products-air-benchmark-20260920-03` and are not
tracked by Git. This screen closes no production-physics gate other than the
preliminary products/air software and conservation blocker.

Geometry-screen evidence is in `cases/dlr_par_geometry/results/`.  Its heavy
artifacts remain at `/home/adan/eilmer-artifacts/dlr-par-geometry-20260921-02`.
It closes the geometry-port task only; it does not close experimental,
wall-resolution, turbulence or separation-validation gates.
