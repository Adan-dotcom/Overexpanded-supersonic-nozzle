# Internal nozzle meshes

`generate_internal_mesh.py` builds structured, wall-normal-clustered
axisymmetric meshes from `DLR_PAR_full_contour.csv`. The outlet lies at the
nozzle exit and is intended for a Riemann static-pressure boundary condition.
This avoids assigning combustion-product thermodynamics to an ambient-air
domain.

```powershell
cd 'D:\PRUEBA SU2_2026\raptor_like_study'
.\.venv\Scripts\python.exe internal_mesh\generate_internal_mesh.py --profile pilot
.\.venv\Scripts\python.exe internal_mesh\generate_internal_mesh.py --profile medium
.\.venv\Scripts\python.exe internal_mesh\generate_internal_mesh.py --profile fine
```

The `screen` profile contains 76,800 quadrilaterals and is only for rapid model
elimination. A result from it is never an accepted separation label. Survivors
must reproduce their behavior on `pilot`, then pass the medium/fine gates.

The generated profiles contain 102,400, 320,000, and 1,024,000 quadrilaterals.
Their first wall-cell heights are 1, 0.5, and 0.25 micrometers, and their
minimum scaled Jacobians are 0.9906, 0.9938, and 0.9951, respectively. All
three `.su2` meshes and their `mesh_summary.json` files are present under
`pilot/`, `medium/`, and `fine/`.
