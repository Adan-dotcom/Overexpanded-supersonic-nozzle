# SU2 mesh preprocessing check

All three meshes were read by SU2 8.5.0 and exercised with one Euler iteration.
This is a mesh-format and geometry check, not a converged flow solution.

| Level | Points | Cells | SU2 min orthogonality | Max CV face aspect ratio | Max sub-volume ratio |
|---|---:|---:|---:|---:|---:|
| Coarse | 103,329 | 102,400 | 57.737 deg | 538.752 | 4.27906 |
| Medium | 321,801 | 320,000 | 57.622 deg | 538.974 | 3.71651 |
| Fine | 950,697 | 947,200 | 64.587 deg | 539.084 | 3.72884 |

SU2 reported all volume and surface elements correctly oriented for every level.
The large maximum aspect ratio occurs in the intentionally thin, wall-normal
cells. Wall orthogonality from the generator is 89.4 degrees or better. Final
acceptance still requires converged `y+`, separation location, wall pressure,
and grid-convergence results.
