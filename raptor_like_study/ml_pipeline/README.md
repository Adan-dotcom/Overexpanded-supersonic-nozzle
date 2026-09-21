# Sparse-sensor ML pipeline

Final training accepts only case rows with `physics_accepted=true`. The current
repository contains zero such rows, so the pipeline must fail closed.

Inputs are pressure values at fixed wall stations plus operating conditions.
All samples and noise realizations derived from one CFD case stay in one fold.
The current scope is one DLR-PAR contour; geometry is not an ML input.

Planned comparisons include uniform placement, greedy selection, POD-QR,
regularized linear models, tree ensembles and an MLP. Report classification
and separation-location errors with grouped nested validation and a locked
test set.

Generated mock datasets and previous provisional model results were removed.
