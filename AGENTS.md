# Agent instructions

Read `HANDOFF.md`, `raptor_like_study/RUN_STATUS.md`, and
`raptor_like_study/physics_model_status.yaml` before running CFD.

- Eilmer 5 is the only active CFD backend. Do not recreate retired solver cases.
- No current CFD case is a physics-accepted ML label.
- Run `raptor_like_study/scripts/check_model_readiness.py` before a campaign.
- Never turn an install test, smoke test, screen, or failed-gate run into data.
- Keep NPR derived from `Pc/Pa`; never sample all three independently.
- Preserve NASA CEA inputs and outputs as thermochemical evidence.
- Use six MPI ranks on this six-core Ryzen unless a benchmark says otherwise.
- Do not commit `lmrsim`, VTK, restart, generated-grid, or solver-log output.
- Keep cold-N2 experimental validation separate from the synthetic hot
  DLR-PAR/methalox application study.
- `raptor_like_study/physics_model_status.yaml` is the readiness authority.
