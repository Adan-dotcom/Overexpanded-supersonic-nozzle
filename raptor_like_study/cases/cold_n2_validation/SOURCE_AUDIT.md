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

The user supplied the full 12-page article PDF.  Its SHA-256 is
`f1d05035c7c39e2a589d827fd9461b2eaba0e763cd2e915a1f44cbd0649e1b73`.
The PDF retains vector paths for the quantitative plots, so the primary
targets were extracted without raster tracing:

- Fig. 3a: 65 startup mean-wall-pressure points at NPR 30, 33, 35, 37 and 40;
- Fig. 7a: 31 startup/shutdown physical-separation points from the oil study;
- Fig. 7b: 23 startup/shutdown incipient-pressure points;
- Fig. 11a: 125 shutdown mean-wall-pressure points at NPR 33 through 16.

The extractor, CSVs and provenance are committed in this directory and its
`results/` subdirectory.  The extractor validates the PDF hash, vector-series
counts and point counts.  Reported sensor coordinates in the article are
retained as a separate text crosscheck because the article itself prints
transducer 10 as both `X/rt = 9.734` and `9.735`.

The CSV uncertainty columns distinguish graphical digitization uncertainty
from experimental uncertainty.  The former is conservatively calculated from
half the plotted stroke width mapped through each axis.  The latter is left
blank: the paper gives the transducer manufacturer's 0.5% statement but does
not provide a complete uncertainty analysis, numeric `Pa` for normalization,
or uncertainty for the oil-derived line.

Primary source links:

- <https://doi.org/10.2514/1.42351>
- <https://elib.dlr.de/59893/>
- <https://www.researchgate.net/publication/225002719_Study_of_Restricted_Shock_Separation_Phenomena_in_a_Thrust_Optimized_Parabolic_Nozzle>

## Absolute-condition crosscheck

Two primary DLR dissertations were also checked for the missing dimensional
conditions.  Frey's facility appendix confirms gaseous nitrogen nominally at
room temperature and explains that an open chamber remains at ambient pressure,
but it does not provide the run-specific numeric `T0` or `Pa` for the later
Verma--Haidn campaign.  Stark's dissertation describes the same P6.2 supply and
horizontal stand and, importantly, states that blowdown lowers total temperature
continuously during a test.  It also documents transient wall temperatures and
possible nitrogen condensation in related TOP tests.

Consequently, neither `T0 = 300 K`, `Pa = 1 bar` nor an adiabatic wall is adopted
silently.  "Room temperature" and "atmospheric pressure" are qualitative source
statements, not substitutes for the missing run logs.  The companion PDFs remain
outside Git in the literature artifact directory with these hashes:

| Source | SHA-256 |
|---|---|
| Frey dissertation (2001) | `f1578ab28b22aeb07b3c6d1c44a3d1f4bb966733c4e1d9cced28f67a2956990a` |
| Stark dissertation (2010) | `872cf1e9a1c4e646f07e816ff44c90e92ee035b1d16efe699f4339999f099247` |

Primary links:

- <https://elib.uni-stuttgart.de/server/api/core/bitstreams/14c94d72-63c9-4356-accf-8daf9f93d403/content>
- <https://elib.dlr.de/69234/1/DissertationRalfStark.pdf>

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

## Still missing before a matched DLR validation run

- Numeric stagnation temperature for each selected run.
- Numeric atmospheric pressure for each selected run (or the logged `P0` and
  `Pa` pair), not merely the ratio.
- Experimental uncertainty for the oil-derived physical separation position.
- Documented wall temperature or a justified thermal sensitivity bracket.
- Inlet turbulence quantities or a declared sensitivity range.

Until these are supplied or recovered, no CFD run can be called a matched
DLR experiment and no error tolerance may be fitted after seeing CFD.
