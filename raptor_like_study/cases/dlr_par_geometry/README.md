# DLR-PAR geometry and grid screen

This case ports the user-supplied `DLR_PAR_full_contour.csv` into an Eilmer 5
axisymmetric structured grid and applies geometry/topology quality checks.  It
does not define a gas, boundary conditions or a flow solution.

The contour remains a user reconstruction, not certified DLR CAD.  Passing
this screen means only that the reconstruction was translated without unit or
topology errors and that the inspection grid is usable as a starting point.
It does not establish wall resolution, `y+`, turbulence suitability or
agreement with the cold-N2 experiment.

The grid contains 92,160 cells in six equal blocks:

- convergent: 120 axial by 128 radial cells, one block;
- divergent: 600 axial by 128 radial cells, five blocks;
- axial clustering toward the throat (`beta=1.1`);
- radial clustering toward the wall (`beta=1.05`).

Run under WSL2 and keep generated grid files outside the repository:

```bash
bash raptor_like_study/cases/dlr_par_geometry/run_geometry_check.sh \
  /home/adan/eilmer-artifacts/dlr-par-geometry-YYYYMMDD-NN
```

The run writes a contour audit, Eilmer grid, mesh-quality JSON, plot and
provenance into that external directory.  Only the small audited evidence in
`results/` is tracked.

