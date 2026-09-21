"""Write explicit provenance for a failed cold-N2 solver attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--started-utc", required=True)
    parser.add_argument("--ended-utc", required=True)
    parser.add_argument("--elapsed-seconds", type=float, required=True)
    parser.add_argument("--adjustment", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_dir.resolve()
    log = root / "solver.log"
    parameters_path = root / "run_parameters.json"
    text = log.read_text(encoding="utf-8", errors="replace")
    payload = {
        "case_id": "dlr_par_cold_n2_internal_screen_v1",
        "classification": "failed_provisional_internal_domain_screen_not_validation",
        "attempt": args.attempt,
        "started_utc": args.started_utc,
        "ended_utc": args.ended_utc,
        "elapsed_upper_bound_seconds": args.elapsed_seconds,
        "solver_exit_status": 136,
        "normal_solver_exit": False,
        "failure_signature": "floating_point_divide_by_zero_in_decompILU0_at_newton_step_1",
        "numerical_adjustment": args.adjustment,
        "parameters": json.loads(parameters_path.read_text()),
        "eilmer_commit": "f53f4609a0331d48efee69a4e4f3c3598378cc03",
        "source_repository_commit": "36fd2d49f2b0675cc8c133195688139d70d77fc5",
        "mpi_ranks": 6,
        "hostname": platform.node(),
        "platform": platform.platform(),
        "solver_log_sha256": sha256(log),
        "run_parameters_sha256": sha256(parameters_path),
        "failure_signature_found_in_log": (
            "Floating point divide-by-zero" in text and "decompILU0" in text
        ),
        "vtk_export_present": any((root / "lmrsim" / "vtk").rglob("*.vtu")),
        "wall_profile_export_present": (root / "wall_profile.csv").exists(),
        "state_audit_completed": False,
        "wall_metrics_completed": False,
        "residual_status": "initial_global_relative_residual_1.0_then_crash_before_completed_iteration",
        "mass_balance_available": False,
        "energy_balance_available": False,
        "physics_accepted": False,
        "training_eligible": False,
        "artifact_directory": str(root),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
