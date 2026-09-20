import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOE = ROOT / "cases" / "doe.csv"
INPUT_DIR = ROOT / "cases" / "cea" / "doe_inputs"
SUMMARY = ROOT / "cases" / "cea" / "cea_summary.csv"
PRODUCTS = ROOT / "cases" / "cea" / "products_long.csv"


def values_after_label(lines: list[str], label: str) -> list[float]:
    for line in lines:
        if line.strip().startswith(label):
            tokens = line.split()
            try:
                return [float(token.replace("E", "e")) for token in tokens[-3:]]
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
        ("Density,", "density", ""),
        ("Cp,", "cp", ""),
        ("Gamma_s", "gamma", ""),
        ("M,", "molecular_weight", ""),
        ("Son.", "sound_speed", ""),
    ):
        vals = values_after_label(lines, prefix)
        if len(vals) == 3:
            for location, value in zip(("chamber", "throat", "exit"), vals):
                states[f"{key}_{location}_{unit}" if unit else f"{key}_{location}"] = value

    mass_start = next(i for i, line in enumerate(lines) if line.strip() == "MASS FRACTIONS")
    products: list[dict[str, object]] = []
    for line in lines[mass_start + 1 :]:
        tokens = line.split()
        if tokens and tokens[0].startswith("PRODUCTS"):
            break
        if len(tokens) != 4:
            continue
        try:
            values = [float(value.replace("E", "e")) for value in tokens[1:]]
        except ValueError:
            continue
        if re.match(r"^[A-Za-z(]", tokens[0]):
            products.append({"species": tokens[0], "chamber": values[0], "throat": values[1], "exit": values[2]})
    return states, products


def main() -> None:
    with DOE.open(newline="", encoding="ascii") as stream:
        doe_rows = {row["case_id"]: row for row in csv.DictReader(stream)}

    summary_rows = []
    product_rows = []
    for output in sorted(INPUT_DIR.glob("*.out")):
        case_id = output.stem
        states, products = parse_output(output)
        row = dict(doe_rows[case_id])
        row.update(states)
        summary_rows.append(row)
        for product in products:
            product_rows.append({"case_id": case_id, **product})

    if not summary_rows:
        raise RuntimeError(f"No CEA outputs found in {INPUT_DIR}")
    fields = list(summary_rows[0])
    with SUMMARY.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)
    with PRODUCTS.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=("case_id", "species", "chamber", "throat", "exit"))
        writer.writeheader()
        writer.writerows(product_rows)
    print(f"Wrote {SUMMARY} ({len(summary_rows)} cases)")
    print(f"Wrote {PRODUCTS} ({len(product_rows)} species rows)")


if __name__ == "__main__":
    main()
