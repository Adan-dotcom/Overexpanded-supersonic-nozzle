# DLR-PAR Eilmer separation and sparse-sensor study

The project studies how many wall-pressure sensors are needed to infer
shock-induced boundary-layer separation in an overexpanded nozzle. Eilmer 5
is the sole CFD backend; NASA CEA supplies chamber thermochemistry.

## Scientific scope

- Geometry: one fixed DLR-PAR contour, area ratio 30.
- Validation lane: published cold gaseous-nitrogen DLR-PAR data.
- Application lane: synthetic DLR-PAR geometry with public NASA LOX/LCH4
  operating conditions.
- Output: `x_sep`, shock location, reattachment and virtual wall transducers.
- ML truth: only CFD cases that pass all numerical and physical gates.

The hot application is not a reconstruction of Raptor or any proprietary
engine. Generalization is over operating conditions for one contour until
additional geometries are introduced.

## Active tools

- Eilmer `v5.0.0`: compressible CFD, MPI, gas models and chemistry.
- NASA CEA v3.3.4: equilibrium/frozen chamber and expansion reference states.
- Python: DOE, evidence gates, post-processing and ML.
- ParaView: interactive VTK inspection; Matplotlib: repeatable paper figures.

See `eilmer/README.md` for installation and commands. The bounded products/air
benchmark and the DLR-PAR geometry-only grid check described in `HANDOFF.md`
have passed their screens. The primary cold-N2 vector plots are now frozen as
CSV targets, but the matched CFD case still awaits numeric absolute run
conditions and the other inputs listed by the source audit in
`cases/cold_n2_validation/`. That audit also rejects a previously conflated
NASA/MSFC PAR campaign.

## Safety rule

`physics_model_status.yaml` currently reports zero accepted labels and blocks
hot production. Smoke and screening data are never training data.
