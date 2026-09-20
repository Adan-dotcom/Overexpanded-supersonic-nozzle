import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "cases" / "cea" / "baseline.out"
PRODUCTS = ROOT / "cases" / "cea" / "baseline_products.csv"
SUMMARY = ROOT / "cases" / "cea" / "baseline_summary.json"


def main() -> None:
    lines = OUTPUT.read_text(encoding="ascii").splitlines()
    header = next(i for i, line in enumerate(lines) if "CHAMBER" in line and "THROAT" in line and "EXIT" in line)
    states: dict[str, dict[str, float]] = {"pressure_bar": {}, "temperature_k": {}, "mach": {}}
    for line in lines[header + 1 : header + 20]:
        tokens = line.split()
        if len(tokens) >= 4 and tokens[0] in {"P,", "T,", "Mach"}:
            if tokens[0] == "P,":
                states["pressure_bar"] = dict(zip(("chamber", "throat", "exit"), map(float, tokens[-3:])))
            elif tokens[0] == "T,":
                states["temperature_k"] = dict(zip(("chamber", "throat", "exit"), map(float, tokens[-3:])))
            elif tokens[0] == "Mach":
                states["mach"] = dict(zip(("chamber", "throat", "exit"), map(float, tokens[-3:])))

    mass_start = next(i for i, line in enumerate(lines) if line.strip() == "MASS FRACTIONS")
    product_rows = []
    for line in lines[mass_start + 1 :]:
        tokens = line.split()
        if not tokens or tokens[0].startswith("PRODUCTS"):
            if product_rows and tokens and tokens[0].startswith("PRODUCTS"):
                break
            continue
        if len(tokens) == 4:
            try:
                values = [float(value.replace("E", "e")) for value in tokens[1:]]
            except ValueError:
                continue
            if re.match(r"^[A-Za-z(]", tokens[0]):
                product_rows.append((tokens[0], *values))

    with PRODUCTS.open("w", newline="", encoding="ascii") as stream:
        writer = csv.writer(stream)
        writer.writerow(("species", "chamber_mass_fraction", "throat_mass_fraction", "exit_mass_fraction"))
        writer.writerows(product_rows)
    SUMMARY.write_text(json.dumps(states, indent=2) + "\n", encoding="ascii")
    print(f"Wrote {PRODUCTS}")
    print(f"Wrote {SUMMARY}")
    print(json.dumps(states, indent=2))


if __name__ == "__main__":
    main()
