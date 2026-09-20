# Assumptions and evidence audit

This file separates measurements, published inputs, user-supplied data,
derived quantities, and modeling choices. CFD and ML outputs are not
experimental truth.

## What is physically measured or published

- The DLR-PAR is a thrust-optimized parabolic nozzle with area ratio 30 and
  published cold-gas separation measurements. The original campaign used
  gaseous nitrogen, not hot LOX/CH4 products.
- Published PAR data show distinct FSS/RSS regimes as NPR changes. NASA's
  nozzle side-load review reports FSS up to about NPR 23.7, RSS beginning near
  23.8, a return to FSS above about 57.2, and full flow near NPR 65.
- NASA LLAMA/HR-1 hot-fire work provides a real LOX/CH4 operating reference:
  the 7 klbf campaign reports approximately 750 psig chamber pressure and
  mixture ratio near 3.2. That hardware does not use the DLR-PAR contour.
- The Kulite HEM-375 data sheet supports the stated 70 bar range, maximum
  0.5% FSO error, temperature limit of 193 C, and greater-than-400 kHz natural
  frequency without a screen. It does not prove survival or bandwidth in this
  nozzle installation.

Primary/public references:

- NASA nozzle side-load review: https://ntrs.nasa.gov/api/citations/20100017649/downloads/20100017649.pdf
- DLR-PAR restricted-shock-separation experiment: https://doi.org/10.2514/1.42351
- Turbulence-model sensitivity for DLR-PAR: https://doi.org/10.1016/j.ast.2015.12.016
- NASA LLAMA/HR-1 hot-fire paper: https://ntrs.nasa.gov/api/citations/20210018424/downloads/AIAA_Process-Dev-Hotfire_NASA%20HR-1_2021.pdf
- Methane nozzle kinetics comparison: https://doi.org/10.1016/j.actaastro.2019.01.001
- Kulite HEM-375 data sheet: https://kulite.com/assets/media/2021/01/HEM-375-CO.pdf

## User-supplied but not independently certified

- `DLR_PAR_full_contour.csv` is the working geometry. Its provenance says it
  was reconstructed from Frey's dissertation. It has not been compared point
  by point with an official CAD file.
- The study objective is sparse wall-pressure sensing of separation location.
- The intended propellants are LOX/LCH4.

## Derived, not independently sampled

- Chamber temperature is calculated from the thermochemical model for each
  pressure and O/F; it is not an independent input.
- In the corrected hot-fire campaign, NPR is `Pc/Pa`; `Pc` and physically
  bounded `Pa` are sampled, and NPR is not an independent random variable.
- Mass flow and thrust are outputs of the choked nozzle solution. The NASA
  7 klbf thrust is not imposed on the much smaller DLR throat.
- `x_sep` is extracted from persistent wall-shear sign reversal. `x_shock` is
  a separate wall-pressure-gradient feature.

## Synthetic modeling choices

- Combining the DLR-PAR contour with NASA methalox chamber conditions creates
  a synthetic nozzle. It is neither the DLR nitrogen experiment nor a NASA or
  SpaceX engine.
- The present chamber-pressure range `5.1-5.4 MPa` and nominal O/F `3.2` are
  consistent with the NASA LLAMA reference. The upper O/F `3.6` is a study
  extension, not established as part of that same LLAMA test envelope.
- The nominal hot-fire campaign uses `Pa=50-101.325 kPa`, which implies roughly
  `NPR=50-108` over `Pc=5.1-5.4 MPa`. The separate one-atmosphere throttling
  campaign reaches roughly `NPR=20-53`; operation below `Pc=5.1 MPa` is an
  explicitly exploratory startup/throttling extension.
- `Pc=5.2 MPa, NPR=20` implies `Pa=260 kPa`. It is meaningful only for a
  pressurized test chamber and is not an open-atmosphere operating point.
- Axisymmetric RANS can estimate a mean axial separation location but cannot
  reproduce asymmetric separation, circumferential side loads, or stochastic
  switching around the circumference.
- SST and SA are model-form alternatives, not truth. Published DLR-PAR work
  shows that separation prediction is sensitive to turbulence modeling.
- An adiabatic wall avoids inventing cooling-channel data, but it is not a
  regeneratively cooled rocket wall. Wall temperature can change viscosity,
  boundary-layer thickness, and separation.
- A uniform equilibrium-products inlet assumes complete mixing and ignores
  injector/chamber nonuniformity and the incoming chamber boundary layer.
- The equilibrium LUT assumes instantaneous chemical equilibration. Frozen
  and finite-rate chemistry can differ, especially at large expansion ratios.
- The current LUT transport remains a Sutherland/constant-Prandtl surrogate.
- The internal-only screen retained a supersonic exit near `18-21 kPa` while a
  `260 kPa` outlet was requested. It cannot rank separation models from the
  quasi-1D supersonic seed because the missing plume does not establish the
  backpressure-driven shock.
- The nozzle-plus-plume LUT feasibility test represents the exterior with cold
  equilibrium products because one SU2 data-driven fluid is active throughout
  the zone. It demonstrates software coupling, not a final products/air model.

## Data and ML truth hierarchy

1. Experimental pressure/schlieren/shear data: physical validation evidence.
2. Grid-, time-, model-, and conservation-qualified CFD: numerical reference.
3. Screening CFD: model-selection evidence only.
4. Smoke tests, unconverged runs, and failed thermal gates: no labels.
5. Virtual sensor samples and their noise realizations: derived from a CFD
   case; they are not additional independent flow cases.

The neural network will initially learn a surrogate of accepted CFD, not a
surrogate of nature. Experimental validation is required before calling its
predictions physically validated.

## Current claim mismatches to fix

- With only `DLR_PAR` in `geometry.variants`, the model can generalize over
  operating conditions for one contour. It cannot claim prediction for an
  arbitrary input geometry. That requires multiple systematically varied
  contours and geometry descriptors.
- A 70 bar sensor has up to 0.35 bar error at 0.5% FSO. This may overwhelm
  low downstream wall-pressure signatures. Sensor range must be optimized by
  station or the study must compare 17/35/70 bar ranges.
- The greater-than-400 kHz figure is for the bare sensor without a screen.
  Installed bandwidth depends on screen, cavity, tubing, mounting, thermal
  protection, signal conditioning, and anti-alias filtering.
- A random 70/15/15 split of 100 CFD cases leaves only 15 independent test
  conditions. Use grouped nested cross-validation and an extrapolation test,
  keeping every sensor/noise realization from one CFD case in one fold.

## Fast-screening policy

- Internal `screen`: 600 x 128, 76,800 cells. Use for startup stability,
  conservation, LUT coverage, and runtime only; do not use it to reject a
  model for absence of separation from a supersonic quasi-1D seed.
- Hybrid plume screen: use for gross shock/separation behavior, but its
  single-LUT exterior remains a model-form sensitivity until air/products
  treatment is justified.
- `pilot`: 800 x 128. Re-run only surviving models and check that rankings and
  qualitative behavior persist.
- `medium` and `fine`: use only for finalists and formal discretization error.
- Reject a screen candidate for divergence, LUT-hull excursions, energy
  nonconservation, or nonphysical states. Judge shock/separation only on a
  domain and initialization capable of transmitting ambient backpressure. Do
  not rank candidates by sub-cell differences in `x_sep`.
