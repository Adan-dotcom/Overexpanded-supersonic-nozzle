# Assumptions and evidence

## Published or measured basis

- DLR-PAR is a thrust-optimized parabolic nozzle with published cold gaseous-
  nitrogen separation measurements.
- Public NASA LOX/CH4 tests provide a representative chamber-pressure and O/F
  envelope, but use different hardware.
- `DLR_PAR_full_contour.csv` is a user-supplied reconstruction, not certified
  official CAD.
- The reconstruction matches the published 20 mm throat, area ratio 30 and
  rounded 34/10 degree wall-angle controls; the full contour is still not
  certified.
- NASA/MSFC report 20100017649 describes a different PAR article using heated
  air in a vacuum chamber. Its transition NPRs are not DLR/N2 measurements.

## Derived quantities

- `T0` and composition come from NASA CEA for each `Pc` and O/F.
- NPR is always `Pc/Pa`.
- Mass flow and thrust are solver outputs, not imposed from another engine.
- Separation is a persistent downstream wall-shear sign reversal; the maximum
  wall-pressure gradient is stored separately as shock location.

## Synthetic choices

- Combining DLR-PAR geometry and NASA methalox conditions creates a synthetic
  methodology case, not a Raptor replica.
- Axisymmetric RANS/URANS cannot establish asymmetric side-load behavior.
- Wall thermal treatment, turbulence and chemistry are model uncertainties.
- One geometry cannot support arbitrary-geometry generalization claims.

## Evidence hierarchy

1. Experimental measurements.
2. Validated, conservation- and discretization-qualified CFD.
3. Screening CFD used only for model selection.
4. Smoke/install tests, which provide no physical labels.
5. Virtual sensor/noise samples derived from an accepted CFD case.

The neural network will initially approximate accepted CFD, not nature. Final
claims require experimental validation and uncertainty reporting.
