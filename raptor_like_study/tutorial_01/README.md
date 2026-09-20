# Tutorial 01: una tobera completa, paso a paso

Este ejercicio es deliberadamente sencillo: aire perfecto, `gamma=1.4`,
`R=287.058`, `P0=2 MPa`, `T0=600 K` y `pb=75 kPa`. No es todavía el modelo
LOX/CH4 del estudio de investigación.

## 1. Crear la malla y la configuración

Desde PowerShell:

```powershell
cd "D:\PRUEBA SU2_2026\raptor_like_study\tutorial_01"
python .\make_case.py --level coarse --solver euler
```

Esto crea `runs/euler_coarse/mesh.su2` y `nozzle.cfg`. La geometría se lee de
`geometry.csv`; `x` es la coordenada axial y `r` el radio. La malla tiene
cuadriláteros estructurados. El refinamiento radial se concentra en la pared.

## 2. Ejecutar SU2

```powershell
wsl.exe -d Ubuntu -- bash -lc "cd '/mnt/d/PRUEBA SU2_2026/raptor_like_study/tutorial_01/runs/euler_coarse' && OMPI_MCA_osc=pt2pt /mnt/d/SU2/v8.5.0/bin/SU2_CFD nozzle.cfg"
```

Al terminar aparecen `history.csv`, `flow.vtk`, `wall.vtk` y `wall.csv`.

## 3. Graficar con Python

```powershell
python .\plot_results.py .\runs\euler_coarse
```

Esto genera `convergence.png` y `wall_pressure.png`. Matplotlib es suficiente
para gráficas de variables sobre una línea o una superficie.

## 4. Comparar mallas

```powershell
python .\make_case.py --level medium --solver euler
python .\make_case.py --level fine --solver euler
```

La malla gruesa, media y fina sirven para comprobar independencia de malla.
No debemos reportar `x_sep` ni presiones como resultados finales hasta que la
solución esté convergida y el cambio entre mallas sea pequeño.

## Qué hace ParaView

ParaView abre `flow.vtk` y permite ver el campo completo: contornos de Mach,
presión, temperatura y shock. Matplotlib no reemplaza esa inspección espacial,
pero sí es la herramienta principal para automatizar gráficas y análisis.
