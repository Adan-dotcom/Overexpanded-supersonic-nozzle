# Instrucciones iniciales para continuar el proyecto

## Lee esto primero

Este repositorio estudia cuántos transductores de presión de pared hacen falta
para estimar la separación de capa límite inducida por choque en una tobera
sobreexpandida. La geometría de trabajo es un contorno DLR-PAR axisimétrico con
relación de áreas 30. Hay dos carriles científicos distintos:

1. Validación con el experimento publicado DLR-PAR de nitrógeno gaseoso frío.
2. Aplicación sintética de la misma geometría a productos calientes LOX/CH4 y
   aire exterior, con condiciones de cámara derivadas mediante NASA CEA.

El segundo carril no representa hardware Raptor ni datos propietarios. Es un
estudio metodológico sintético. El objetivo final es producir CFD validada,
extraer `x_sep` y presiones de pared, y después comparar arreglos de sensores y
modelos de aprendizaje automático.

## Verdad actual del proyecto

- Backend CFD activo: **Eilmer 5**, no SU2.
- Versión fijada: `v5.0.0`, commit
  `f53f4609a0331d48efee69a4e4f3c3598378cc03`.
- Etiquetas CFD aceptadas para ML: **0**.
- El benchmark multicomponente productos/aire todavía no está implementado.
- La validación DLR-PAR con N2 frío todavía no está reproducida en Eilmer.
- La campaña caliente está bloqueada hasta cerrar los gates documentados.
- Las LUT históricas fueron retiradas. No recrearlas como modelo activo.
- El árbol actual está limpio de mallas, reinicios, VTK y campañas pesadas.

## Limite de responsabilidad de esta computadora

Este agente trabaja **solo** el carril CFD/Eilmer: instalacion, benchmark
productos/aire, validacion DLR-PAR con N2 y, cuando los gates lo permitan,
casos calientes. No debe ejecutar redes neuronales, recuperar perfiles SU2
historicos ni seguir `instrucciones para claude.md`. Ese documento pertenece a
otra computadora y a un sandbox ML provisional separado.

Referencia histórica de las LUT retiradas:

| Tabla | Resolución | Rango T alcanzado | Rango p alcanzado | Estado |
|---|---:|---:|---:|---|
| NASA-refined | 72 x 192 = 13 824 estados | 272.459 a 3 800.781 K | 1.752 kPa a 9.367 MPa | interpolación aprobada, modelo físico no aprobado |
| GRI-Mech prototipo | 36 x 72 = 2 592 estados | 272.459 a 5 502.124 K | 1.752 kPa a 25.991 MPa | rechazada |

La tabla refinada estaba parametrizada realmente en densidad y energía interna:
`rho = 0.02..6.0 kg/m3` y `e = -10.78..-1.50 MJ/kg`. Los rangos de T y p
eran los valores resultantes dentro de ese rectángulo, no sus ejes. Su base
termodinámica declaraba 200 a 6 000 K, pero eso no resolvía el error de usar una
única composición de productos también en el ambiente. Ninguna LUT es parte del
flujo Eilmer actual.

Los archivos con autoridad son, en este orden:

1. `AGENTS.md`
2. `raptor_like_study/physics_model_status.yaml`
3. `HANDOFF.md`
4. `raptor_like_study/RUN_STATUS.md`
5. `raptor_like_study/ASSUMPTIONS_AND_EVIDENCE.md`
6. `experiment_spec_final_hot_lox_ch4.yaml`

Si una conversación previa contradice esos archivos, usa los archivos.

## Arranque en la computadora nueva

Trabaja preferentemente dentro del sistema de archivos Linux de WSL2, no bajo
`/mnt/c`, porque compilar y escribir muchos archivos pequeños es más rápido.

Desde PowerShell, si WSL2/Ubuntu aún no existe:

```powershell
wsl --install -d Ubuntu
```

Después del reinicio, abre Ubuntu y ejecuta:

```bash
cd ~
git clone https://github.com/Adan-dotcom/Overexpanded-supersonic-nozzle.git
cd Overexpanded-supersonic-nozzle
git switch main
git pull --ff-only
```

Lee el estado antes de hacer CFD:

```bash
sed -n '1,240p' AGENTS.md
sed -n '1,260p' HANDOFF.md
sed -n '1,260p' raptor_like_study/RUN_STATUS.md
sed -n '1,280p' raptor_like_study/ASSUMPTIONS_AND_EVIDENCE.md
sed -n '1,320p' raptor_like_study/physics_model_status.yaml
```

Instala la versión fijada de Eilmer. El script instala dependencias de Ubuntu,
OpenMPI, LDC y compila el ejecutable optimizado con MPI:

```bash
bash raptor_like_study/eilmer/install_eilmer5_wsl.sh
source raptor_like_study/eilmer/eilmer5-env.sh
bash raptor_like_study/eilmer/check_eilmer_install.sh
```

La instalación reproducida debe quedar en:

- código fuente: `~/gdtk`
- ejecutables y datos: `~/gdtkinst`
- compilador: `~/opt/ldc2-1.42.0-linux-x86_64`

No reemplaces silenciosamente una instalación distinta que ya exista. El
instalador se detiene si `~/gdtk` apunta a otro commit.

## Comprobación inicial obligatoria

Instala el entorno Python del repositorio y corre las verificaciones rápidas:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r raptor_like_study/requirements.txt
(cd raptor_like_study && python -m unittest discover -s tests -v)
python raptor_like_study/scripts/check_model_readiness.py products_air_benchmark --stage screen
python raptor_like_study/scripts/check_model_readiness.py hot_methalox_products_air_plume --stage production
```

Resultado esperado al recibir el repo:

- los tests pasan;
- `products_air_benchmark --stage screen` está listo para implementarse;
- producción caliente permanece bloqueada y enumera sus bloqueos.

No elimines un bloqueo editando nombres o cambiando `false` por `true`. Sólo se
cierra con evidencia generada y auditada.

## Primer trabajo que debes ejecutar

Implementa un benchmark Eilmer pequeño de mezcla compresible de productos de
combustión y aire. No empieces por la tobera completa.

Requisitos mínimos:

- entre 20 000 y 60 000 celdas;
- seis rangos MPI;
- composición de productos y composición de aire aplicadas en fronteras
  distintas;
- conjunto de especies, termodinámica y transporte explícitos y documentados;
- estados finitos con presión, densidad y temperatura positivas;
- cierre de fracciones másicas;
- balance de flujo de masa;
- balance de flujo de energía total;
- exportación VTK inspeccionable;
- objetivo de 10 a 30 minutos de solver en la máquina Ryzen;
- aborto duro a los 60 minutos.

Antes de lanzarlo vuelve a ejecutar:

```bash
python raptor_like_study/scripts/check_model_readiness.py products_air_benchmark --stage screen
```

Cada corrida debe vivir fuera del código fuente, en un directorio aislado de
artefactos. No agregues `lmrsim`, mallas generadas, VTK, reinicios ni logs al
Git. Sí agrega el caso reproducible, scripts de postproceso, métricas pequeñas,
provenance y un reporte breve.

Secuencia típica de Eilmer:

```bash
source raptor_like_study/eilmer/eilmer5-env.sh
lmr prep-gas -i gas-model.inp -o gas-model.lua
lmr prep-grid
lmr prep-sim
mpirun -np 6 lmr-mpi-run
lmr snapshot2vtk --all
```

Adapta los comandos a la API concreta del caso y a la documentación de Eilmer
5. No inventes sintaxis de Eilmer 4 o de SU2.

## Orden después del benchmark

1. Pasar y documentar el benchmark productos/aire.
2. Portar `DLR_PAR_full_contour.csv` y revisar geometría y calidad de malla.
3. Digitalizar las condiciones y anclas experimentales DLR-PAR de N2 frío.
4. Reproducir presión de pared y posición de separación del experimento.
5. Hacer convergencia de malla, paso temporal y dominio.
6. Calificar turbulencia y condición térmica de pared.
7. Seleccionar y validar química/termodinámica/transporte LOX/CH4.
8. Ejecutar el DOE caliente y sólo entonces producir etiquetas para ML.

La separación se define como el primer cruce persistente posgarganta de
esfuerzo cortante de pared positivo a negativo. El choque se guarda aparte como
el máximo gradiente de presión de pared. No uses el salto de presión como
sinónimo automático de separación.

## Reglas científicas que no se negocian

- `NPR = Pc/Pa`; no muestres `Pc`, `Pa` y NPR como tres variables independientes.
- `T0` y composición vienen de CEA para cada `Pc` y O/F.
- N2 frío valida la geometría y separación, no la química de metano/oxígeno.
- Una sola geometría no permite afirmar generalización geométrica.
- Un smoke test sólo prueba software.
- Un screen sólo selecciona opciones numéricas.
- Una corrida que falla un gate jamás se convierte en etiqueta final.
- Mantén juntos en el mismo fold todos los snapshots, perturbaciones y ruidos
  derivados de una misma corrida CFD.
- Para producción exige conservación, convergencia, sensibilidad de modelo y
  ancla experimental.

## Qué entregar al terminar cada bloque

Actualiza `raptor_like_study/RUN_STATUS.md` y
`raptor_like_study/physics_model_status.yaml` con evidencia verificable. Incluye
commit de Eilmer, archivo de gas/química, malla, ranks, tiempo de pared, estado
de salida, rangos físicos, balances y rutas locales de artefactos. Corre:

```bash
git diff --check
(cd raptor_like_study && python -m unittest discover -s tests -v)
git status --short
```

Haz commits pequeños y descriptivos y súbelos a `origin/main` cuando el bloque
esté probado. No reescribas la historia remota sin autorización explícita.

## Definición de éxito del traspaso

El repositorio ya es suficiente para continuar en otra computadora: contiene
la geometría, CEA, DOE, reglas físicas, gates, scripts ML, instalación fijada de
Eilmer y este procedimiento. No contiene resultados CFD aceptados ni el primer
caso Eilmer del proyecto. Tu primera responsabilidad es construir y auditar el
benchmark, no anunciar que la campaña física ya está lista.
