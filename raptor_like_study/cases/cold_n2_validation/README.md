# Cold-N2 DLR-PAR validation inputs

This directory holds the source audit and frozen inputs for the experimental
validation lane.  It intentionally contains no flow case yet: the target DLR
campaign does not publish every absolute boundary condition needed to match
Reynolds number.

The user-supplied article PDF was verified by SHA-256 and its vector paths were
used to freeze 190 mean-pressure points from Figs. 3a and 11a, 31 oil-derived
physical-separation points from Fig. 7a, and 23 incipient-pressure points from
Fig. 7b.  The committed CSV files and full provenance are in `results/`.
Experimental uncertainty fields remain blank because the article does not
report the needed profile or oil-line uncertainty. A separately labeled
provisional digitization uncertainty of +/-0.055 rt is authorized for `x_sep`.

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

Regenerate the digitized targets from the exact supplied PDF with:

```bash
python raptor_like_study/cases/cold_n2_validation/digitize_primary_figures.py \
  /path/to/AIAA-JPPjl_2009.pdf \
  --output-dir raptor_like_study/cases/cold_n2_validation/results
```

The extractor refuses any PDF whose SHA-256 differs from the audited source.
Digitization uncertainty is kept separate from unavailable experimental
uncertainty.

`boundary_conditions.yaml` records the user-authorized provisional sensitivity
ranges. `mesh_family/` contains the executed three-level geometry screen, and
`flow_screen/` contains the guarded N2 case. Dimensional flow remains blocked
until numeric `Pa` and the factorial/OFAT design are explicitly declared.
