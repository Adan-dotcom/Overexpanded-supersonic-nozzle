# Instrucciones para Claude: orquestación ML provisional

## Misión

Trabaja en esta computadora sobre el pipeline de aprendizaje automático para
selección de transductores de presión. El propósito inmediato es desarrollar,
probar y visualizar el flujo de datos y los modelos usando información
heredada, aunque sea físicamente inválida. Esto es un **sandbox de software**,
no un resultado científico ni una parte publicable del paper.

Otro agente ejecutará la nueva CFD con Eilmer en otra computadora. No lances
CFD pesada aquí y no reviertas la migración a Eilmer.

## Estado que debes aceptar

- Hay cero etiquetas con `physics_accepted=true`.
- Las 48 filas en `raptor_like_study/cases/physical_doe.csv` son condiciones de
  operación propuestas, no soluciones CFD.
- `raptor_like_study/cases/cea/physical_cea_summary.csv` contiene resultados
  termoquímicos CEA, no posiciones de separación.
- `raptor_like_study/ml_pipeline/case_registry.csv` tiene 48 casos planeados,
  pero no perfiles de presión ni etiquetas.
- El commit histórico `8bea52b` conserva perfiles SU2 provisionales y métricas
  fallidas. Pueden recuperarse sólo para probar código.
- La LUT y SU2 están retirados del modelo físico activo.

Lee primero:

```text
AGENTS.md
HANDOFF.md
raptor_like_study/RUN_STATUS.md
raptor_like_study/physics_model_status.yaml
raptor_like_study/ml_pipeline/README.md
raptor_like_study/ml_pipeline/build_training_dataset.py
raptor_like_study/ml_pipeline/train_sensor_models.py
experiment_spec_final_hot_lox_ch4.yaml
```

## Prohibiciones

- No cambies `physics_accepted` a `true`.
- No metas datos provisionales en `accepted_sensor_dataset.csv`.
- No llames a los resultados “validados”, “predictivos” o “publicables”.
- No uses filas CEA como si fueran muestras independientes de separación.
- No cuentes snapshots temporales, realizaciones de ruido o sensores de una
  misma CFD como casos físicos independientes.
- No mezcles información del test fold al elegir posiciones de sensores,
  normalizar, imputar o ajustar hiperparámetros.
- No recuperes VTK, reinicios, mallas ni logs grandes del historial.
- No modifiques los gates de física para hacer que el sandbox pase.

## Estructura de trabajo

Crea una ruta separada:

```text
raptor_like_study/ml_sandbox_legacy/
  README.md
  scripts/
  tests/
  data/        # local/ignorado por Git
  artifacts/   # local/ignorado por Git
  reports/
```

Agrega `data/` y `artifacts/` al `.gitignore`. El código, tests, configuración y
reportes pequeños sí pueden versionarse. Todo resultado debe llevar:

```json
{
  "physics_accepted": false,
  "provisional_data_used": true,
  "publishable": false,
  "purpose": "pipeline_development_only"
}
```

## Fase 1: inventario reproducible

Construye un script que catalogue el árbol actual y los CSV pequeños accesibles
en el commit `8bea52b`. Usa `git ls-tree` y `git show`; no hagas checkout del
commit viejo encima de `main`.

Prioriza únicamente:

```text
raptor_like_study/**/wall_processed*.csv
raptor_like_study/**/wall_settle.csv
raptor_like_study/**/smoke_field_audit*.json
raptor_like_study/scripts/legacy_effective_ideal_metrics*.json
```

Genera `reports/data_inventory.csv` con origen, commit, tamaño, columnas,
unidades inferidas, condición de operación, geometría, timestep/caso padre,
calidad conocida y razón de exclusión científica. Calcula hashes SHA-256 de lo
recuperado. No asumas unidades a partir del nombre: inspecciónalas y registra
cualquier ambigüedad.

## Fase 2: dataset de desarrollo

Normaliza los perfiles a columnas mínimas:

```text
source_case_id, snapshot_id, geometry_id, pc_pa, t0_k, pa_pa, of_ratio,
x_m, pressure_pa, cf, wall_shear_pa, provisional, exclusion_reason
```

No todos los archivos tendrán todas las columnas. Conserva faltantes como
faltantes y documenta qué transformaciones son posibles. Deriva `x_sep` sólo
si existe esfuerzo cortante o `Cf` con convención de signo comprobable y el
cruce negativo persiste al menos 1 mm. Guarda el máximo gradiente de presión
como `x_shock`, una variable distinta.

Si sólo hay uno o muy pocos casos físicos independientes, no fabriques una
validación. Puedes crear perturbaciones sintéticas para probar las funciones,
pero deben tener `source_case_id` común y `synthetic=true`; nunca pueden cruzar
entre train y test como grupos distintos.

El constructor final de datos aceptados debe seguir fallando cerrado. Añade una
ruta separada o usa explícitamente `--allow-provisional`; no cambies el valor
predeterminado seguro.

## Fase 3: experimentos ML

Primero prueba baselines sencillos y después redes neuronales. Para cada número
de sensores en `[2, 3, 4, 5, 6, 8, 10, 12, 16, 24]`, compara cuando los datos lo
permitan:

- promedio o prevalencia como baseline nulo;
- regresión lineal/Ridge y clasificación logística;
- random forest;
- MLP pequeño con regularización y early stopping;
- sensores uniformes;
- selección POD-QR aprendida sólo con el train fold;
- selección greedy o información mutua aprendida sólo con el train fold;
- varias semillas para layouts aleatorios como referencia.

Tareas separadas:

1. Clasificar si hay separación.
2. Regresar `x_sep` condicionado a que exista separación.

No entrenes un clasificador si sólo existe una clase. No entrenes una red si el
número de grupos independientes no permite ni una evaluación mínima; en ese
caso prueba el código con datos sintéticos y entrega un diagnóstico de
insuficiencia, no una métrica engañosa.

Escala presiones de forma físicamente interpretable, por ejemplo `p_wall/Pc` o
`(p_wall-Pa)/Pc`, y conserva también las variables de operación. Ajusta el
escalador únicamente en entrenamiento. Mantén `NPR=Pc/Pa` como derivada, nunca
como una tercera muestra independiente de `Pc` y `Pa`.

## Validación y fugas

El grupo indivisible es `source_case_id`. Todos los snapshots, perfiles
interpolados, ruidos y aumentos de un caso permanecen en el mismo fold. La
selección de sensores también ocurre dentro de cada train fold.

Con suficientes casos usa validación cruzada agrupada anidada y reserva un test
bloqueado. Mientras sólo haya datos heredados, usa el protocolo más honesto que
permita el número de grupos y marca explícitamente su limitación. Reporta:

- número de casos físicos independientes;
- distribución de separados/no separados;
- MAE y RMSE de `x_sep` en mm;
- F1, balanced accuracy, AUROC y curvas de calibración cuando sean definibles;
- media, dispersión e intervalo entre semillas;
- posiciones físicas de sensores, no sólo índices;
- comparación contra el baseline nulo;
- sensibilidad a ruido y bias de transductor;
- costo/beneficio al aumentar sensores.

## Figuras y reporte

Produce como mínimo:

1. mapa de perfiles de presión heredados;
2. ubicación de sensores sobre el contorno;
3. error de `x_sep` contra número de sensores;
4. métricas de clasificación contra número de sensores;
5. predicho contra objetivo, si la evaluación es definible;
6. gráfico de residuos;
7. tabla que separe datos reales, CFD provisional y datos sintéticos.

Pon una banda o título visible `PROVISIONAL - NOT FOR PUBLICATION` en todas las
figuras. Escribe `reports/PROVISIONAL_ML_REPORT.md` con métodos, inventario,
fugas evitadas, resultados, fallas y requisitos para reemplazar el sandbox por
datos Eilmer aceptados.

## Contrato con el agente CFD

Prepara un importador que más adelante acepte una fila por corrida Eilmer con:

```text
case_id,geometry_id,pc_pa,t0_k,pa_pa,of_ratio,chemistry_model,
turbulence_model,wall_model,mesh_id,time_window,profile_csv,separated,
x_sep_m,x_reattach_m,x_shock_m,numerically_accepted,physics_accepted,
provisional,exclusion_reason
```

`profile_csv` debe contener como mínimo `x_m,pressure_pa`; para auditar la
etiqueta debe conservar además `cf` o `wall_shear_pa`. Sólo filas con
`physics_accepted=true` entrarán al dataset final. Cuando lleguen, la ruta final
debe ejecutarse sin `--allow-provisional` y los resultados antiguos deben quedar
separados.

## Criterio de terminado

Termina el bloque únicamente cuando:

- el inventario puede regenerarse desde el commit histórico;
- los parsers tienen tests con perfiles mínimos;
- no existe fuga entre grupos;
- el pipeline seguro todavía rechaza cero etiquetas aceptadas;
- el sandbox corre de punta a punta o explica con precisión qué dato falta;
- cada resultado provisional está marcado como no publicable;
- hay un comando único documentado para repetir los experimentos;
- `git diff --check` y los tests pasan.

No maquilles una carencia de datos. El resultado útil de esta etapa puede ser
un pipeline impecable que concluye “todavía no se puede medir capacidad
predictiva”. Eso deja listo el trabajo serio cuando lleguen las corridas Eilmer.
