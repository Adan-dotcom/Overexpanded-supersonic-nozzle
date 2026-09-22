# Official Eilmer basis and cold-N2 external-screen decision

## Scope

This document is a numerical software/workflow screen only. It does not claim
DLR experimental validation, hot-gas validation, production readiness, or ML
label eligibility. Every audit records `physics_accepted=false` and
`training_eligible=false`.

The installed tree was pinned and checked without editing official sources:

| item | value |
|---|---|
| source | `/home/adan/gdtk` |
| install | `/home/adan/gdtkinst` |
| commit | `f53f4609a0331d48efee69a4e4f3c3598378cc03` |
| version | Eilmer 5.0.0, LDC 2.112, OpenMPI |

## Reproduction A

Commands were run in fresh copies with the source files unchanged:

```text
make prep
make run-transient       # nozzle-conical-back and Hakkinen
make run                 # underexpanded-jet
make post
make prep                # Mabey initialization only
```

The exact source-copy hashes and compact positivity audits are in
`raptor_like_study/cases/cold_n2_external_screen/results/official_basis/`.

| official example | expected/obtained result | evidence |
|---|---|---|
| `nozzle-conical-back` | normal `maximum-time`; step 5457, `t=0.00400073 s`; 3,300 cells; 64 VTK; all p/rho/T finite positive | `nozzle_conical_back.json` |
| `underexpanded-jet` | normal `maximum-time`; step 40091, `t=0.005 s`; 126,960 cells; 3,334 VTK; all p/rho/T finite positive | `underexpanded_jet.json` |
| `flat-plate-hakkinen-swbli/transient.lua` | normal `maximum-time`; step 2514, `t=0.00087564 s`; 16,000 cells; 232 VTK; all p/rho/T finite positive | `flat_plate_hakkinen_swbli.json` |
| `flat-plate-turbulent-mabey/job.lua` initialization | preparation completed; `tke=76.2339615`, `log(omega)=15.033477894648`; no solver run requested | `flat_plate_turbulent_mabey_initialization.json` |

The first Mabey preparation reported missing `gpmetis`, exactly as the pinned
`src/grid_utils/ugrid_partition.d` check predicts. Ubuntu METIS 5.1.0 was
installed as an installation dependency; the official source and job file
were not modified. The second unmodified preparation completed and printed the
expected Mabey turbulence values. This was an installation diagnosis, not a
CFD-parameter adjustment.

## What was inherited and what differs

Inherited directly from official examples:

- axisymmetric structured-grid and ambient-plume topology from
  `examples/lmr/2D/underexpanded-jet/grid.lua`;
- `InOutFlowBC_Ambient` and `OutFlowBC_Simple` from its `transient.lua`;
- transient RK3/adaptive/viscous settings and no-slip wall forms from
  `flat-plate-hakkinen-swbli/transient.lua`;
- wall load output and `k_log_omega` initialization algebra from
  `flat-plate-turbulent-mabey/job.lua`;
- no Newton/JFNK in stages 1--3.

The new case differs only in the application geometry and screen inputs: the
audited DLR-PAR reconstructed contour is used for the internal nozzle, a
downstream exterior region is added, N2 is ideal, and the provisional
`Pa=100000 Pa`, `NPR`, `T0=295 K`, wall and turbulence inputs are generated with
`P0=NPR*Pa`. The nozzle lip is a grid connection, not a pressure boundary.

## Incremental evidence

Heavy artifacts are under
`/home/adan/eilmer-artifacts/cold-n2-external-screen-20260921/`; the repository
tracks only code, metadata and compact audits.

| stage | result |
|---|---|
| 1 inviscid | one initial run exposed a `tke` field with turbulence disabled; this was corrected in the case script. The one allowed retry used the official underexpanded-jet transient controls and completed at 1 ms with positive states, 111 VTK and 208 wall loads. |
| 2 laminar/no-slip | first fixed-temperature attempt stopped at 85.6 µs. The one official Hakkinen-based retry used adiabatic no-slip and completed at 1 ms with positive states, 111 VTK and 208 wall loads. |
| 3 `k_log_omega` | completed at 1 ms with positive states, 111 VTK and 208 wall loads. Mabey initialization remained finite. |
| 4 steady acceleration | not used to alter transient controls; the official `FlowSolution` restart pattern is documented for a later isolated qualification. |

Compact tracked stage evidence is in
`raptor_like_study/cases/cold_n2_external_screen/results/stage_summary.json`.

For all transient runs, a global mass/energy balance is explicitly marked
unavailable because the case is an open ambient transient and the current
audit does not close a control volume including storage, wall heat and viscous
work.

## Startup NPR sweep

The provisional baseline was `Pa=100000 Pa`, `NPR=35`, `T0=295 K`, wall
temperature 300 K, `Tu=1%`, `L=1 mm`, with `P0=NPR*Pa`. The same external
stage-3 setup was run for NPR 30, 33, 35, 37 and 40. Every case reached 1 ms
with `maximum-time`, finite positive pressure/density/temperature, VTK and
wall-load output. Compact evidence is in
`raptor_like_study/cases/cold_n2_external_screen/results/startup_summary.json`.

| NPR | final step | final time (s) | x_sep (m) | y+ max | state/VTK/loads |
|---:|---:|---:|---:|---:|---|
| 30 | 4330 | 0.00100009 | 0.125020 | 6903.8 | pass/pass/pass |
| 33 | 4179 | 0.00100004 | 0.125020 | 7513.2 | pass/pass/pass |
| 35 | 4100 | 0.00100010 | 0.125020 | 7183.1 | pass/pass/pass |
| 37 | 4037 | 0.00100001 | 0.125020 | 7932.5 | pass/pass/pass |
| 40 | 3962 | 0.00100008 | 0.081580 | 8595.7 | pass/pass/pass |

The large `y+` values and the open-transient balance limitation are explicit
reasons this remains a numerical screen, not a wall-resolved validation. The
wall metric is provisional and must not be interpreted as an experimental
separation result.

## Decision

The startup NPR sweep is recorded below after all five cases finish. A GO here
authorizes only the next LOX/CH4 screen; it does not authorize production,
experimental claims or ML/DOE labeling.

**GO_FOR_LOX_SCREEN_ONLY**

This GO authorizes only preparation and screening of LOX/CH4 using the same
provisional numerical-audit gates. It does not authorize hot-flow production,
experimental validation claims, DOE for ML, or physics-accepted labels. The
internal cold-N2 case remains the separately preserved `NO_GO` documented in
`COLD_N2_SCREEN_DECISION.md`.

## Subsequent wall-resolution gate

The GO above is retained as the historical workflow-stability decision. A
later user-required wall-resolution gate now blocks LOX progression. Three
wall meshes pass geometry, but the explicit timestep is infeasible under the
60-minute limit. The former steady `SIGSEGV` was traced to incompatible
transient gradient settings and removed with Mabey's exact official WLSQ
configuration; the corrected screen converged normally with `lmrZ`. Direct
continuation to wall-coarse nevertheless failed after turbulence residual
growth drove CFL below the unchanged official minimum. A decade wall-spacing
bridge is in progress. Consequently `y+ <= 1` is not verified and the current
progression decision remains **NO_GO_WALL_RESOLUTION**. See
`WALL_MESH_AND_SEPARATION_STATUS.md`.
