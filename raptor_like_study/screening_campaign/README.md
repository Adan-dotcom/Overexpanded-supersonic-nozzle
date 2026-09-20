# Rapid model screening

These runs use the 76,800-cell internal `screen` mesh. They can reject unstable,
nonconservative, or qualitatively wrong configurations. They cannot establish
an accurate separation location and must never be exported as ML labels.

The initial matrix holds geometry, boundary conditions, transport surrogate,
spatial order, and iteration count fixed while varying one of:

- ideal effective gas versus equilibrium-products LUT;
- SST-2003m versus Spalart-Allmaras;
- HLLC versus SLAU2 where SU2 permits it.

Run `make_screening_configs.py`, then execute each generated config from this
directory with six MPI ranks. Stage 1 uses 100 first-order steady iterations,
followed by 300 settling iterations. The control `ideal+SST+HLLC`, turbulence
sensitivity `ideal+SA+HLLC`, and physical-fluid candidate `LUT+SST+HLLC` then
continue for 1,200 iterations at CFL 0.25. Only candidates with reasonable
mass/energy behavior proceed to a second-order screen and then to the pilot
mesh.

`analyze_screening.py` applies the fast-screen physics audit and writes
`screening_summary.json` plus `screening_wall_profiles.png`. A screening pass
still has `training_eligible=false`; only a converged pilot/medium/fine campaign
can produce accepted ML labels.
