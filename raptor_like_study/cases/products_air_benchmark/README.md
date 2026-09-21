# Products/air compressible-mixing benchmark

This is a **screening benchmark**, not a nozzle solution and not an ML label. It
is a planar, laminar, frozen-chemistry mixing layer designed to test Eilmer 5
multispecies transport, six-rank execution, state integrity and conservation
before a full DLR-PAR case is attempted.

## Evidence-backed inputs

- Solver/API: Eilmer `v5.0.0`, commit
  `f53f4609a0331d48efee69a4e4f3c3598378cc03`.
- Product source: retained NASA CEA files for
  `hot_methalox_nominal_022`, specifically
  `../cea/physical_doe_inputs/hot_methalox_nominal_022.inp`, its `.out`,
  `../cea/physical_cea_summary.csv` and `../cea/physical_products_long.csv`.
- That DOE row has `Pc=5.145685861 MPa`, `O/F=3.195137284`,
  `Pa=100.836186539 kPa`; the CEA exit has `T=1738.69 K`.
- Product species are the eight species whose maximum CEA mass fraction over
  chamber, throat or exit exceeds `1e-3` anywhere in the retained physical
  campaign: `H2O, CO2, CO, H2, OH, O2, O, H`. Their nominal-022 exit fractions
  sum to `0.9999992609` before normalization; the omitted trace fraction is
  `7.391e-7`.
- Air is `N2=0.767, O2=0.233` by mass, matching the pinned Eilmer examples.
- Thermodynamics are thermally perfect. Viscosity and conductivity come from
  the Eilmer species database with `prefer-grimech`; laminar species diffusion
  uses Fick's first law with Eilmer's binary diffusion coefficients.

The two streams use the DOE ambient static pressure and Mach 2. The equal
pressure is deliberate: it isolates compressible mixing and transport from the
pressure mismatch of the overexpanded nozzle. The product temperature remains
the CEA exit value; air is the explicitly documented 300 K benchmark reference
state. These are screening choices and must not be presented as a physical
DLR-PAR operating point.

## Discretization and gates

- Domain: `0.120 m x 0.040 m`, planar.
- Grid: `180 x 200 = 36,000` structured cells in six equal blocks.
- Parallelism: six MPI ranks, one block per rank.
- Boundaries: separate supersonic product/air inlets, simple outflow, slip top
  and bottom walls.
- Solver: viscous transient, adaptive Hanel/AUSMDV flux, RK3, CFL 0.5, 1.5
  air-stream flow-through times. The initial field already contains both
  correct streams; one transit removes downstream dependence on that field and
  the final 0.5 transit provides development margin. This duration was
  selected from measured six-rank cost to meet the 10--30 minute screen target.
- Required gates: successful exit, all finite positive `p/rho/T`, species sum
  error at most `1e-6`, relative mass imbalance at most `0.005`, relative total
  energy-flux imbalance at most `0.01`, evidence of actual products/air mixing,
  and inspectable VTK output.
- Runtime target: 10--30 minutes; the runner hard-stops the solver at 60 minutes.

The flux audit integrates `rho*u` and
`rho*u*(h + |V|^2/2)` over inlet and outlet faces. Enthalpy is evaluated with
the exact generated `gas-model.lua` used by Eilmer, preserving its species
reference energies. The report labels this as a convective boundary estimate;
the screen is failed if the stated tolerances are not met.

## Run

From the repository root in WSL, after loading the pinned Eilmer environment:

```bash
source raptor_like_study/eilmer/eilmer5-env.sh
bash raptor_like_study/cases/products_air_benchmark/run_benchmark.sh \
  "$HOME/eilmer-artifacts/products-air-$(date -u +%Y%m%dT%H%M%SZ)"
```

The destination must be outside the repository. Generated grids, `lmrsim`, VTK
and logs stay there. The runner performs the readiness check, gas/grid/simulation
preparation, six-rank solve, VTK export, audit and screen-gate evaluation.

The retained result summary, formal gate result, provenance and report are in
`results/`. Heavy solver and VTK artifacts are intentionally external.
