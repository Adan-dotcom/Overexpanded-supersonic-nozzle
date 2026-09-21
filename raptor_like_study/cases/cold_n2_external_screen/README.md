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

Run one case into an external artifact directory with:

```bash
source /home/adan/eilmer-screen-venv/bin/activate
bash run_case.sh 1 35 /home/adan/eilmer-artifacts/cold-n2-external-screen/stage1 0.001
```

All run metadata and audits retain `physics_accepted=false` and
`training_eligible=false`. Heavy `lmrsim`, VTK and solver logs stay outside
Git under `/home/adan/eilmer-artifacts/`.
