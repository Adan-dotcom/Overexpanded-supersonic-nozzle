# DLR-PAR mesh study

This folder generates three structured, axisymmetric quadrilateral meshes from
`../../DLR_PAR_full_contour.csv`. The contour is geometry; the `.su2` files in
`coarse`, `medium`, and `fine` are the CFD meshes.

The radial topology contains a core block and a 1.5 mm wall-normal block. The
first wall-cell heights are 1.00, 0.50, and 0.25 micrometres. These values are
initial design targets; the actual adequacy is decided from the converged `y+`
field, not from geometry alone.

```powershell
cd "D:\PRUEBA SU2_2026\raptor_like_study\dlr_par_mesh_study"
python .\generate_meshes.py
```

`mesh_summary.csv` records cell counts and geometric quality. A mesh is rejected
if any quadrilateral has zero or negative signed area. SU2's own geometry checks
must also pass before a flow solution is accepted.

The current domain ends at the physical nozzle exit. Before production, outlet
sensitivity will be checked against a downstream ambient extension because
separated subsonic regions can be influenced by a pressure boundary placed too
close to the nozzle.
