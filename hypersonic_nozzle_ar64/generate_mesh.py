from math import cos, exp, pi
from pathlib import Path


OUT = Path(__file__).with_name("nozzle_axisymmetric.su2")

# Geometry in metres. The divergent uses a smooth bell-like cubic contour.
X_INLET = -0.040
X_THROAT = 0.0
X_EXIT = 0.200
X_OUTLET = 0.400
R_INLET = 0.025
R_THROAT = 0.010
R_EXIT = 0.080

N_CONVERGENT = 60
N_DIVERGENT = 220
N_DOWNSTREAM = 160
N_RADIAL = 100
WALL_CLUSTERING = 7.0


def wall_radius(x: float) -> float:
    if x <= X_THROAT:
        s = (x - X_INLET) / (X_THROAT - X_INLET)
        return R_THROAT + 0.5 * (R_INLET - R_THROAT) * (1.0 + cos(pi * s))
    if x >= X_EXIT:
        return R_EXIT
    s = (x - X_THROAT) / (X_EXIT - X_THROAT)
    smoothstep = 3.0 * s * s - 2.0 * s * s * s
    return R_THROAT + (R_EXIT - R_THROAT) * smoothstep


def axial_stations() -> list[float]:
    convergent = [
        X_INLET + (X_THROAT - X_INLET) * i / N_CONVERGENT
        for i in range(N_CONVERGENT)
    ]
    divergent = [
        X_THROAT + (X_EXIT - X_THROAT) * i / N_DIVERGENT
        for i in range(N_DIVERGENT + 1)
    ]
    downstream = [
        X_EXIT + (X_OUTLET - X_EXIT) * i / N_DOWNSTREAM
        for i in range(1, N_DOWNSTREAM + 1)
    ]
    return convergent + divergent + downstream


def radial_fraction(j: int) -> float:
    # j=0 is the axis and j=N_RADIAL is the wall. Exponential spacing
    # concentrates cells at the no-slip wall for the SST boundary layer.
    distance_from_wall = (N_RADIAL - j) / N_RADIAL
    wall_distance_fraction = (
        exp(WALL_CLUSTERING * distance_from_wall) - 1.0
    ) / (exp(WALL_CLUSTERING) - 1.0)
    return 1.0 - wall_distance_fraction


def node(i: int, j: int) -> int:
    return i * (N_RADIAL + 1) + j


def main() -> None:
    xs = axial_stations()
    n_axial = len(xs) - 1
    n_points = len(xs) * (N_RADIAL + 1)
    n_elements = n_axial * N_RADIAL

    with OUT.open("w", encoding="ascii", newline="\n") as mesh:
        mesh.write("NDIME= 2\n")
        mesh.write(f"NELEM= {n_elements}\n")
        element_id = 0
        for i in range(n_axial):
            for j in range(N_RADIAL):
                mesh.write(
                    f"9 {node(i, j)} {node(i + 1, j)} "
                    f"{node(i + 1, j + 1)} {node(i, j + 1)} {element_id}\n"
                )
                element_id += 1

        mesh.write(f"NPOIN= {n_points}\n")
        for i, x in enumerate(xs):
            radius = wall_radius(x)
            for j in range(N_RADIAL + 1):
                r = radius * radial_fraction(j)
                mesh.write(f"{x:.12e} {r:.12e} {node(i, j)}\n")

        mesh.write("NMARK= 4\n")

        mesh.write("MARKER_TAG= WALL\n")
        mesh.write(f"MARKER_ELEMS= {n_axial}\n")
        for i in range(n_axial):
            mesh.write(f"3 {node(i, N_RADIAL)} {node(i + 1, N_RADIAL)}\n")

        mesh.write("MARKER_TAG= INLET\n")
        mesh.write(f"MARKER_ELEMS= {N_RADIAL}\n")
        for j in range(N_RADIAL):
            mesh.write(f"3 {node(0, j + 1)} {node(0, j)}\n")

        mesh.write("MARKER_TAG= OUTLET\n")
        mesh.write(f"MARKER_ELEMS= {N_RADIAL}\n")
        for j in range(N_RADIAL):
            mesh.write(f"3 {node(n_axial, j)} {node(n_axial, j + 1)}\n")

        mesh.write("MARKER_TAG= AXIS\n")
        mesh.write(f"MARKER_ELEMS= {n_axial}\n")
        for i in range(n_axial):
            mesh.write(f"3 {node(i + 1, 0)} {node(i, 0)}\n")

    first_cell_height = wall_radius(X_THROAT) * (1.0 - radial_fraction(N_RADIAL - 1))
    area_ratio = (R_EXIT / R_THROAT) ** 2
    print(f"Wrote {OUT}")
    print(f"Cells: {n_elements}; points: {n_points}")
    print(f"Ae/At: {area_ratio:.1f}; throat first-cell height: {first_cell_height:.3e} m")


if __name__ == "__main__":
    main()
