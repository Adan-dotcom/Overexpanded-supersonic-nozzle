# Products/air benchmark result

The `products_air_benchmark_v1` case passed every software and conservation
screen on 2026-09-20 local time. It remains a screening calculation, not a
nozzle result, a physics-accepted case or an ML label.

## Execution

- Eilmer commit: `f53f4609a0331d48efee69a4e4f3c3598378cc03`.
- Grid: 36,000 cells in six blocks.
- MPI map: six unique tasks, one block per task.
- Solver stop: normal `maximum-time` stop after 2,660 RK3 steps.
- Physical duration: 1.5 air-stream flow-through times.
- Solver wall time: 1,082 s (18.0 min); total recorded wall time: 1,152 s.
- Export: nine snapshots and 64 VTK/PVTU/PVD files.
- VTK inspection: MeshIO read a final block as 6,161 points and 6,000 quad
  cells with pressure, temperature, velocity and all nine mass fractions.
- Full external artifacts:
  `/home/adan/eilmer-artifacts/products-air-benchmark-20260920-03`.

## Audit

The final 36,000-cell snapshot contained no non-finite or non-positive
pressure, density or temperature values. Temperature ranged from 300.0 to
1,743.42 K. Species closure error was `6.66e-16`; the small minimum mass
fraction (`-4.73e-15`) is roundoff and is within the `1e-6` tolerance.

The inlet/outlet cell-centre convective audit gave a relative mass-flux
imbalance of `4.1028e-4` (0.0410%) and a relative total-energy-flux imbalance
of `1.26885e-4` (0.0127%). The latter uses
`rho*u*(h + |V|^2/2)` and enthalpy from the exact generated Eilmer gas model.
Both are below the screen limits of 0.5% and 1%, respectively.

The gas model was separately evaluated for both product and air compositions
at 30 combinations spanning 200--4,000 K and 10 kPa--5.2 MPa. Thermodynamics,
viscosity, thermal conductivity and all off-diagonal binary diffusion
coefficients were finite and positive. The final field stayed inside this
temperature range. Mixing was detected in 2,033 cells (5.647%).

The formal result is `screening_survivor=true`, while
`physics_accepted=false` and `training_eligible=false`. The calculation closes
only the preliminary products/air benchmark blocker.
