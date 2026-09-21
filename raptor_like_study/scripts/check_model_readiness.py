"""Fail closed before launching a CFD track whose physics model is not ready."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATUS = ROOT / "physics_model_status.yaml"


def check_readiness(status: dict, track_name: str, stage: str) -> tuple[bool, list[str]]:
    tracks = status.get("tracks", {})
    if track_name not in tracks:
        return False, [f"unknown_track:{track_name}"]
    track = tracks[track_name]
    enabled_key = "software_screening_enabled" if stage == "screen" else "production_enabled"
    enabled = track.get(enabled_key) is True
    return enabled, [] if enabled else list(track.get("blockers", [f"{enabled_key}=false"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("track")
    parser.add_argument("--stage", choices=("screen", "production"), required=True)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    args = parser.parse_args()

    status = yaml.safe_load(args.status.read_text(encoding="utf-8"))
    ready, blockers = check_readiness(status, args.track, args.stage)
    label = "READY" if ready else "BLOCKED"
    print(f"{label}: {args.track} / {args.stage}")
    for blocker in blockers:
        print(f"- {blocker}")
    raise SystemExit(0 if ready else 2)


if __name__ == "__main__":
    main()
