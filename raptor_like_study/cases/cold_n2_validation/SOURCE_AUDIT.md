# Cold-N2 source audit

Audited: 2026-09-21 UTC

## Eligible target campaign

The target is the DLR Lampoldshausen P6.2 horizontal-test-bench campaign
reported by S. B. Verma and O. Haidn, *Study of Restricted Shock Separation
Phenomena in a Thrust Optimized Parabolic Nozzle*, Journal of Propulsion and
Power 25(5), 1046-1057 (2009), DOI `10.2514/1.42351`.

The primary article reports:

- dry gaseous nitrogen at ambient temperature;
- discharge into atmospheric pressure on the horizontal bench, not the
  high-altitude chamber;
- NPR varied through stagnation pressure `P0`;
- throat diameter 20 mm and area ratio 30;
- 13 axial wall-pressure locations at 8 mm pitch plus four added points;
- Kulite XT-140M sensors, 0-1 bar range, manufacturer accuracy within 0.5%,
  1 kHz acquisition and 160 Hz low-pass cutoff for the axial line;
- held mean-pressure profiles at startup NPR 30, 33, 35, 37 and 40;
- an FSS-to-partially-formed-RSS transition between approximately NPR 33 and
  35, pRSS at 35-37, and the end-effect return to FSS near NPR 38;
- fully formed RSS first observed near NPR 34 during shutdown in the reported
  campaign.

The article calls the pressure-jump location `X_inc` (incipient separation),
while the physical separation `X_sep` comes from oil-pigment accumulation.
The CFD definitions must preserve this distinction; wall-pressure shock
location is not automatically the wall-shear separation location.

The full-text landing page is public through the author upload, but the binary
PDF was not available to the automated fetch used here.  The indexed text is
sufficient to audit the statements above but not to digitize the plotted
curves at defensible resolution.

Primary source links:

- <https://doi.org/10.2514/1.42351>
- <https://elib.dlr.de/59893/>
- <https://www.researchgate.net/publication/225002719_Study_of_Restricted_Shock_Separation_Phenomena_in_a_Thrust_Optimized_Parabolic_Nozzle>

## Geometry corroboration

The same DLR nozzle is described in S. B. Verma and O. Haidn, *Cold Gas
Testing of Thrust-Optimized Parabolic Nozzle in a High-Altitude Test
Facility*, DOI `10.2514/1.B34320`.  It reports a 20 mm throat, area ratio 30, a 34 degree wall angle
downstream of the throat circular arc and a 10 degree exit angle.  The tracked
CSV agrees with those rounded scalar controls within 0.08 degree and exactly
matches the throat/area controls; see `results/geometry_source_crosscheck.json`.

This is partial corroboration, not full-contour certification.  The source
does not tabulate every wall coordinate.

## Rejected validation source

NASA report `20100017649`, *Nozzle Side Load Testing and Analysis at Marshall
Space Flight Center*, was previously cited as the source for the planned NPR
23.8/57.2 transition targets.  Its Figures 11 and 12 belong to a different
MSFC PAR test article:

| Attribute | DLR target | NASA/MSFC PAR |
|---|---:|---:|
| Working gas | dry N2 | heated dry air |
| Throat diameter | 20 mm | 38.1 mm |
| Area ratio | 30 | 30.5 |
| Initial divergent angle | 34 deg after throat arc | 40 deg |
| Environment | atmospheric horizontal bench | vacuum chamber |
| Typical total temperature | stated only as ambient | 66 degC |

The NASA curves remain useful evidence about a different PAR nozzle, but they
are ineligible as quantitative anchors or transition thresholds for this DLR
validation.  The downloaded report is retained only in the external literature
artifact directory with SHA-256
`23a193a093ed3b5453dc8a06fe84f43b59ffb037d33c1102421349e70c0d10a2`.

NASA source:
<https://ntrs.nasa.gov/api/citations/20100017649/downloads/20100017649.pdf>

## Secondary CFD source

Nedjari, Benarous and Benazza (2023) report a numerical case at NPR 25.25
using 25.25 bar and 283 K nitrogen with 1 bar, 270 K ambient.  Those numbers
are useful for reproducing their numerical comparison, but they are not
substituted here for missing primary measurements from the Verma-Haidn test.

Source: <https://rmf.smf.mx/ojs/index.php/rmf/article/download/6154/6644/21790>

## Missing before a DLR validation run

- A high-resolution copy of the target DLR figures or tabulated wall-pressure
  data, with exact sensor abscissae.
- Numeric stagnation temperature for each selected run.
- Numeric atmospheric pressure for each selected run (or the logged `P0` and
  `Pa` pair), not merely the ratio.
- Experimental uncertainty for the oil-derived physical separation position.
- Documented wall temperature or a justified thermal sensitivity bracket.
- Inlet turbulence quantities or a declared sensitivity range.

Until these are supplied or recovered, no CFD run can be called a matched
DLR experiment and no error tolerance may be fitted after seeing CFD.
