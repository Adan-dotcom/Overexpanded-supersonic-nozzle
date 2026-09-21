# Provisional cold-N2 internal-domain screen

This case is a six-rank, axisymmetric viscous RANS software/physics screen on
the audited three-level mesh family. It uses ideal N2 with Eilmer's species
transport data, `k_log_omega`, a stagnation inlet and a fixed ambient-pressure
outlet. It does not include an external plume domain, so it cannot by itself
validate the DLR free-jet separation topology.

Every dimensional run requires an explicit numeric ambient pressure. The
preprocessor derives `P0=NPR*Pa` and accepts only the user-authorized provisional
values: T0 = 285/295/305 K; adiabatic or fixed wall at 280/300/320 K; inlet
turbulence intensity = 0.5/1/5%; length scale = 0.1/1/5 mm. Wall material,
thickness and CHT are absent. These values are assumed sensitivity inputs, not
recovered experimental conditions.

Run outside the repository as user `adan`:

```bash
bash raptor_like_study/cases/cold_n2_validation/flow_screen/run_screen.sh \
  /home/adan/eilmer-artifacts/RUN_NAME PA_PA NPR T0_K WALL TI LENGTH_M MESH SWEEP
```

For example, `WALL` must be exactly `adiabatic`, `280`, `300` or `320`; `MESH`
must be `coarse`, `medium` or `fine`. The runner has a hard 60-minute limit,
and `SWEEP` must be `startup` or `shutdown` so hysteretic targets are never
mixed. It writes VTK, wall pressure/shear/`y+`, provisional `x_sep`, shock
location and provenance outside Git, and never marks the result as validation
or training data. A run matrix is intentionally not inferred from the ranges:
the factorial/OFAT design and its reference NPR must be explicitly declared.
