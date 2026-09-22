# cold_n2_external_screen

This is a separate provisional N2 external-plume screen. It is not a copy of
the failed internal-domain cold-N2 case and is not an experimental DLR match.

The topology follows the installed Eilmer v5 `underexpanded-jet` example:
axisymmetric reservoir/nozzle, an exterior ambient region beginning at the
nozzle lip, `InOutFlowBC_Ambient` on the far-field boundary, and
`OutFlowBC_Simple` downstream. The nozzle exit is an internal grid connection;
there is no fixed-pressure plane at that exit.

Stages are deliberately incremental:

1. inviscid N2 transient with the official underexpanded-jet controls;
2. laminar viscosity and no-slip adiabatic wall, using the official Hakkinen
   transient controls;
3. `k_log_omega`, wall temperature 300 K, and Mabey's official turbulence
   initialization (`k` from intensity and `omega=rho*k/mu_t`, stored as
   `log(omega)`);
4. steady acceleration is only a consideration from a saved transient using
   the official `FlowSolution` restart pattern. It is not enabled by default.

The wall-resolution family is generated with:

```bash
bash prepare_wall_mesh_family.sh /home/adan/eilmer-artifacts/cold-n2-wall-mesh-family
```

It defines `wall-coarse`, `wall-medium` and `wall-fine` with 112, 136 and 160
wall-normal cells. `audit_wall_mesh.py` checks the generated first-cell sizes
and positive cell areas. The flow gate currently fails on the coarse mesh, so
the smaller meshes are not automatically launched.

The official-example and minimal steady-crash diagnostic ladder can be left in
a persistent terminal with:

```bash
tmux new-session -d -s eilmer-overnight \
  "bash run_overnight_diagnostics.sh /home/adan/eilmer-artifacts/overnight-eilmer-diagnostics"
```

It retains per-step logs and `status.tsv`, enforces a 60-minute limit per CFD
run, and builds a separate debug installation plus MPI backtrace if a
segmentation fault is reproduced. It never replaces the optimized install.

`run_overnight_fallback.sh` may be queued in a second tmux session. It waits
for the primary campaign, then runs the official Busemann coarse-to-fine
`FlowSolution` continuation, any matrix cases not already passed, and a
real-versus-complex Frechet diagnostic for crashing prepared cases.

Run one case into an external artifact directory with:

```bash
source /home/adan/eilmer-screen-venv/bin/activate
bash run_case.sh 1 35 /home/adan/eilmer-artifacts/cold-n2-external-screen/stage1 0.001
```

All run metadata and audits retain `physics_accepted=false` and
`training_eligible=false`. Heavy `lmrsim`, VTK and solver logs stay outside
Git under `/home/adan/eilmer-artifacts/`.
