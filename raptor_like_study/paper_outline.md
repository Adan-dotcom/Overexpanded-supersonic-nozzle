# Proposed paper

## Working title

Validation-aware sparse pressure sensing of shock-induced boundary-layer
separation in an overexpanded rocket nozzle.

## Claims we may be able to support

- A reproducible public-parameter CFD workflow with explicit physics gates.
- Cold-N2 DLR-PAR validation of wall pressure and separation regimes.
- A synthetic LOX/CH4 products-air application after model qualification.
- Sparse wall-pressure layouts compared with non-neural and neural estimators.
- Uncertainty estimates and a locked test set grouped by complete CFD case.

## Claims we must not make without evidence

- Exact prediction of a current proprietary Raptor nozzle.
- Universal separation prediction from one turbulence model.
- Arbitrary-geometry generalization from the single DLR-PAR contour.
- Accuracy beyond the validation data and physics models.

## Required validation

- Mesh refinement.
- RANS versus URANS sensitivity.
- Equilibrium versus frozen chemistry sensitivity.
- Comparison with published experimental overexpanded-nozzle data.
- A locked test set grouped by complete CFD case, not snapshots or noise draws.

See `VALIDATION_AND_SENSOR_PLAN.md` for the validation matrix, sensor error
model and pre-registered selection rule.
