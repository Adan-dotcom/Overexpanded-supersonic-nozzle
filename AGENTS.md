# Agent instructions

Read `HANDOFF.md`, `raptor_like_study/RUN_STATUS.md`, and
`raptor_like_study/ASSUMPTIONS_AND_EVIDENCE.md` before running CFD.

- No current CFD case is a physics-accepted ML label.
- Never train final models from smoke, screening, mock, or failed-gate data.
- The surviving numerical branch is the one-atmosphere hybrid-plume LUT/SST/HLLC URANS case.
- Keep NPR derived from `Pc/Pa`; do not independently sample all three quantities.
- Do not commit raw VTK, restart DAT, or generated mesh files. Regenerate them locally and update `LOCAL_ARTIFACTS_MANIFEST.csv` when needed.
- Use six MPI ranks on a six-core Ryzen unless a new benchmark establishes otherwise.
- Preserve the distinction between DLR cold-N2 validation and the synthetic DLR-PAR/methalox application study.

