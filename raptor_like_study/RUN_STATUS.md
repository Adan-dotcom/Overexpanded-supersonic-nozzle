# DLR-PAR LOX/CH4 sensor-study status

## 2026-09-20 physics correction (supersedes the model recommendations below)

The chronology below is retained to show what was tested, but its former
"surviving" hot-plume branch is no longer an eligible physical model.

- The hybrid LUT exterior was not air or pure CO2. It was cold equilibrium
  methalox products because one `DATADRIVEN_FLUID` table occupied the complete
  zone. Those results are software-feasibility artifacts only.
- The 36 x 72 GRI-Mech LUT is rejected: some evaluated states were outside the
  declared thermodynamic-polynomial range. Do not use it for new runs.
- The replacement NASA-polynomial LUT has 72 x 192 nodes and passed a
  2,000-point interpolation audit: maximum errors are 0.257% in temperature,
  0.212% in pressure and 0.198% in equilibrium sound-speed squared. It remains
  a single-composition candidate and is not production-ready.
- The former `Tmax < T0` thermal gate was overgeneralized. For reacting gas,
  qualify energy using global total-energy flux and consistently referenced
  total enthalpy, not static temperature alone. Historical constant-gamma
  diagnostics remain relevant only to the rejected effective-gas surrogate.
- SU2 8.5 does not supply the required combination of compressible RANS,
  composition-coupled products/air mixing and hot methalox chemistry in the
  paths exercised here. Full hot-plume production is blocked pending a
  validated solver/model choice.
- There are still zero physics-accepted labels. Long hot runs are paused. The
  next defensible CFD work is published cold-N2 DLR-PAR validation and cheap
  single-composition thermochemistry screens, never final labels.

Machine-readable status: `physics_model_status.yaml`. Gate implementation:
`scripts/evaluate_physics_gate.py`. Preflight:
`scripts/check_model_readiness.py`.

## 2026-09-20 Eilmer 5 installation and solver selection

Eilmer `v5.0.0` was built from official source at commit
`f53f4609a0331d48efee69a4e4f3c3598378cc03` under WSL2. The optimized build
includes OpenMPI, multiespecies, multitemperature and turbulence support.
Official convex-corner tests passed in serial and two-rank MPI modes and wrote
VTK. A real-number transient underexpanded-jet smoke test also ran with six MPI
ranks over 32 blocks. Exact paths and results are in
`eilmer/installation_report.json`.

Eilmer is now the candidate hot products/air solver; SU2 remains the cold-N2
validation and cross-solver lane. No hot case is production-ready merely from
this install. The active blockers are recorded in `physics_model_status.yaml`.

## What is validated

- NASA CEA nominal state: `sensor_study/nominal_cea/nominal_summary.json`.
- Frozen effective-gas baseline for SU2: gamma `1.1982940938`, R `390.599754679 J/(kg K)`.
- Hybrid nozzle/ambient mesh generator: `ambient_mesh/generate_hybrid_mesh.py`.
- Pilot hybrid mesh: `ambient_mesh/hybrid_pilot/dlr_par_hybrid.su2`.
- Medium hybrid mesh: `ambient_mesh/hybrid_medium/dlr_par_hybrid.su2`.
- MPI execution with four ranks on both hybrid meshes and production timing with six ranks.
- NPR 20 seed, steady startup, BDF1 bootstrap, BDF2 temporal marching, and MUSCL calibration.

## Hybrid meshes

| Mesh | Cells | Nozzle block | First wall cell | Gmsh min scaled Jacobian | SU2 min orthogonality |
|---|---:|---:|---:|---:|---:|
| Pilot | 311,958 | 800 x 128 quads | 1.0 um | 0.9906 | 45.83 deg |
| Medium | 1,645,044 | 1600 x 200 quads | 0.5 um | 0.9938 | 35.78 deg |

The ambient boundary is 10 exit diameters downstream and 5 exit diameters radially. The nozzle is a transfinite quadrilateral block. The downstream ambient/plume region is conformal and triangular. The outlet pressure is no longer imposed directly at the nozzle lip.

## NPR 20 checkpoint

Inputs: Pc `5.2 MPa`, T0 `3485.33 K`, p_ambient `260 kPa`, NPR `20`.

The ideal seed exit is Mach `4.0305` and `15.76 kPa`. The pilot run used 500 startup iterations followed by 1000 conservative relaxation iterations.

Current diagnostics:

- Steady RANS did not converge: final `rms[Rho] = 10^-2.08`.
- Wall pressure rise remains at the exit (`x = 125.02 mm`).
- Minimum wall shear is locally negative (`-155 Pa`) but is not negative for the required 1 mm persistence.
- No separation location is accepted.
- `y+` median `0.141`, 95th percentile `0.628`, maximum `0.971`.
- Maximum temperature remains nonphysical for this effective adiabatic model (`5281 K > T0`).

Therefore this checkpoint is for initialization only. It must not be added to the ML label table.

## URANS calibration and current transient

The original `npr20_urans_smoke.cfg` verified file/restart mechanics but its 20 inner
iterations were insufficient. The calibrated sequence is:

1. `npr20_bdf1_warmup.cfg`: two BDF1 steps to create consecutive time levels.
2. `npr20_bdf2_bootstrap.cfg`: five BDF2 steps at first order in space.
3. `npr20_bdf2_muscl_cal_k001.cfg`: second-order MUSCL calibration.
4. `npr20_bdf2_production_segment.cfg` and continuations: transient marching.

The current robust numerical settings are BDF2, `dt = 0.25 us`, HLLC, MUSCL flow
reconstruction, Venkatakrishnan-Wang coefficient `0.005`, fixed pseudo-CFL `0.5`,
and 100 inner iterations. Six MPI ranks were about 12 percent faster than four for
the one-step pilot test.

The pilot has reached physical iteration 100 (`25 us`). This is only about
`0.2-0.3` nozzle acoustic/convective times, so it is not temporally converged.
The provisional features continue to move upstream:

| Iteration | Time [us] | Shock rise x [mm] | Separation x [mm] | Reattachment x [mm] |
|---:|---:|---:|---:|---:|
| 28 | 7.0 | 123.456 | 123.264 | 124.587 |
| 50 | 12.5 | 122.869 | 122.667 | 124.583 |
| 80 | 20.0 | 120.525 | 120.141 | not robustly detected |
| 100 | 25.0 | 119.353 | 118.996 | 124.583 |

At iteration 100, `y+` median is `0.071`, the 95th percentile is `0.650`, and
the maximum is `1.750`. The maximum volume temperature is still nonphysical for
this adiabatic effective-gas model: `5364 K > T0`. Consequently
`label_accepted=false` remains mandatory.

Plots and machine-readable results:

- `sensor_study/npr20_hybrid_pilot/transient_progress.png`
- `sensor_study/npr20_hybrid_pilot/flow_fields_production_t100.png`
- `sensor_study/npr20_hybrid_pilot/transient_feature_progress.csv`
- `sensor_study/npr20_hybrid_pilot/production_inner_residual_drops.csv`
- `sensor_study/npr20_hybrid_pilot/inner_convergence_calibration.png`

## Fine-grid, small-time-step check (completed to step 200)

The 1,645,044-cell mesh was initialized from pilot step 100 and marched with
`dt = 0.00625 us` from steps 101 through 200. Two BDF1 transfer steps were
followed by BDF2. An inner-iteration calibration at step 103 showed that 10
inner iterations changed `x_sep` by only `2.34 um` relative to 100 inner
iterations while reducing the density residual by about 2.85 decades. The
production continuation therefore used 10 inner iterations, fixed pseudo-CFL
`0.5`, HLLC, MUSCL, Venkatakrishnan-Wang `K=0.005`, SST, and four MPI ranks.

| Fine step | Added time after pilot t100 [us] | Shock rise x [mm] | Separation x [mm] | Reattachment x [mm] |
|---:|---:|---:|---:|---:|
| 120 | 0.1250 | 119.255 | 118.9719 | 124.5708 |
| 140 | 0.2500 | 119.255 | 118.9694 | 124.5614 |
| 160 | 0.3750 | 119.255 | 118.9672 | 124.5494 |
| 180 | 0.5000 | 119.255 | 118.9652 | 124.5378 |
| 200 | 0.6250 | 119.158 | 118.9634 | 124.5274 |

The separation point drifted only `8.48 um` from fine steps 120 to 200. It is
`32.30 um` upstream of the pilot step-100 result, less than one fine streamwise
wall spacing and only `0.026%` of nozzle divergent length. This is strong
evidence that the separation *location* is not a gross pilot-grid artifact.
It is not yet a formal three-grid GCI result, and the fine run covers only
`0.625 us`, so it does not establish statistical stationarity.

Fine-step-200 wall resolution is excellent for wall-resolved SST:
`y+95 = 0.349`, `y+max = 0.872`. However, the fine mesh resolves a sharper and
higher wall-pressure peak, and the maximum volume temperature is still
nonphysical (`5279 K > T0`). SU2 also reported 9 nonphysical reconstructed
states at finalization. Thus profile amplitudes and thermal boundedness are not
grid independent, and `label_accepted=false` remains mandatory.

Fine-grid outputs:

- `sensor_study/npr20_hybrid_fine/fine_grid_comparison.png`
- `sensor_study/npr20_hybrid_fine/fine_grid_comparison.json`
- `sensor_study/npr20_hybrid_fine/flow_fields_fine_t200.png`
- `sensor_study/npr20_hybrid_fine/diagnostics_fine_t200.json`
- `sensor_study/npr20_hybrid_fine/npr20_fine_bdf2_140_to200_i10.cfg`

## Limiter and pseudo-CFL cascade (steps 201-250)

Three controlled branches were started from the same fine-grid step-200
checkpoint. Each branch advanced 50 steps, or `0.3125 us`. In the accumulated
simulation clock this corresponds to approximately `25.625-25.9375 us`; 200 and
250 are iteration numbers, not microseconds.

| Branch | Limiter | Pseudo-CFL | Inner iter. | Tmax [K] | x_sep [mm] | Runtime [s] |
|---|---|---:|---:|---:|---:|---:|
| Baseline step 200 | Venkat-Wang K=0.005 | 0.5 | 10 | 5279.486 | 118.96342 | - |
| A step 250 | Venkat-Wang K=0.001 | 0.5 | 10 | 5125.868 | 118.94063 | 1350.46 |
| B step 250 | Barth-Jespersen | 0.5 | 10 | 5124.816 | 118.94093 | 1352.56 |
| C step 250 | Venkat-Wang K=0.001 | 0.25 | 30 | 5125.821 | 118.92598 | 3511.84 |

All three runs exited successfully and A/B/C produced no final warning about
nonphysical reconstructed states. Nevertheless, every branch retains a maximum
static temperature about `1640 K` above `T0=3485.33 K`. A and B are effectively
identical: `1.05 K` difference in Tmax and `0.30 um` in x_sep. C improves the
inner density residual from about `10^-4.964` to `10^-5.045`, but costs 2.6 times
as much as A and does not reduce Tmax. Its x_sep differs from A by only `14.65 um`.

Therefore the thermal overshoot is not controlled by these limiter or
pseudo-time settings. The separation location remains insensitive at the scale
of one fine wall cell, but no branch passes the thermal acceptance gate and
`label_accepted=false` remains mandatory.

An energy-field diagnostic on branch C confirms that this is not merely a
static-temperature plotting artifact. The maximum static temperature is
`5125.821 K` at `(x,r)=(132.508,33.983) mm`, with local Mach `0.699` and local
total temperature `5373.888 K`. The maximum computed local total temperature is
`5492.122 K`. Inside the nozzle (`x <= 125.02 mm`), the maximum static and total
temperatures are `4535.911 K` and `4662.358 K`, located on the axis near
`x=123.4 mm`. A calorically-perfect normal shock at the seeded exit Mach
`4.0305` should produce approximately `3439 K`, not `4500-5500 K`.

The branch-A Tmax trend is monotonic (`5239, 5201, 5173, 5148, 5126 K` at steps
210-250). Since A, B, and C agree at the same physical time, most of the drop
from the step-200 baseline is transient evolution rather than a limiter benefit.
The two leading numerical hypotheses are therefore an underdeveloped initial
plume transient and a multidimensional strong-shock anomaly of the HLLC flux.
The next discriminating flux tests should use SU2's `SLAU2` and
`AUSMPLUSUP2`, which were designed for improved strong-shock stability, while
retaining the common step-200 checkpoint and the branch-A settings.

Cascade outputs:

- `sensor_study/npr20_hybrid_fine/limiter_cascade_comparison.png`
- `sensor_study/npr20_hybrid_fine/limiter_cascade_comparison.json`
- `sensor_study/npr20_hybrid_fine/flow_fields_fine_A_t250.png`
- `sensor_study/npr20_hybrid_fine/flow_fields_fine_B_t250.png`
- `sensor_study/npr20_hybrid_fine/flow_fields_fine_C_t250.png`
- `sensor_study/npr20_hybrid_fine/npr20_fine_A_k0001_201_to250.cfg`
- `sensor_study/npr20_hybrid_fine/npr20_fine_B_barth_201_to250.cfg`
- `sensor_study/npr20_hybrid_fine/npr20_fine_C_k0001_cfl025_i30_201_to250.cfg`
- `sensor_study/npr20_hybrid_fine/temperature_overshoot_C_t250.json`
- `sensor_study/npr20_hybrid_fine/diagnose_temperature_overshoot.py`

## Acceptance gate for an ML label

1. Use second-order spatial reconstruction after the first-order startup is stable.
2. Reduce inner residuals by at least 2-3 decades per physical step or demonstrate time-step independence of wall pressure and wall shear.
3. Demonstrate global total-energy conservation and audit local total enthalpy
   with consistent chemical reference states; do not use `Tmax < T0` as a
   universal reacting-flow criterion.
4. Sample long enough to discard the transient and cover multiple shock/boundary-layer cycles.
5. Define separation as the first downstream crossing where signed wall shear stays negative for at least 1 mm.
6. Report mean, standard deviation, and distribution of `x_sep(t)` for unsteady cases.
7. Repeat on the medium mesh and require the mean separation location to be grid independent within the declared tolerance.
8. Keep `label_accepted=false` until every applicable condition passes.

## Reproduction

From `raptor_like_study` in PowerShell:

```powershell
.\.venv\Scripts\python.exe ambient_mesh\generate_hybrid_mesh.py --profile pilot
.\.venv\Scripts\python.exe ambient_mesh\generate_hybrid_mesh.py --profile medium
python sensor_study\npr20_hybrid_pilot\generate_seed.py
```

Run the startup from WSL:

```bash
cd '/mnt/d/PRUEBA SU2_2026/raptor_like_study/sensor_study/npr20_hybrid_pilot'
export OMPI_MCA_osc=pt2pt
mpirun --allow-run-as-root -np 4 /mnt/d/SU2/v8.5.0/bin/SU2_CFD npr20_startup.cfg
```

The current wall plot is
`sensor_study/npr20_hybrid_pilot/wall_diagnostics_production_t100.png`.

## Modeling limitation still open

The present pilot uses one frozen effective ideal gas for both combustion products and the external ambient. It is suitable for numerical workflow development, not the final chemistry claim. The paper model must explicitly justify this approximation or move to a species-capable products/air formulation and validate it against CEA-derived states and experimental data.

## Final numerical campaign (SLAU2, completed)

The strong-shock flux screen used a common BDF1 checkpoint and matched physical
time. HLLC and SLAU2 produced effectively the same first separation location;
AUSMPLUSUP2 lost inner convergence. SLAU2 was retained because it matched the
label while avoiding HLLC's documented strong-shock anomaly risk. The physical
time-step screen at `6.25`, `12.5`, and `25 ns` supported `25 ns` on the pilot
mesh over the short matched interval. Later tests at `50` and `100 ns` shifted
the rapidly moving separation point by `0.392` and `0.794 mm`, so production
retained `25 ns`.

The dual-time calibration showed that the old `CFL=0.5`, 10-inner-iteration
setup biased the transient separation label. The selected pilot settings were
SLAU2, MUSCL, Venkatakrishnan-Wang `K=0.001`, pseudo-CFL `2.0`, 30 inner
iterations, and six MPI ranks. Twelve MPI ranks on the 6-core/12-thread Ryzen
were 14.5 percent slower than six.

The pilot was marched from `25 us` to `162.825 us` (`5613` physical steps in
the accumulated indexing). An axis integration gave a nozzle convective time
of `42.842 us`. The initially reported separation near `119 mm` was a startup
transient: it migrated upstream for more than three convective times before
forming a plateau.

| Quantity | Pilot final | Fine final |
|---|---:|---:|
| First persistent separation x | `35.80185 mm` | `35.80876 mm` |
| Pilot/fine difference | - | `0.00691 mm` |
| Final-window x-separation range/drift | `0.01934 mm` | `0.01050 mm` |
| y+ median | `0.137` | `0.069` |
| y+ 95th percentile | `0.604` | `0.301` |
| y+ maximum | `1.127` | `0.712` |

The fine mesh contains `1,645,044` cells. It was initialized from pilot step
5613 with two BDF1 steps and advanced 50 BDF2 steps at `6.25 ns`, SLAU2,
pseudo-CFL `2.0`, and 30 inner iterations. The separation label passes the
temporal, grid-difference, and wall-resolution gates. Therefore
`separation_label_numerically_accepted=true` for this effective-gas case.

The thermal gate still fails. Fine-grid maximum local total temperature is
`4005.886 K`, or `14.94%` above the prescribed inlet `T0=3485.33 K`. The pilot
and fine values agree, so this is not removed by mesh refinement. Consequently
`paper_physics_accepted=false`: the result may be used to validate the workflow
and sensor-label extractor, but not yet as a production LOX/CH4 paper datum.

Final artifacts:

- `sensor_study/npr20_hybrid_fine/final_validation_summary.json`
- `sensor_study/npr20_hybrid_fine/final_validation_summary.png`
- `sensor_study/npr20_hybrid_pilot/relaxation_feature_history.csv`
- `sensor_study/npr20_hybrid_pilot/relaxation_feature_history.png`
- `sensor_study/npr20_hybrid_pilot/numerics_campaign_summary.json`
- `sensor_study/npr20_hybrid_pilot/numerics_campaign_comparison.png`

## Equilibrium-products LUT integration (completed prototype)

The official SU2 8.5.0 `DATADRIVEN_FLUID`/`LUT` path was exercised with a
custom Dragon table for gaseous equilibrium LOX/CH4 products at `O/F=3.2`.
The table was generated with Cantera 3.2/GRI-Mech 3.0 on a rectangular
`36 x 72` density/internal-energy grid (`2592` nodes), as required by SU2's
data-driven fluid initialization. It contains `Density`, `Energy`, entropy,
and the five first/second entropy derivatives expected by SU2.

An independent 200-point off-node validation produced:

| Quantity | Median absolute error | p95 | Maximum |
|---|---:|---:|---:|
| Temperature | `0.019%` | `0.305%` | `3.565%` |
| Pressure | `0.467%` | `0.710%` | `3.079%` |

All interpolated sound-speed squares were positive. The maximum errors occur
near low-temperature/low-pressure edges; 96 validation points exceeded 3500 K,
outside the nominal range of at least some GRI-Mech species polynomials. The
table is therefore an integration prototype pending a state-grid comparison
against NASA CEA and transport-property validation.

SU2 loaded the fine table and completed two RANS-SST/HLLC iterations on six MPI
ranks. SU2 explicitly disallows SLAU2 and a `FARFIELD` boundary for non-ideal
compressible fluids; HLLC plus Riemann inlet/outlet is required here. A new
internal structured pilot mesh was generated with `102400` quadrilaterals,
`1 um` first wall cell, and minimum scaled Jacobian `0.9906`. Its separate
smoke test also ended with `Exit Success` on six MPI ranks.

The corresponding internal medium and fine meshes are also generated. They
contain `320000` and `1024000` quadrilaterals, use `0.5 um` and `0.25 um` first
wall cells, and have minimum scaled Jacobians `0.9938` and `0.9951`. They have
not been advanced in CFD yet; generating a mesh is not evidence of flow-field
convergence.

Artifacts:

- `thermochemistry/LUT_lox_ch4_equilibrium.drg`
- `thermochemistry/LUT_lox_ch4_equilibrium.metadata.json`
- `thermochemistry/LUT_lox_ch4_equilibrium.validation.json`
- `thermochemistry/LUT_lox_ch4_equilibrium.validation.png`
- `thermochemistry/datadriven_lut_smoke.log`
- `internal_mesh/pilot/dlr_par_internal.su2`
- `internal_mesh/pilot/mesh_summary.json`
- `sensor_study/npr20_internal_lut_pilot/internal_lut_smoke.log`

This does not change the existing paper gate. The effective-ideal-gas separation
label remains numerically accepted but not physically accepted. LUT smoke-test
outputs are not training data. A production LUT run must start from a compatible
LUT state, establish temporal stationarity, repeat the mesh/time-step gates, and
validate equilibrium/frozen and transport-model sensitivity.

## Corrected physical DOE and rapid model screen

The previous independent sampling of chamber pressure and NPR was retired for
the hot-fire campaign. `Pc=5.2 MPa, NPR=20` implies `Pa=260 kPa`, so that point
is retained only as a pressurized-chamber numerical test. The corrected DOE has
24 nominal cases at `Pc=5.1-5.4 MPa`, `Pa=50-101.325 kPa`, and O/F `3.1-3.3`,
plus 24 explicitly exploratory one-atmosphere throttle cases at
`Pc=2.0-5.4 MPa`. NPR is derived. NASA CEA completed all 48 cases and predicted
`T0=3365.9-3501.7 K`.

Five 76,800-cell internal screens exercised ideal/LUT, SST/SA, and HLLC/SLAU2.
All remained finite, but none passed the physics gate. After 400 or 1,600
iterations they reduced density residuals by only `0.29-0.56` decades, and the
continued cases had `9.4-12.8%` mass imbalance. Their exit pressure remained
about `18-21 kPa` instead of the requested `260 kPa`; the quasi-1D supersonic
branch therefore did not establish the backpressure shock and cannot rank
separation behavior.

A nozzle-plus-plume feasibility run replaced the unsupported LUT farfield with
a Riemann pressure boundary. A seed-classification bug was found: a `0.1 nm`
wall tolerance classified alternating wall nodes as ambient because mesh/spline
differences reach about `5 nm`. The tolerance is now `0.1 um`, below the `1 um`
first wall cell, and both the LUT and legacy ideal seed generators are fixed.
The corrected LUT hybrid run completed 105 MPI iterations with finite positive
states, `Tmax=3503.614 K`, and zero LUT extrapolation points. It has not
converged, has no persistent separation yet, and uses cold combustion products
instead of real exterior air; `physics_accepted=false` and
`training_eligible=false` remain mandatory.

The ML registry now contains the 48 corrected cases as planned work. Final
dataset construction strictly requires `physics_accepted=true`; its verified
current behavior is to stop with zero eligible profiles. Mock-data model plots
remain software-development artifacts and are not publishable results.

The corrected open-atmosphere screen was also run at `Pc=5.2 MPa` and
`Pa=101.325 kPa` (`NPR=51.32`). The five-iteration startup and 100-iteration
continuation completed cleanly; a CFL-adaptive continuation diverged at its
64th iteration, while a fixed-`CFL=0.02` continuation completed 400 more.
After 505 accumulated pseudo-iterations the field remained finite and inside
the LUT with `Tmax=3548.751 K`, `y+ p95=2.981`, and no persistent negative-Cf
run. Its density residual ended at `10^-1.943` and was not monotonically
converging. This is the surviving software-feasibility branch, not a separation
label. The next physical stage must use URANS and run for multiple convective
times; more steady pseudo-iterations are not accepted as a substitute.

A 10-step first-order URANS smoke test then started successfully from the
fixed-CFL checkpoint at `dt=25 ns` with 30 inner iterations. It reached
`0.25 us`, exited successfully on six MPI ranks, kept all density/pressure/
temperature values positive, and used zero LUT extrapolation points. The last
inner density residual was about `10^-2.75`; `Tmax=3555.135 K`, `y+ p95=2.847`,
and no persistent negative-Cf run was present. This proves dual-time software
operation only. It is far shorter than one nozzle convective time and remains
`physics_accepted=false`, `training_eligible=false`.

## Assumption audit and rapid-screening mesh

`ASSUMPTIONS_AND_EVIDENCE.md` now records which quantities are measured,
published, user-supplied, derived, or purely synthetic. The largest scope issue
is explicit: DLR-PAR geometry plus NASA methalox conditions is a synthetic
combination, and one contour cannot support a claim of generalization to
arbitrary geometry. `LITERATURE_REVIEW.md` records the directly relevant
DLR-PAR, turbulence, chemistry, sensor, and NASA LLAMA sources.

A `600 x 128` internal screening mesh with `76800` quadrilaterals was generated.
It preserves the wall-normal layer count of the stable pilot while reducing
axial resolution and removing the ambient domain. Attempts at `400 x 64` and
`400 x 96` failed during the impulsive cold-to-hot start and were rejected.
The `600 x 128` mesh also fails after roughly 10 steady iterations when started
uniformly at 300 K and exposed immediately to the full `5.2 MPa, 3485 K` inlet.
Ideal/LUT and SST/SA variants fail in the same startup, so this is not valid
model-ranking evidence. The next screening runs require a quasi-1D compatible
seed or a staged pressure/temperature ramp. No screening run is an ML label.
