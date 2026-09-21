# Plan de validacion DLR-PAR y sensores de presion

## Decision de estudio

La pregunta final es: para una tobera DLR-PAR fija y un intervalo de
condiciones definido, cual es el menor numero y la ubicacion de sensores de
presion de pared que permiten estimar el regimen de separacion y `x_sep` con
una incertidumbre declarada.

La cadena de evidencia es:

1. Validar Eilmer frente al experimento DLR-PAR de N2 frio.
2. Cerrar los gates de la aplicacion sintetica caliente.
3. Generar CFD aceptada con perfiles de pared y estadisticas URANS.
4. Simular instrumentacion realista sobre esos perfiles.
5. Ajustar y evaluar la seleccion de sensores sin fuga entre corridas CFD.

La validacion N2 no valida quimica LOX/CH4; la aplicacion caliente no valida la
geometria DLR-PAR. Son dos carriles que responden preguntas distintas.

## Base experimental

Haidn y Verma estudiaron una TOP de relacion de areas 30, con N2 en la
instalacion P6.2 de DLR Lampoldshausen. Se adquirieron presiones de pared,
visualizacion por aceite, schlieren de alta velocidad y galgas. El fenomeno
incluye FSS, RSS parcial y RSS plena, con oscilacion axial y variacion
circunferencial de los choques.

Una auditoria de fuentes encontro que las Figuras 11 y 12 del reporte NASA de
side loads **no corresponden a esta tobera DLR**. La PAR de NASA/MSFC tiene
garganta de 38.1 mm, relacion de areas 30.5, angulo inicial de 40 grados y usa
aire seco calentado en camara de vacio. La DLR-PAR objetivo tiene garganta de
20 mm, relacion de areas 30, angulo de 34 grados despues del arco de garganta,
N2 seco y descarga atmosferica. Por tanto, los umbrales NASA 23.8, 57.2 y 13.4
no son objetivos admisibles para la validacion DLR.

El articulo DLR objetivo reporta perfiles medios de subida a NPR 30, 33, 35,
37 y 40. En esa campana la transicion FSS a RSS parcial ocurre entre NPR 33 y
35, hay RSS parcial entre 35 y 37, el end effect devuelve el flujo a FSS cerca
de 38 y aparece RSS plena cerca de NPR 34 durante bajada. Los valores exactos
de las curvas todavia requieren una copia de figura con resolucion suficiente.
La auditoria completa esta en `cases/cold_n2_validation/SOURCE_AUDIT.md`.

## Matriz de validacion

Esta matriz es provisional hasta congelar las condiciones absolutas y los
puntos digitizados del articulo DLR:

| Caso | Condicion DLR | Observable primario | Objetivo |
|---|---|---|---|
| N2-01 | NPR 30, subida | FSS y `p_wall/Pa` | Reproducir perfil medio DLR Fig. 3a |
| N2-02 | NPR 33, subida | FSS previo a transicion | Perfil medio y `X_inc` |
| N2-03 | NPR 35, subida | RSS parcial/intermitente | Media y estadisticas URANS |
| N2-04 | NPR 37, subida | RSS parcial/intermitente | Media y estadisticas URANS |
| N2-05 | NPR cercano a 38, subida | End effect, pRSS a FSS | Transicion y movimiento de separacion |
| N2-06 | NPR 40, subida | FSS posterior al end effect | Perfil medio DLR Fig. 3a |
| N2-07 | NPR cercano a 34, bajada | Primera RSS plena reportada | Regimen, choque, separacion y reenganche |

Primero usa RANS solo para depurar geometria, malla y perfiles medios FSS.
Los casos RSS parcial, end effect e histeresis requieren URANS: una solucion
RANS estacionaria no puede reproducir flapping, rippling ni conmutacion de
regimen.

Registra por caso `p_wall/Pa(x/Rt)`, RMSE y error maximo contra los puntos
digitizados, `x_shock`, `x_sep`, `x_reattach`, regimen, direccion de barrido,
estadisticas URANS, positividad, balances de masa/energia e independencia de
malla, paso temporal y dominio.

Todavia no hay puntos digitizados ni incertidumbre tabulada en el repositorio.
La plantilla vacia esta en
`cases/cold_n2_validation/cold_n2_validation_targets.template.csv`. No se
fijan porcentajes ficticios de error. Al digitalizar se debe congelar:

```text
case_id,sweep_direction,npr,regime_expected,x_rt,pwall_over_pa,
sigma_pwall_over_pa,x_shock_rt,sigma_x_shock_rt,x_sep_rt,sigma_x_sep_rt,
source_figure,digitization_method
```

Antes de observar CFD, el equipo debe fijar error de perfil, error de posicion
y tolerancia NPR. La tolerancia de transicion no puede ser menor que el salto
NPR medido y no se ajusta para favorecer un modelo de turbulencia.

## Requisitos de la validacion fria

- Usa N2 consistente con el ensayo, no CEA ni productos LOX/CH4.
- Trata `DLR_PAR_full_contour.csv` como reconstruccion del usuario. Sus cuatro
  controles escalares publicados son consistentes, pero el contorno completo
  no esta certificado.
- Genera tres mallas, con capas normales a pared y `y+` de orden uno para el
  modelo de bajo Reynolds que se elija.
- Refina garganta, posible choque en divergente y salida.
- Compara al menos dos modelos de turbulencia soportados. No calibres sobre el
  mismo conjunto que usas para evaluar.
- Separa medias RANS de estadisticas URANS.

## Sensores: baseline de ocho canales

El modelo observa presion estatica de pared flush mounted. `Pc`, O/F y `Pa` son
metadatos de operacion, no sustitutos de transductores. Las posiciones se miden
desde la garganta en el divergente, cuya longitud es `Ldiv = 125.02 mm`.

| Sensor | x [mm] | x/Ldiv | Funcion |
|---|---:|---:|---|
| S1 | 5 | 0.040 | Referencia posgarganta |
| S2 | 15 | 0.120 | Choque adelantado |
| S3 | 28 | 0.224 | Separacion temprana |
| S4 | 43 | 0.344 | Divergente medio temprano |
| S5 | 61 | 0.488 | Divergente medio |
| S6 | 80 | 0.640 | Choque o reenganche tardio |
| S7 | 101 | 0.808 | RSS aguas abajo |
| S8 | 119 | 0.952 | Condicion de salida |

Este conjunto sirve como baseline interpretable. Para presupuestos menores se
evalua layout uniforme. POD-QR, greedy y layouts aleatorios solo se ajustan
dentro del fold de entrenamiento de CFD aceptada.

## Rango, ruido y adquisicion

La ficha Kulite HEM-375 lista 17, 35 y 70 bar, error combinado maximo de 0.5%
FSO y frecuencia natural mayor de 400 kHz sin pantalla. Son candidatos para un
modelo inicial, no una garantia de instalacion caliente.

| Zona | Rango candidato | Razon |
|---|---:|---|
| S1-S2 | 70 bar absoluto | Mayor presion y margen posgarganta |
| S3-S5 | 35 bar absoluto | Compromiso entre margen y resolucion |
| S6-S8 | 17 bar absoluto | Mejor resolucion aguas abajo |

El 0.5% FSO equivale a 0.085, 0.175 y 0.350 bar en 17, 35 y 70 bar. Simula
siempre tres niveles: sensor ideal; error fijo de calibracion por canal; e
instalacion con drift termico, ruido, sesgo, cavidad/pantalla y filtrado. Los
parametros de instalacion deben medirse o marcarse como supuestos.

No conviertas 400 kHz en ancho de banda del sistema. La cavidad, pantalla,
proteccion termica, cableado y adquisicion lo cambian. Cuando se fije `f_bw`,
adquiere al menos a `10*f_bw` y documenta el filtro antialias.

## Regla para el numero minimo

```text
B* = menor B que satisface simultaneamente las metas de clasificacion,
     x_sep, calibracion y robustez al ruido en el test bloqueado.
```

Propuesta inicial para congelar antes del test: `F1 >= 0.90`, MAE de `x_sep <=
5 mm` y cobertura de incertidumbre cercana a 95%. Son metas de ingenieria, no
resultados ni limites experimentales. Deben revisarse cuando queden definidas la
precision de validacion DLR y la necesidad operativa real.

## Entregables

1. `cold_n2_validation_targets.csv` digitizado y trazable.
2. Reporte N2 de malla, dominio, paso, balances y turbulencia.
3. Comparacion ciega contra objetivos congelados.
4. Dataset Eilmer con `physics_accepted=true` solo donde todos los gates pasen.
5. Estudio de sensores con seleccion dentro de cada train fold.
6. Test bloqueado por corrida CFD completa y reporte de incertidumbre.

## Fuentes

- Verma y Haidn, campana DLR objetivo: https://doi.org/10.2514/1.42351
- Verma y Haidn, geometria y efecto del entorno: https://doi.org/10.2514/1.B34320
- Registro DLR con resumen experimental: https://elib.dlr.de/59893/
- Prueba P6.2, N2 y area ratio 30:
  https://portal.fis.tum.de/en/publications/study-on-restricted-shock-separation-phenomena-in-rocket-nozzles
- NASA/MSFC, PAR distinta conservada solo como fuente rechazada para DLR:
  https://ntrs.nasa.gov/api/citations/20100017649/downloads/20100017649.pdf
- Kulite HEM-375: https://kulite.com/assets/media/2021/01/HEM-375-CO.pdf
