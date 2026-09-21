# Cold-N2 mesh family

This is a three-level, six-block, axisymmetric structured-grid family for
screening the reconstructed DLR-PAR contour. The levels contain 51,840,
103,680 and 207,360 cells. All use the same topology and clustering functions.

The family is not called wall-resolved merely from geometric spacing. Its
first-cell heights are audited here; `y+` must be measured from a completed
viscous solution at the declared absolute pressure before qualification.

The 2026-09-21 geometry run passed all gates. The frozen lightweight summary
is in `results/mesh_family_summary.json`; heavy grids and plots remain under
`/home/adan/eilmer-artifacts/dlr-par-cold-n2-mesh-family-20260921-01`.
The runner uniformly resamples the source polyline at 0.05 mm for the Eilmer
path files because `Spline2` otherwise transfers the CSV's abrupt point-density
change into an artificial cell-area jump. The authoritative CSV is unchanged,
and the conditioning method and generated point counts are recorded by
`contour_audit.json` in each artifact directory.

Generate and audit all three levels outside the repository:

```bash
bash raptor_like_study/cases/cold_n2_validation/mesh_family/run_mesh_family.sh \
  /home/adan/eilmer-artifacts/dlr-par-cold-n2-mesh-family-YYYYMMDD-NN
```

This closes only the geometry-quality portion of the mesh-family task. The
family remains pending flow-based `y+`, separation-resolution and convergence
qualification.
