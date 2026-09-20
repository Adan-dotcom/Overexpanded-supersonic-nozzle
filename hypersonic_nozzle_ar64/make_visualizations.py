from pathlib import Path

import matplotlib.pyplot as plt
from paraview.simple import (
    ColorBy,
    GetActiveViewOrCreate,
    GetColorTransferFunction,
    GetScalarBar,
    LegacyVTKReader,
    ResetCamera,
    SaveScreenshot,
    SaveState,
    Show,
    Text,
    _DisableFirstRenderCameraReset,
)

from find_separation import centerline_analysis, wall_analysis


ROOT = Path(__file__).resolve().parent
SEPARATION_X = 0.12129721
REATTACHMENT_X = 0.14849716
SHOCK_X = 0.16227275


def plot_wall_cf() -> None:
    wall, separations, reattachments = wall_analysis()
    x = [row["x"] for row in wall]
    cf = [row["cf_t"] for row in wall]
    separation = separations[0] if separations else SEPARATION_X
    reattachment = reattachments[0] if reattachments else REATTACHMENT_X

    fig, ax = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.axvspan(separation, reattachment, color="#e45756", alpha=0.18, label="Flujo separado")
    ax.plot(x, cf, color="#146c94", linewidth=1.8, label=r"$C_{f,t}$ en pared")
    ax.axvline(separation, color="#c1121f", linestyle="--", linewidth=1.4, label=f"Separacion: {separation:.4f} m")
    ax.axvline(reattachment, color="#2a9d8f", linestyle="--", linewidth=1.4, label=f"Readherencia: {reattachment:.4f} m")
    ax.set_xlim(0.0, 0.2)
    ax.set_xlabel("x desde la garganta [m]")
    ax.set_ylabel(r"Coeficiente de friccion tangencial $C_{f,t}$")
    ax.set_title("Desprendimiento de la capa limite")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.savefig(ROOT / "cf_separation.png", dpi=180)
    plt.close(fig)


def plot_centerline() -> None:
    centerline, shock, _ = centerline_analysis()
    nozzle = [row for row in centerline if 0.0 <= row["x"] <= 0.2]
    x = [row["x"] for row in nozzle]
    mach = [row["mach"] for row in nozzle]
    pressure_kpa = [row["pressure"] / 1000.0 for row in nozzle]

    fig, left = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
    right = left.twinx()
    mach_line = left.plot(x, mach, color="#146c94", linewidth=2.0, label="Mach sobre el eje")
    pressure_line = right.plot(x, pressure_kpa, color="#d1495b", linewidth=1.8, label="Presion sobre el eje")
    left.axvline(shock["x"], color="#6c757d", linestyle="--", linewidth=1.4, label=f"Choque: {shock['x']:.4f} m")
    left.axvspan(SEPARATION_X, REATTACHMENT_X, color="#e45756", alpha=0.14)
    left.set_xlim(0.0, 0.2)
    left.set_xlabel("x desde la garganta [m]")
    left.set_ylabel("Mach", color="#146c94")
    right.set_ylabel("Presion estatica [kPa]", color="#d1495b")
    left.set_title("Perfil central y posicion del choque")
    left.grid(True, alpha=0.25)
    lines = mach_line + pressure_line + [left.lines[-1]]
    left.legend(lines, [line.get_label() for line in lines], loc="best")
    fig.savefig(ROOT / "centerline_profiles.png", dpi=180)
    plt.close(fig)


def paraview_outputs() -> None:
    _DisableFirstRenderCameraReset()
    flow = LegacyVTKReader(registrationName="Flujo SU2", FileNames=[str(ROOT / "flow.vtk")])
    wall = LegacyVTKReader(registrationName="Pared", FileNames=[str(ROOT / "wall.vtk")])
    view = GetActiveViewOrCreate("RenderView")
    view.ViewSize = [1500, 760]
    view.UseColorPaletteForBackground = 0
    view.Background = [1.0, 1.0, 1.0]
    view.OrientationAxesVisibility = 1
    view.CameraParallelProjection = 1

    flow_display = Show(flow, view, "UnstructuredGridRepresentation")
    flow_display.Representation = "Surface"
    wall_display = Show(wall, view, "UnstructuredGridRepresentation")
    wall_display.Representation = "Surface"
    wall_display.AmbientColor = [0.05, 0.05, 0.05]
    wall_display.DiffuseColor = [0.05, 0.05, 0.05]
    wall_display.LineWidth = 2.0

    summary = Text(registrationName="Resultado")
    summary.Text = "Mmax = 5.46    x_sep = 0.121 m    x_reatt = 0.148 m    x_shock = 0.162 m"
    summary_display = Show(summary, view)
    summary_display.WindowLocation = "Upper Center"
    summary_display.FontSize = 18
    summary_display.Color = [0.05, 0.05, 0.05]

    ColorBy(flow_display, ("POINTS", "Mach"))
    mach_lut = GetColorTransferFunction("Mach")
    mach_lut.ApplyPreset("Viridis", True)
    mach_lut.RescaleTransferFunction(0.0, 6.3)
    flow_display.SetScalarBarVisibility(view, True)
    mach_bar = GetScalarBar(mach_lut, view)
    mach_bar.TitleColor = [0.0, 0.0, 0.0]
    mach_bar.LabelColor = [0.0, 0.0, 0.0]
    ResetCamera(view)
    view.CameraPosition = [0.18, 0.035, 1.0]
    view.CameraFocalPoint = [0.18, 0.035, 0.0]
    view.CameraParallelScale = 0.12
    SaveScreenshot(str(ROOT / "mach_contour.png"), view, ImageResolution=[1500, 760])

    ColorBy(flow_display, ("POINTS", "Pressure"))
    pressure_lut = GetColorTransferFunction("Pressure")
    pressure_lut.ApplyPreset("Cool to Warm", True)
    pressure_lut.RescaleTransferFunction(500.0, 2_000_000.0)
    pressure_lut.MapControlPointsToLogSpace()
    pressure_lut.UseLogScale = 1
    flow_display.SetScalarBarVisibility(view, True)
    pressure_bar = GetScalarBar(pressure_lut, view)
    pressure_bar.TitleColor = [0.0, 0.0, 0.0]
    pressure_bar.LabelColor = [0.0, 0.0, 0.0]
    SaveScreenshot(str(ROOT / "pressure_contour.png"), view, ImageResolution=[1500, 760])

    ColorBy(flow_display, ("POINTS", "Mach"))
    flow_display.SetScalarBarVisibility(view, True)
    SaveState(str(ROOT / "nozzle_results.pvsm"))


if __name__ == "__main__":
    plot_wall_cf()
    plot_centerline()
    paraview_outputs()
    print(f"Visualizations written to {ROOT}")
