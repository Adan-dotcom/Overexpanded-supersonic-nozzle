#!/usr/bin/env python3
"""Record the official Mabey turbulence initialization without running it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-job", type=Path, required=True)
    parser.add_argument("--executed-job", type=Path, required=True)
    parser.add_argument("--prep-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.executed_job.read_text(encoding="utf-8")
    log = args.prep_log.read_text(encoding="utf-8", errors="replace")
    tke = re.search(r"turb=\{([0-9.eE+-]+),", log)
    omega = re.search(r"turb=\{[0-9.eE+-]+,\s*([0-9.eE+-]+),", log)
    payload = {
        "scope": "official_initialization_only_no_solver_run",
        "installed_job_sha256": digest(args.installed_job),
        "executed_job_sha256": digest(args.executed_job),
        "source_copy_unmodified": digest(args.installed_job) == digest(args.executed_job),
        "formulation_lines_present": all(
            phrase in source
            for phrase in (
                "config.turbulence_model = \"k_log_omega\"",
                "tke_inf = 1.5 * (turb_intensity * V_inf)^2",
                "omega_inf = gs.rho * tke_inf / mu_t",
                "omega_inf = math.log(omega_inf)",
            )
        ),
        "prep_completed": "Build fluid files." in log,
        "inflow_tke": float(tke.group(1)) if tke else None,
        "inflow_log_omega": float(omega.group(1)) if omega else None,
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
