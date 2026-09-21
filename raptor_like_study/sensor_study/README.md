# Sparse wall-sensor study

This folder contains input templates for estimating the minimum number and
placement of wall-pressure transducers needed to infer nozzle separation.

The full Eilmer field is a candidate reference only after it passes the gates
in `physics_model_status.yaml`. Sensor rows and noise realizations derived from
one CFD case must remain in the same ML fold.

Required researcher inputs are geometry, `Pc`, `Pa`, propellant O/F or cold-gas
state, wall thermal condition, sensor range/bandwidth/noise and the separation
definition. NPR and CEA chamber temperature are derived quantities.

No solver fields or generated sensor datasets belong in Git.
