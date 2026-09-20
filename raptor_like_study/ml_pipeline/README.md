# Sparse-sensor ML pipeline

This pipeline is developed in parallel with CFD, but final training accepts
only rows with `physics_accepted=true`. Screening, smoke, mock, and failed-gate
cases can exercise the software with `--allow-provisional`; their metrics are
always marked non-publishable.

The current model scope is one fixed DLR-PAR contour. Inputs are wall pressures
at a fixed subset of candidate stations plus operating conditions. Geometry is
not an input until multiple contours exist.

`sync_physical_registry.py` imports the corrected CEA DOE as planned cases.
`build_training_dataset.py` samples only eligible CFD wall profiles onto the
fixed candidate grid; without `--allow-provisional`, it accepts exclusively
`physics_accepted=true` rows and refuses to create an empty final dataset.

```powershell
cd 'D:\PRUEBA SU2_2026\raptor_like_study'
.\.venv\Scripts\python.exe ml_pipeline\make_mock_dataset.py
.\.venv\Scripts\python.exe ml_pipeline\train_sensor_models.py `
  ml_pipeline\mock_sensor_dataset.csv --allow-provisional
```

For every sensor budget the code compares uniform placement with POD-QR fitted
only on the training partition. It reports separation classification and
conditional `x_sep` regression. CFD-case rows, not noise realizations, are the
split unit.

The current trainer uses one grouped development holdout and always writes
`publishable=false`. A paper result still requires grouped nested validation,
hyperparameter selection inside the training folds, and a locked final test
set as declared in the physical experiment specification.
