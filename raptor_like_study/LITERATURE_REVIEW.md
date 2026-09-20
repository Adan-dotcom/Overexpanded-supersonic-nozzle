# Literature review: nozzle separation and sparse sensing

## Directly relevant nozzle evidence

### DLR-PAR experiment

Verma and Haidn studied restricted shock separation in a thrust-optimized
parabolic nozzle with area ratio 30. The work includes fast wall-pressure
transducers and distinguishes free shock separation (FSS), restricted shock
separation (RSS), reattachment, and time-dependent switching.

- DOI: https://doi.org/10.2514/1.42351
- Relevance: validates the geometry family, pressure observables, and the need
  to store shock, separation, and reattachment as different quantities.
- Limitation for this project: cold gaseous-nitrogen experiment, not LOX/CH4.

NASA's nozzle side-load review summarizes PAR pressure profiles across NPR and
reports FSS below approximately 23.8, RSS through much of the intermediate NPR
range, a return to FSS above approximately 57.2, and full flow near NPR 65.

- Public report: https://ntrs.nasa.gov/api/citations/20100017649/downloads/20100017649.pdf
- Relevance: the proposed NPR 20-100 sweep crosses multiple physical regimes;
  a single smooth regression target is insufficient without regime labels.

### Turbulence-model uncertainty

Allamaprabhu et al. compared SA and SST against experimental separation data
for DLR-PAR and other nozzles. Standard models did not predict every nozzle and
NPR consistently, and adjusted SST coefficients were explored.

- DOI: https://doi.org/10.1016/j.ast.2015.12.016
- Relevance: SST cannot be designated truth. Model-form sensitivity and
  experimental comparison are mandatory.
- Warning: tuning coefficients on the same cases used for evaluation would
  contaminate validation.

### Methane chemistry

Zhukov compared frozen, equilibrium, and finite-rate methane/oxygen nozzle
models. Frozen expansion was inaccurate; equilibrium could be acceptable, but
finite-rate effects became more important with expansion.

- DOI: https://doi.org/10.1016/j.actaastro.2019.01.001
- Relevance: equilibrium is a defensible primary screening model, not a proven
  universal model for this nozzle. Frozen and preferably finite-rate bounds are
  needed for final claims.

The 2024 Space Propulsion study by Grossi et al. reports finite-rate chemistry
closest to nominal performance and similar equilibrium/finite-rate results for
a high-pressure Raptor reference, while also finding sensitivity to engine
size, chamber pressure, and expansion ratio.

- Record: https://hdl.handle.net/11573/1750290
- Relevance: it supports a sensitivity study; it does not turn the present
  synthetic DLR-PAR case into a Raptor simulation.

### Methalox operating reference

NASA's LLAMA/HR-1 campaign reports a real 7 klbf LOX/CH4 thrust chamber with
steady chamber pressure near 750 psig and mixture ratio near 3.2.

- Public paper: https://ntrs.nasa.gov/api/citations/20210018424/downloads/AIAA_Process-Dev-Hotfire_NASA%20HR-1_2021.pdf
- Relevance: supports the nominal Pc and O/F scale.
- Limitation: different chamber, injector, cooling, throat, contour, and
  instrumentation. It supplies an operating reference, not validation data for
  the DLR-PAR geometry.

## Sparse sensing evidence

Manohar et al. use SVD/POD features and pivoted QR to select sparse measurement
locations tailored to known data patterns.

- DOI: https://doi.org/10.1109/MCS.2018.2810460
- Open preprint: https://arxiv.org/abs/1701.07569
- Relevance: POD-QR is a strong non-neural baseline and should be fitted only
  on training CFD cases. Its selected locations must then be frozen before
  validation and testing.

The DLR-PAR experiment itself demonstrates why pressure sensors are useful:
pressure signals change as the separation shock crosses a transducer, and RSS
produces distinct downstream pressure behavior. It does not establish that a
particular number of sensors is sufficient for the present hot-gas dataset.

## Instrument evidence

Kulite's HEM-375 data sheet lists ranges including 17/35/70 bar, maximum error
of 0.5% FSO, operation to 193 C, and natural frequency above 400 kHz without a
screen.

- Official sheet: https://kulite.com/assets/media/2021/01/HEM-375-CO.pdf
- Implication: range selection matters. At 70 bar, 0.5% FSO is 0.35 bar. The
  installed screen/cavity/thermal protection response must be characterized;
  the bare-sensor frequency cannot simply be imposed as system bandwidth.

## Literature-access policy

Public NASA/DLR reports, open papers, preprints, DOI metadata, and author-posted
manuscripts can be reviewed directly. For paywalled papers, only the accessible
abstract/metadata can be used unless the user supplies a PDF or an accessible
repository copy. Every important project claim should point to the exact source
and page/figure once the full paper is available.
