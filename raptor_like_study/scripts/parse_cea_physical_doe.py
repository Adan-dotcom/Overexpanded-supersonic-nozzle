"""Join NASA CEA chamber/nozzle states to the corrected physical DOE."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOE = ROOT / "cases" / "physical_doe.csv"
INPUT_DIR = ROOT / "cases" / "cea" / "physical_doe_inputs"
SUMMARY = ROOT / "cases" / "cea" / "physical_cea_summary.csv"
PRODUCTS = ROOT / "cases" / "cea" / "physical_products_long.csv"


def values_after_label(lines: list[str], label: str) -> list[float]:
    for line in lines:
        if line.strip().startswith(label):
            try:
                return [float(token.replace("E", "e")) for token in line.split()[-3:]]
            except ValueError:
                return []
    return []


def parse_output(path: Path) -> tuple[dict[str, float], list[dict[str, object]]]:
    lines = path.read_text(encoding="ascii").splitlines()
    states: dict[str, float] = {}
    for prefix, key, unit in (
        ("P,", "pressure", "bar"),
        ("T,", "temperature", "k"),
        ("Mach", "mach", ""),
        ("Density,", "density", "kg_m3"),
        ("Cp,", "cp", "kj_kg_k"),
        ("Gamma_s", "gamma", ""),
        ("M,", "molecular_weight", "kg_kmol"),
        ("Son.", "sound_speed", "m_s"),
    ):
        values = values_after_label(lines, prefix)
        if len(values) == 3:
            for location, value in zip(("chamber", "throat", "exit"), values):
                suffix = f"_{unit}" if unit else ""
                states[f"{key}_{location}{suffix}"] = value

    mass_start = next(index for index, line in enumerate(lines) if line.strip() == "MASS FRACTIONS")
    products = []
    for line in lines[mass_start + 1 :]:
        tokens = line.split()
        if tokens and tokens[0].startswith("PRODUCTS"):
            break
        if len(tokens) != 4 or not re.match(r"^[A-Za-z(]", tokens[0]):
            continue
        try:
            values = [float(value.replace("E", "e")) for value in tokens[1:]]
        except ValueError:
            continue
        products.append(
            {"species": tokens[0], "chamber": values[0], "throat": values[1], "exit": values[2]}
        )
    return states, products


def main() -> None:
    with DOE.open(newline="", encoding="ascii") as stream:
        doe_rows = {row["case_id"]: row for row in csv.DictReader(stream)}

    summary_rows = []
    product_rows = []
    for output in sorted(INPUT_DIR.glob("*.out")):
        states, products = parse_output(output)
        row = dict(doe_rows[output.stem])
        row["t0_k"] = states["temperature_chamber_k"]
        row.update(states)
        summary_rows.append(row)
        product_rows.extend({"case_id": output.stem, **product} for product in products)

    if len(summary_rows) != len(doe_rows):
        raise RuntimeError(f"Expected {len(doe_rows)} CEA outputs, found {len(summary_rows)}")
    with SUMMARY.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    with PRODUCTS.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=("case_id", "species", "chamber", "throat", "exit"))
        writer.writeheader()
        writer.writerows(product_rows)

    temperatures = [float(row["t0_k"]) for row in summary_rows]
    print(f"Wrote {SUMMARY} ({len(summary_rows)} cases)")
    print(f"Chamber temperature range: {min(temperatures):.2f} to {max(temperatures):.2f} K")
    print(f"Wrote {PRODUCTS} ({len(product_rows)} species rows)")


if __name__ == "__main__":
    main()
