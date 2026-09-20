# Como ver y usar los resultados

## Abrir la interfaz

Haz doble clic en `ABRIR_RESULTADOS.cmd`. Se abre ParaView 6.1.1 con
`nozzle_results.pvsm`, el volumen `flow.vtk` y la pared `wall.vtk` cargados.

En `Pipeline Browser`, a la izquierda:

- `Flujo SU2` es todo el campo dentro de la tobera.
- `Pared` dibuja el contorno.
- `Resultado` es el texto con las posiciones principales.
- El icono de ojo muestra u oculta cada elemento.

## Cambiar la variable mostrada

Selecciona `Flujo SU2` y usa la lista de color de la barra superior, que empieza
en `Mach`. Las variables mas utiles son:

- `Mach`: aceleracion supersonica, zona hipersonica y salto a traves del choque.
- `Pressure`: caida de presion y recuperacion brusca en el choque.
- `Temperature`: enfriamiento durante la expansion y calentamiento tras el choque.
- `Velocity`: magnitud de velocidad; tambien se puede usar para crear vectores.
- `Eddy_Viscosity`: actividad del modelo turbulento.

Pulsa `Rescale to Data Range` despues de cambiar de variable. La rueda del mouse
hace zoom; el boton central desplaza la vista; `r` restablece la camara.

## Identificar la separacion

Abre `cf_separation.png`. La linea azul es el coeficiente de friccion tangencial
en la pared:

- `Cf_t > 0`: el flujo cercano a la pared avanza aguas abajo.
- `Cf_t = 0` en x = 0.1213 m: punto de separacion.
- `Cf_t < 0`: flujo local invertido, dentro de la burbuja separada.
- `Cf_t = 0` en x = 0.1485 m: readherencia.

La zona roja de la grafica es la burbuja separada. `centerline_profiles.png`
muestra la caida brusca de Mach y el aumento de presion asociados al choque.

## Archivos principales

- `mach_contour.png`: mapa de Mach listo para presentar.
- `pressure_contour.png`: mapa de presion con escala logaritmica.
- `cf_separation.png`: evidencia del desprendimiento de capa limite.
- `centerline_profiles.png`: Mach y presion sobre el eje.
- `wall_cf_processed.csv`: datos numericos de pared para Excel.
- `flow.vtk` y `wall.vtk`: resultados completos para ParaView.

## Volver a procesar

En PowerShell:

```powershell
cd 'D:\PRUEBA SU2_2026\hypersonic_nozzle_ar64'
& 'C:\Program Files\ParaView 6.1.1\bin\pvpython.exe' .\make_visualizations.py
```

Para cambiar geometria o condiciones primero hay que modificar y recalcular el
caso; cambiar solamente la escala de colores no modifica la solucion CFD.
