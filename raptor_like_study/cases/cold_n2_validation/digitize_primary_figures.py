#!/usr/bin/env python3
"""Extract DLR cold-N2 validation targets from the supplied vector PDF.

This extractor is deliberately tied to the exact Verma--Haidn PDF recorded
below.  It reads vector paths rather than raster pixels, validates counts and
ordering, and writes only dimensionless quantities published in the figures.
It does not manufacture the unreported absolute test conditions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

import pymupdf


EXPECTED_SHA256 = "f1d05035c7c39e2a589d827fd9461b2eaba0e763cd2e915a1f44cbd0649e1b73"
ARTICLE_DOI = "10.2514/1.42351"


def pdf_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def transform(point, axes, x_limits, y_limits):
    """Map a PDF point into linear plot coordinates."""
    x_left, y_bottom, x_right, y_top = axes
    x_value = x_limits[0] + (point[0] - x_left) / (x_right - x_left) * (
        x_limits[1] - x_limits[0]
    )
    y_value = y_limits[0] + (y_bottom - point[1]) / (y_bottom - y_top) * (
        y_limits[1] - y_limits[0]
    )
    return x_value, y_value


def unique_line_vertices(drawings: Iterable[dict], axes, x_limits, y_limits):
    points = []
    for drawing in drawings:
        for item in drawing["items"]:
            if item[0] != "l":
                continue
            for point in item[1:3]:
                value = transform(point, axes, x_limits, y_limits)
                if not points or max(abs(value[k] - points[-1][k]) for k in (0, 1)) > 1.0e-5:
                    points.append(value)
    return points


def gray(color) -> float | None:
    return None if color is None else float(color[0])


def close(value: float | None, target: float, tolerance: float = 0.002) -> bool:
    return value is not None and abs(value - target) <= tolerance


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def figure_3a_rows(document) -> list[dict]:
    # PDF page 3 / journal page 1048, Fig. 3a.  Axes are the outer vector frame.
    axes = (158.670, 123.528, 283.750, 50.566)
    drawings = document[2].get_drawings()
    # Marker fill and path-item count uniquely identify each legend series.
    series = {
        30: (0.073, 1),  # square
        33: (0.410, 2),  # upward triangle
        35: (0.247, 2),  # downward triangle
        37: (0.430, 3),  # diamond
        40: (0.000, 11),  # circle
    }
    text_positions = {
        8: (8.145, 8.145),
        9: (8.945, 8.945),
        # The article prints 9.734 in Figs. 3b/8 and 9.735 in the body text.
        10: (9.734, 9.735),
        11: (10.540, 10.540),
        12: (11.340, 11.340),
        13: (12.135, 12.135),
    }
    rows = []
    for npr, (target_gray, item_count) in series.items():
        markers = []
        for drawing in drawings:
            rect = drawing["rect"]
            if drawing["fill"] is None or not close(gray(drawing["fill"]), target_gray):
                continue
            if len(drawing["items"]) != item_count:
                continue
            center = ((rect.x0 + rect.x1) / 2.0, (rect.y0 + rect.y1) / 2.0)
            # This admits the 13 data markers and rejects the in-plot legend.
            if 162.0 < rect.x0 and center[0] < 264.7 and 54.0 < rect.y0 and rect.y1 < 112.0:
                markers.append(center)
        markers.sort(key=lambda point: point[0])
        if len(markers) != 13:
            raise RuntimeError(f"Fig. 3a NPR {npr}: expected 13 markers, found {len(markers)}")
        for station, marker in enumerate(markers, start=1):
            x_rt, pressure = transform(marker, axes, (2.0, 14.0), (0.0, 1.0))
            reported_min, reported_max = text_positions.get(station, (None, None))
            rows.append(
                {
                    "source_figure": "3a",
                    "sweep_direction": "startup",
                    "npr": f"{npr:.0f}",
                    "profile_type": "mean_pressure_15s_hold",
                    "station_label": f"base_{station:02d}",
                    "x_rt": f"{x_rt:.6f}",
                    "pwall_over_pa": f"{pressure:.6f}",
                    "text_x_rt_min": "" if reported_min is None else f"{reported_min:.3f}",
                    "text_x_rt_max": "" if reported_max is None else f"{reported_max:.3f}",
                    "digitization_uncertainty_x_rt": "0.018",
                    "digitization_uncertainty_pwall_over_pa": "0.003",
                    "experimental_uncertainty_pwall_over_pa": "",
                }
            )
    return rows


def figure_7_rows(document):
    # PDF page 6 / journal page 1051.  Values are vertices of the plotted paths.
    drawings = document[5].get_drawings()
    axes_a = (127.950, 134.643, 279.397, 49.342)
    axes_b = (321.201, 134.641, 473.900, 49.698)

    startup_a = [
        drawing
        for drawing in drawings
        if close(gray(drawing["color"]), 0.055)
        and abs((drawing["width"] or 0.0) - 0.670) < 0.01
        and 149.0 <= drawing["rect"].x0 < 260.0
        and drawing["rect"].y1 < 127.0
    ]
    shutdown_a = [
        drawing
        for drawing in drawings
        if close(gray(drawing["color"]), 0.410)
        and abs((drawing["width"] or 0.0) - 0.670) < 0.01
        and drawing["rect"].width > 60.0
        and drawing["rect"].y1 < 127.0
    ]
    startup_b = [
        drawing
        for drawing in drawings
        if close(gray(drawing["color"]), 0.055)
        and abs((drawing["width"] or 0.0) - 0.721) < 0.01
        and drawing["rect"].width > 70.0
    ]
    shutdown_b = [
        drawing
        for drawing in drawings
        if close(gray(drawing["color"]), 0.410)
        and abs((drawing["width"] or 0.0) - 0.721) < 0.01
        and drawing["rect"].width > 100.0
    ]

    curves_a = {
        "startup": unique_line_vertices(startup_a, axes_a, (0.0, 70.0), (0.0, 14.0)),
        "shutdown": unique_line_vertices(shutdown_a, axes_a, (0.0, 70.0), (0.0, 14.0)),
    }
    curves_b = {
        "startup": unique_line_vertices(startup_b, axes_b, (0.0, 70.0), (0.0, 0.6)),
        "shutdown": unique_line_vertices(shutdown_b, axes_b, (0.0, 70.0), (0.0, 0.6)),
    }
    expected = {"startup": (14, 9), "shutdown": (17, 14)}
    for direction in expected:
        # Remove only consecutive duplicate vertices at the split in Fig. 7a.
        deduplicated = []
        for point in curves_a[direction]:
            if not deduplicated or max(abs(point[k] - deduplicated[-1][k]) for k in (0, 1)) > 1.0e-5:
                deduplicated.append(point)
        curves_a[direction] = deduplicated
        if (len(curves_a[direction]), len(curves_b[direction])) != expected[direction]:
            raise RuntimeError(
                f"Fig. 7 {direction}: unexpected vertex counts "
                f"{len(curves_a[direction])}, {len(curves_b[direction])}"
            )

    separation_rows = []
    pressure_rows = []
    for direction, points in curves_a.items():
        for npr, x_sep in points:
            separation_rows.append(
                {
                    "source_figure": "7a",
                    "sweep_direction": direction,
                    "npr": f"{npr:.6f}",
                    "x_sep_over_rt": f"{x_sep:.6f}",
                    "digitization_uncertainty_npr": "0.155",
                    "digitization_uncertainty_x_sep_over_rt": "0.055",
                    "experimental_uncertainty_x_sep_over_rt": "",
                }
            )
    for direction, points in curves_b.items():
        for npr, pressure in points:
            pressure_rows.append(
                {
                    "source_figure": "7b",
                    "sweep_direction": direction,
                    "npr": f"{npr:.6f}",
                    "pinc_over_pa": f"{pressure:.6f}",
                    "digitization_uncertainty_npr": "0.165",
                    "digitization_uncertainty_pinc_over_pa": "0.0026",
                    "experimental_uncertainty_pinc_over_pa": "",
                }
            )
    return separation_rows, pressure_rows


def station_label(x_rt: float) -> str:
    published_layout = [
        (4.945, "base_04"),
        (5.745, "base_05"),
        (6.545, "base_06"),
        (7.345, "base_07"),
        (8.145, "base_08"),
        (8.545, "mid_08_09"),
        (8.945, "base_09"),
        (9.345, "mid_09_10"),
        (9.735, "base_10"),
        (10.140, "mid_10_11"),
        (10.540, "base_11"),
        (10.940, "mid_11_12"),
        (11.340, "base_12"),
        (12.135, "base_13"),
    ]
    _, label = min(published_layout, key=lambda item: abs(item[0] - x_rt))
    return label


def figure_11a_rows(document) -> list[dict]:
    # PDF page 9 / journal page 1054, Fig. 11a.
    axes = (68.440, 543.950, 275.980, 415.360)
    drawings = document[8].get_drawings()
    paths = [
        drawing
        for drawing in drawings
        if abs((drawing["width"] or 0.0) - 0.944) < 0.01
        and 88.0 < drawing["rect"].x0 < 111.0
        and 250.0 < drawing["rect"].x1 < 260.0
        and 425.0 < drawing["rect"].y0
        and drawing["rect"].y1 < 536.0
        and len(drawing["items"]) >= 12
    ]
    nprs = [33, 30, 28, 26, 24, 22, 20, 18, 16]
    if len(paths) != len(nprs):
        raise RuntimeError(f"Fig. 11a: expected {len(nprs)} paths, found {len(paths)}")
    rows = []
    for npr, path in zip(nprs, paths):
        points = unique_line_vertices([path], axes, (4.0, 13.0), (0.0, 2.2))
        if len(points) not in (13, 14):
            raise RuntimeError(f"Fig. 11a NPR {npr}: unexpected point count {len(points)}")
        for x_rt, pressure in points:
            rows.append(
                {
                    "source_figure": "11a",
                    "sweep_direction": "shutdown",
                    "npr": f"{npr:.0f}",
                    "profile_type": "mean_pressure_15s_hold_independent_run",
                    "station_label": station_label(x_rt),
                    "x_rt": f"{x_rt:.6f}",
                    "pwall_over_pa": f"{pressure:.6f}",
                    "text_x_rt_min": "",
                    "text_x_rt_max": "",
                    "digitization_uncertainty_x_rt": "0.021",
                    "digitization_uncertainty_pwall_over_pa": "0.009",
                    "experimental_uncertainty_pwall_over_pa": "",
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path, help="Verma--Haidn 2009 article PDF")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    actual_sha = pdf_sha256(args.pdf)
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(
            f"Refusing unrecognized PDF: expected SHA-256 {EXPECTED_SHA256}, got {actual_sha}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(args.pdf)

    pressure_rows = figure_3a_rows(document) + figure_11a_rows(document)
    separation_rows, incipient_rows = figure_7_rows(document)
    profile_fields = [
        "source_figure",
        "sweep_direction",
        "npr",
        "profile_type",
        "station_label",
        "x_rt",
        "pwall_over_pa",
        "text_x_rt_min",
        "text_x_rt_max",
        "digitization_uncertainty_x_rt",
        "digitization_uncertainty_pwall_over_pa",
        "experimental_uncertainty_pwall_over_pa",
    ]
    write_csv(args.output_dir / "published_pressure_profiles.csv", profile_fields, pressure_rows)
    write_csv(
        args.output_dir / "physical_separation_fig7a.csv",
        [
            "source_figure",
            "sweep_direction",
            "npr",
            "x_sep_over_rt",
            "digitization_uncertainty_npr",
            "digitization_uncertainty_x_sep_over_rt",
            "experimental_uncertainty_x_sep_over_rt",
        ],
        separation_rows,
    )
    write_csv(
        args.output_dir / "incipient_pressure_fig7b.csv",
        [
            "source_figure",
            "sweep_direction",
            "npr",
            "pinc_over_pa",
            "digitization_uncertainty_npr",
            "digitization_uncertainty_pinc_over_pa",
            "experimental_uncertainty_pinc_over_pa",
        ],
        incipient_rows,
    )

    provenance = {
        "schema_version": 1,
        "article": {
            "authors": "S. B. Verma and O. Haidn",
            "title": "Study of Restricted Shock Separation Phenomena in a Thrust Optimized Parabolic Nozzle",
            "doi": ARTICLE_DOI,
            "pdf_sha256": actual_sha,
        },
        "extractor": {
            "method": "direct PDF vector-path extraction",
            "pymupdf_version": pymupdf.__version__,
            "script": "digitize_primary_figures.py",
            "figures": ["3a", "7a", "7b", "11a"],
        },
        "records": {
            "published_pressure_profiles": len(pressure_rows),
            "physical_separation_fig7a": len(separation_rows),
            "incipient_pressure_fig7b": len(incipient_rows),
        },
        "uncertainty_policy": {
            "digitization": "half plotted stroke width mapped through each linear axis; rounded upward",
            "experimental": "left blank because the article does not report profile or oil-line uncertainty",
            "sensor_accuracy_reported": "manufacturer accuracy within 0.5% over the stated 0-1 bar operating range; normalization cannot be completed without numeric Pa",
        },
        "reported_text_anchors": {
            "startup_xinc_jump_x_rt": [7.35, 9.735],
            "startup_transition_npr": [33, 35],
            "startup_prss_npr": [35, 37],
            "startup_end_effect_npr": 38.19,
            "startup_end_effect_xsep_shift_mm": [8, 9],
            "shutdown_first_fully_formed_rss_npr": 34,
            "critical_npr_to_initiate_shutdown_rss": 37,
        },
        "unresolved_absolute_conditions": [
            "numeric stagnation temperature per run",
            "numeric ambient pressure per run",
            "numeric stagnation pressure per run",
            "wall thermal condition",
            "inlet turbulence quantities",
            "experimental uncertainty of oil-derived physical separation",
        ],
    }
    with (args.output_dir / "digitization_provenance.json").open("w", encoding="utf-8") as stream:
        json.dump(provenance, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
