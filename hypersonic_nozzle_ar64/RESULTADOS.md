# Prueba SU2: tobera axisimetrica hipersonica sobreexpandida

## Caso demostrativo

- Modelo: RANS compresible axisimetrico, SST-2003m con correccion Sarkar.
- Gas: aire caloricamente perfecto, gamma 1.4, ley de Sutherland.
- Pared: adiabatica y no-slip.
- Camara: p0 = 2.0 MPa, T0 = 600 K.
- Contrapresion: pb = 75 kPa; NPR = 26.67.
- Geometria: garganta x = 0 m, rt = 0.010 m; salida x = 0.200 m,
  re = 0.080 m; Ae/At = 64.
- Dominio numerico: termina en x = 0.400 m para mantener el outlet subsonico.
- Malla: 44,000 cuadrilateros; primera celda en garganta = 6.62e-7 m.
- Paralelismo probado: OpenMPI, 6 procesos.

La solucion cuasi-1D inicial coloca un choque normal consistente con pb. SU2
resuelve despues la capa limite viscosa y la interaccion choque-capa limite.

## Resultado del ultimo checkpoint

- Mach maximo global: 5.4594 en x = 0.15455 m, r = 0.02745 m.
- Separacion, cruce Cf_t positivo a negativo: x = 0.12130 m.
- Readherencia, cruce Cf_t negativo a positivo: x = 0.14850 m.
- Longitud de la burbuja separada: 0.02720 m.
- Choque central, maximo gradiente positivo de presion: x = 0.16227 m.
- Outlet numerico: M = 0.5996, p = 74.763 kPa.
- Resolucion de pared: y+ mediana = 0.440; y+ maxima = 1.822.

Entre los dos ultimos checkpoints, x_sep cambio de 0.12387 a 0.12130 m.
Por ello, el valor que debe usarse para esta prueba es x_sep aproximadamente
0.122 +/- 0.002 m, medido desde la garganta, no una cifra de precision de diseno.

## Reproduccion

Desde PowerShell:

```powershell
wsl.exe -d Ubuntu --cd '/mnt/d/PRUEBA SU2_2026/hypersonic_nozzle_ar64' -- bash -lic "mpirun -np 6 SU2_CFD nozzle_continue.cfg"
wsl.exe -d Ubuntu --cd '/mnt/d/PRUEBA SU2_2026/hypersonic_nozzle_ar64' -- python3 find_separation.py
```

Para reconstruir desde cero se ejecutan, en este orden, `generate_mesh.py`,
`make_seed_template.cfg`, `generate_shocked_seed.py` y `nozzle_seeded.cfg`.

## Limitaciones

El calculo estacionario no alcanzo el criterio formal de residuos. La posicion
del choque y x_sep oscilan, comportamiento esperable en una interaccion fuerte
choque-capa limite. Para una prediccion de ingenieria se requieren URANS,
promedio temporal, estudio de independencia de malla y condiciones/geometria
reales. A T0 = 600 K, el modelo de gas perfecto tambien es una idealizacion
fuerte en la zona de mayor Mach.
