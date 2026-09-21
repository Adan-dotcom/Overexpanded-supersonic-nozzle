# Run status

Updated: 2026-09-20

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

Exact provenance is in `eilmer/installation_report.json`.

## Repository cleanup

The former solver campaigns and their generated meshes, restarts, VTK, logs,
plots, LUTs and provisional results were removed. Their results are not part of
the new evidence chain. NASA CEA data, the DLR-PAR contour, DOE, literature,
sensor definitions, ML gates and Eilmer installation files were retained.

## Physics readiness

- Physics-accepted labels: **0**.
- Products/air benchmark: not yet implemented.
- Cold-N2 DLR-PAR validation: not yet reproduced with Eilmer.
- Hot DLR-PAR/methalox production: blocked.
- Final ML training: blocked.

## Immediate order

1. Implement the 20k-60k-cell Eilmer products/air benchmark.
2. Require six-rank runtime below 30 minutes, with a 60-minute hard stop.
3. Verify species, state positivity, mass and total-energy conservation.
4. Port the DLR-PAR geometry and perform a mesh-quality-only check.
5. Reproduce published cold-N2 separation anchors.
6. Qualify hot chemistry, transport, turbulence and wall models.
