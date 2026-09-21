# Cold-N2 DLR-PAR validation inputs

This directory holds the source audit and frozen inputs for the experimental
validation lane.  It intentionally contains no flow case yet: the target DLR
campaign does not publish every absolute boundary condition needed to match
Reynolds number, and its plotted wall-pressure values have not yet been
digitized from a sufficiently resolved copy of the target article.

`SOURCE_AUDIT.md` records a critical source correction.  NASA report
20100017649 contains useful PAR data, but its article is not the DLR-PAR
hardware: it used a 38.1 mm throat, area ratio 30.5, a 40 degree initial angle,
heated dry air and a vacuum chamber.  Those curves must not be used as DLR
cold-N2 validation targets.

Run the scalar geometry comparison with:

```bash
python raptor_like_study/cases/cold_n2_validation/check_published_geometry.py \
  DLR_PAR_full_contour.csv \
  --output raptor_like_study/cases/cold_n2_validation/results/geometry_source_crosscheck.json
```

The comparison checks only the published scalar controls.  It cannot certify
the full reconstructed contour.

