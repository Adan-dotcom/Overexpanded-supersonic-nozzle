# DLR-PAR geometry screen report

The user-reconstructed DLR-PAR contour was converted from millimetres to
metres and meshed with the pinned Eilmer 5 commit
`f53f4609a0331d48efee69a4e4f3c3598378cc03`.  The geometry-only screen passed
all declared checks on 2026-09-21.

## Contour

- 385 finite points with strictly increasing axial coordinate.
- Unique minimum-radius point at `x=0`, `r=0.010 m`.
- Inlet at `x=-0.02268 m`, `r=0.020 m`.
- Exit at `x=0.12502 m`, `r=0.05477226 m`.
- Exit/throat area ratio: `30.0000046551`.
- SHA-256: `8984b016bbebb3b6816d92c0b30ef46a84ffa1867edb9888cc525efb68fee116`.

This confirms internal consistency only.  The CSV remains a user
reconstruction and must be checked against the published geometry before the
experimental validation claim can close.

## Inspection grid

- 92,160 quadrilateral cells in six equal, conformal blocks.
- All signed cell areas are positive; minimum `7.1631e-10 m2`.
- Five internal interfaces match exactly within floating-point output.
- Corner-angle range: `56.12` to `123.94 deg`.
- Maximum edge-length aspect ratio: `14.005`.
- Maximum adjacent-cell area ratio: `1.2813`.
- Wall-adjacent vertex spacing: `14.36` to `78.64 micrometres`.

No flow solver was executed, no MPI ranks were used, and `y+` was not
evaluated.  This grid is not a wall-resolved validation mesh and is not a CFD
label.  The next CFD block still requires published cold-N2 boundary
conditions and experimental anchors, followed by a three-level mesh family.

Heavy generated files and the inspection plot remain at
`/home/adan/eilmer-artifacts/dlr-par-geometry-20260921-02`.
