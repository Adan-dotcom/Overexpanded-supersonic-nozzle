import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "npr20_hybrid_fine"))
from diagnose_temperature_overshoot import read_points_and_arrays  # noqa: E402


source = HERE / "flow_npr20_cfl2_inner30_from500_00520.vtk"
points, arrays = read_points_and_arrays(source)
mask = (
    (np.abs(points[:, 1]) < 1e-10)
    & (points[:, 0] >= 0.0)
    & (points[:, 0] <= 0.12502)
    & (arrays["Velocity"][:, 0] > 1.0)
)
x = points[mask, 0]
u = arrays["Velocity"][mask, 0]
order = np.argsort(x)
x, u = x[order], u[order]
x, unique = np.unique(x, return_index=True)
u = u[unique]

transit_s = float(np.trapz(1.0 / u, x))
result = {
    "source": source.name,
    "path": "axis from throat to nozzle exit",
    "point_count": int(x.size),
    "minimum_axial_velocity_m_s": float(np.min(u)),
    "maximum_axial_velocity_m_s": float(np.max(u)),
    "integral_dx_over_ux_us": 1e6 * transit_s,
    "one_transit_target_time_from_initialization_us": 25.0 + 1e6 * transit_s,
    "target_iteration_at_dt_0p025us": int(np.ceil(100 + transit_s / 2.5e-8)),
}
(HERE / "flow_timescale.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
print(json.dumps(result, indent=2))
