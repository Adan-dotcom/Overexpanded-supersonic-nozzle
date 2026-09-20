# Sensor-minimum study for separated supersonic nozzles

This folder defines the information needed to automate the paper study. The
neural network must predict a CFD/experimental separation label from sparse
sensor measurements, not from the full CFD field. The full CFD solution is the
reference truth; synthetic sensors are sampled from it and corrupted with the
specified noise, bandwidth and placement constraints.

## Required inputs from the researcher

1. **Geometry**: nozzle wall profile as `x,r` in metres, throat location, axis
   convention, and an identifier for each geometry.
2. **Operating envelope**: chamber or reservoir pressure and temperature, back
   pressure, mass flow or thrust if available, and the range of each quantity.
3. **Gas state**: cold-flow gas, or propellant pair and mixture ratio. For a
   hot-fire LOX/CH4 nozzle provide whether the inlet state comes from CEA
   equilibrium, frozen chemistry, finite-rate chemistry, or measured chamber
   data. CEA composition is preferable to guessing air properties.
4. **Wall/thermal model**: adiabatic, fixed wall temperature, measured wall
   temperature, or conjugate heat transfer; include material and emissivity if
   radiation matters.
5. **Sensor definition**: sensor type, allowable axial/radial locations,
   pressure/temperature range, bandwidth, sampling rate, resolution, noise and
   whether sensors are flush-mounted or intrusive.
6. **Ground truth policy**: separation location from wall `Cf_t=0`, pressure
   plateau/shock location, measured oil-flow result, or another definition.

## Templates

- `experiment_spec.template.yaml` contains the physical and numerical study
  inputs.
- `sensor_layouts.template.csv` contains candidate transducer locations and
  measurement models.

The automation will produce one case-level row per operating point and sensor
layout. The train/test split must hold out complete geometries or operating
conditions; random splitting individual sensor samples would leak information.

## Recommended first campaign

Start with one axisymmetric idealized geometry and hot-gas effective properties
from CEA, then vary chamber pressure, back pressure, area ratio and wall
temperature. Compare equilibrium and frozen CEA states. Use wall pressure as
the first sensor family, then add wall temperature/heat flux only if they are
physically available. Run coarse/medium/fine meshes and accept a separation
label only after mesh and residual checks pass.
