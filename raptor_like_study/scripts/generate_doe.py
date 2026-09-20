"""Generate the corrected fixed-geometry physical DOE and NASA CEA inputs."""

from __future__ import annotations

import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOE = ROOT / "cases" / "physical_doe.csv"
CEA_DIR = ROOT / "cases" / "cea" / "physical_doe_inputs"
SEED = 20260919
NOMINAL_CASES = 24
THROTTLE_CASES = 24


def lhs(low: float, high: float, n: int, rng: random.Random) -> list[float]:
    bins = [(index + rng.random()) / n for index in range(n)]
    rng.shuffle(bins)
    return [low + value * (high - low) for value in bins]


def cea_input(pc_pa: float, of_ratio: float) -> str:
    return "\n".join(
        (
            "problem rocket equilibrium",
            f"  p,bar={pc_pa / 1.0e5:.8f}",
            f"  o/f={of_ratio:.8f}",
            "  supar=30.0",
            "reactant",
            "  fuel CH4(L) wt%=100 t(k)=111.66",
            "  oxid O2(L) wt%=100 t(k)=90.17",
            "output massf trace=1e-8 transport",
            "end",
            "",
        )
    )


def make_campaign(
    name: str,
    count: int,
    pc_range: tuple[float, float],
    pa_range: tuple[float, float],
    rng: random.Random,
    evidence_status: str,
) -> list[dict[str, object]]:
    pc_values = lhs(*pc_range, count, rng)
    of_values = lhs(3.10, 3.30, count, rng)
    pa_values = (
        [pa_range[0]] * count
        if pa_range[0] == pa_range[1]
        else lhs(*pa_range, count, rng)
    )
    rows = []
    for index, (pc_pa, of_ratio, pa_pa) in enumerate(zip(pc_values, of_values, pa_values), start=1):
        rows.append(
            {
                "case_id": f"{name}_{index:03d}",
                "campaign": name,
                "geometry_id": "DLR_PAR",
                "pc_pa": pc_pa,
                "pa_pa": pa_pa,
                "npr": pc_pa / pa_pa,
                "of_ratio": of_ratio,
                "t0_k": "CEA_PENDING",
                "gas_model": "equilibrium_products_LUT",
                "turbulence_model": "SST_2003m",
                "wall_model": "adiabatic",
                "evidence_status": evidence_status,
                "physics_accepted": "false",
                "training_eligible": "false",
            }
        )
    return rows


def validate(rows: list[dict[str, object]]) -> None:
    for row in rows:
        pc = float(row["pc_pa"])
        pa = float(row["pa_pa"])
        npr = float(row["npr"])
        if pa > 101325.0 + 1.0e-9:
            raise ValueError(f"{row['case_id']}: pa exceeds one atmosphere")
        if abs(npr - pc / pa) > 1.0e-12 * npr:
            raise ValueError(f"{row['case_id']}: inconsistent NPR")
        if not 3.10 <= float(row["of_ratio"]) <= 3.30:
            raise ValueError(f"{row['case_id']}: O/F outside declared range")
        if row["campaign"] == "hot_methalox_nominal" and not 5.10e6 <= pc <= 5.40e6:
            raise ValueError(f"{row['case_id']}: nominal Pc outside evidence envelope")


def main() -> None:
    rng = random.Random(SEED)
    rows = make_campaign(
        "hot_methalox_nominal",
        NOMINAL_CASES,
        (5.10e6, 5.40e6),
        (50.0e3, 101325.0),
        rng,
        "representative_LLAMA_scale_operating_envelope",
    )
    rows.extend(
        make_campaign(
            "hot_methalox_ground_throttle_exploratory",
            THROTTLE_CASES,
            (2.00e6, 5.40e6),
            (101325.0, 101325.0),
            rng,
            "exploratory_not_validated_below_5.1MPa",
        )
    )
    validate(rows)

    DOE.parent.mkdir(parents=True, exist_ok=True)
    CEA_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with DOE.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        (CEA_DIR / f"{row['case_id']}.inp").write_text(
            cea_input(float(row["pc_pa"]), float(row["of_ratio"])), encoding="ascii"
        )

    nominal_npr = [float(row["npr"]) for row in rows if row["campaign"] == "hot_methalox_nominal"]
    throttle_npr = [
        float(row["npr"])
        for row in rows
        if row["campaign"] == "hot_methalox_ground_throttle_exploratory"
    ]
    print(f"Wrote {DOE} with {len(rows)} fixed-geometry cases")
    print(f"Nominal NPR: {min(nominal_npr):.2f} to {max(nominal_npr):.2f}")
    print(f"Throttle NPR: {min(throttle_npr):.2f} to {max(throttle_npr):.2f}")
    print(f"Wrote NASA CEA inputs to {CEA_DIR}")


if __name__ == "__main__":
    main()
