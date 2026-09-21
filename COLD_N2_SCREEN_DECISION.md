# Cold-N2 screen decision

Decision: **NO_GO**

This decision applies only to numerical readiness of the provisional
DLR-PAR/N2 Eilmer workflow. It is not an experimental-validation decision and
produces no ML labels.

## Executed gate

The required baseline was attempted on the six-block coarse mesh (51,840
cells) with startup metadata, Pa=100,000 Pa, NPR=35, derived P0=3,500,000 Pa,
T0=295 K, fixed 300 K wall, turbulence intensity 0.01 and length scale 0.001 m.

| Run | Elapsed upper bound | Result | Residual | x_sep | x_shock | y+ | Mass/energy |
|---|---:|---|---|---|---|---|---|
| baseline coarse, attempt 1 | 5.1 s | exit 136; floating-point divide-by-zero in `decompILU0` at Newton step 1 | initial global relative residual 1.0; no completed iteration | unavailable | unavailable | unavailable | unavailable |
| baseline coarse, attempt 2 | 16.7 s | same exit and failure signature after the one permitted adjustment | initial global relative residual 1.0; no completed iteration | unavailable | unavailable | unavailable | unavailable |

Attempt 2 changed only numerical controls: `extrema_clipping=false`, ILU fill
1, diagonal perturbation 1e-30 and equation scaling. The identical zero-pivot
failure persisted before a nonlinear iteration completed. Neither attempt
produced VTK, a wall profile, a final state audit, or mass/energy balances.
Both failure records explicitly retain `physics_accepted=false` and
`training_eligible=false`.

Heavy evidence is retained at:

- `/home/adan/eilmer-artifacts/cold-n2-screen-20260921/baseline-coarse-attempt1`
- `/home/adan/eilmer-artifacts/cold-n2-screen-20260921/baseline-coarse-attempt2`

The solver-log SHA-256 values are respectively
`797e0799da6ec365b4c42699f73711f702bbeee2c75c702850ac3cde1d0721d2`
and `2532acb66bf79fd5897d8b11d6554b9ec2f8fa89a4d136edcd94ebb36d94fc64`.

## Gated runs

Medium baseline, startup NPR 30/33/37/40, and all eleven medium-mesh OFAT
perturbations were not launched. The prescribed design requires a healthy
coarse baseline first, and the repeated step-1 preconditioner failure makes
those cases unsafe repetitions rather than independent evidence. Shutdown was
also not launched because physical descending continuation/restart is not yet
implemented.

## Required correction

The cold-N2 workflow must first eliminate the singular steady Newton
preconditioner path. The next engineering step is a separately qualified
transient initialization or continuation/restart into steady RANS, followed by
one fresh coarse-baseline gate. The failed baseline provides no basis for mesh
comparison, NPR robustness, sensitivity quantification, or a hot-gas screen.

LOX/CH4 screening remains disabled.
