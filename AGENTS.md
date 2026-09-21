# Agent instructions

Read `HANDOFF.md`, `raptor_like_study/RUN_STATUS.md`, and
`raptor_like_study/ASSUMPTIONS_AND_EVIDENCE.md` before running CFD.

`CODEX_CONVERSATION.md` is a sanitized user/assistant transcript of the
original local Codex session. Read it only when the concise handoff and run
status do not answer a historical question; it is intentionally not a raw
Codex session database.

- No current CFD case is a physics-accepted ML label.
- Never train final models from smoke, screening, mock, or failed-gate data.
- Do not continue the one-atmosphere single-LUT plume as a physical model: it
  represents the exterior with cold methalox products rather than air.
- Run `raptor_like_study/scripts/check_model_readiness.py` before any new campaign. A blocked
  production track must not be bypassed by relabeling a smoke test.
- The NASA-refined LUT is an interpolation-qualified single-composition
  candidate; the legacy GRI-Mech LUT is rejected.
- Keep NPR derived from `Pc/Pa`; do not independently sample all three quantities.
- Do not commit raw VTK, restart DAT, or generated mesh files. Regenerate them locally and update `LOCAL_ARTIFACTS_MANIFEST.csv` when needed.
- Use six MPI ranks on a six-core Ryzen unless a new benchmark establishes otherwise.
- Preserve the distinction between DLR cold-N2 validation and the synthetic DLR-PAR/methalox application study.
- Read `raptor_like_study/physics_model_status.yaml` as the machine-readable
  authority for model readiness.
