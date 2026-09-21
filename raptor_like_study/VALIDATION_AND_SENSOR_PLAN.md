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

El reporte NASA de side loads presenta perfiles de presion normalizados de una
PAR para barridos de NPR. Es la fuente abierta para digitalizar curvas y
transiciones:

| Barrido | Regimen publicado | Uso CFD |
|---|---|---|
| NPR creciente | FSS hasta 23.7; RSS desde 23.8 hasta poco mas de 57.2; FSS hasta flujo lleno cerca de 65 | Regimen, perfil y zona de choque |
| NPR decreciente | Flujo lleno hasta 62.2; FSS hasta 57.5; RSS hasta 13.4; FSS debajo de 13.4 | Histeresis y retransicion |
| RSS | Picos de presion sobre ambiente y valles cercanos a ambiente | Forma de perfil, choque y reenganche |

Estos limites describen regimenes, no sustituyen condiciones de frontera
completas. Antes de declarar validacion, digitaliza las figuras y guarda
direccion de barrido, NPR, resolucion de eje, incertidumbre y referencia
espacial.

## Matriz de validacion

| Caso | Condicion | Observable primario | Objetivo |
|---|---|---|---|
| N2-01 | NPR 20.0, subida | FSS y `p_wall/Pa` | Reproducir FSS y perfil digitalizado |
| N2-02 | NPR 23.7/23.8, subida | FSS a RSS | Capturar transicion dentro de resolucion experimental |
| N2-03 | NPR 30.0, subida | RSS | Perfil, `x_shock`, `x_sep`, `x_reattach` |
| N2-04 | NPR 40.5, subida | RSS | Perfil medio y estadisticas URANS |
| N2-05 | NPR 52.8/57.2, subida | Fin de RSS | Capturar retorno a FSS |
| N2-06 | NPR 13.4, bajada | RSS a FSS | Reproducir histeresis |
| N2-07 | NPR 57.5/62.2, bajada | FSS a flujo lleno | Regimen y perfil correctos |

Las NPR se tomaron de las leyendas de las Figuras 11 y 12 del reporte NASA.
Primero usa RANS para depurar geometria, malla y presion media. Cerca de 23.8,
57.2 y 13.4 requiere URANS: una solucion RANS estacionaria no puede reproducir
flapping, rippling ni conmutacion de regimen.

Registra por caso `p_wall/Pa(x/Rt)`, RMSE y error maximo contra los puntos
digitizados, `x_shock`, `x_sep`, `x_reattach`, regimen, direccion de barrido,
estadisticas URANS, positividad, balances de masa/energia e independencia de
malla, paso temporal y dominio.

Todavia no hay puntos digitizados ni incertidumbre tabulada en el repositorio.
No se fijan porcentajes ficticios de error. Al digitalizar se debe congelar:

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
- Trata `DLR_PAR_full_contour.csv` como reconstruccion del usuario hasta
  contrastarla con la fuente.
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

- NASA, *Nozzle Side Load Technology*, Figuras 11 y 12:
  https://ntrs.nasa.gov/api/citations/20100017649/downloads/20100017649.pdf
- Haidn y Verma, DOI: https://doi.org/10.2514/1.42351
- Registro DLR con resumen experimental: https://elib.dlr.de/59893/
- Prueba P6.2, N2 y area ratio 30:
  https://portal.fis.tum.de/en/publications/study-on-restricted-shock-separation-phenomena-in-rocket-nozzles
- Kulite HEM-375: https://kulite.com/assets/media/2021/01/HEM-375-CO.pdf
