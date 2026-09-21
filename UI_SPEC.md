# Especificación de interfaz para la plataforma CFD de toberas

## 1. Propósito

Esta especificación define una interfaz profesional para configurar, ejecutar,
vigilar, auditar y comparar estudios CFD de separación en toberas
sobreexpandidas. La interfaz debe envolver el flujo de trabajo existente de
SU2, MPI, WSL, Gmsh, NASA CEA/Cantera, LUT y Python sin ocultar las decisiones
físicas que determinan si un resultado puede utilizarse como evidencia o como
etiqueta de aprendizaje automático.

Este documento es un contrato de producto y arquitectura para otro agente. No
autoriza a cambiar los solvers, los casos ni los criterios científicos.

### Principios no negociables

1. La aplicación nunca presentará `Exit Success` como sinónimo de resultado
   físicamente válido.
2. Debe mostrar de forma permanente la procedencia de cada cantidad:
   medida/publicada, suministrada, derivada o asumida.
3. Debe impedir que smoke tests, screens, mock data o casos que fallen algún
   gate entren al dataset final.
4. Debe mantener separados los dos carriles científicos:
   - **Validación cold-N2:** DLR-PAR y datos experimentales publicados.
   - **Aplicación hot-methalox:** geometría DLR-PAR sintética con productos
     LOX/CH4; no es una reconstrucción de Raptor ni del hardware NASA LLAMA.
5. NPR siempre se deriva de `Pc/Pa`; la UI no permitirá muestrear `Pc`, `Pa` y
   NPR como tres variables independientes.
6. Los artefactos grandes se quedan en almacenamiento local. Git sólo conserva
   configuración, código, metadatos, resultados procesados y manifiestos.

## 2. Usuarios y decisiones

### Investigador CFD

- Define geometría, dominio, malla, condiciones y modelos.
- Lanza SU2 en WSL/MPI y diagnostica convergencia.
- Decide qué rama numérica merece pruebas más costosas.

### Responsable de física y validación

- Revisa balances, propiedades, química, transporte y sensibilidad de modelo.
- Compara cold-N2 con experimento y hot-methalox con referencias
  termoquímicas.
- Firma o rechaza gates físicos con evidencia trazable.

### Responsable de sensores y ML

- Define ubicaciones, rango, frecuencia, ruido y subconjuntos de sensores.
- Sólo consume perfiles con `physics_accepted=true`.
- Audita particiones por caso físico y evita fuga entre realizaciones de ruido.

### Operador

- Ve cola, recursos, logs, disco, reinicios y fallos.
- Puede pausar después de un segmento, reanudar desde checkpoint o cancelar
  con terminación ordenada.

## 3. Modelo mental y navegación

La aplicación debe abrir en el **Workspace del estudio**, no en una landing
page. La navegación principal será una barra lateral compacta:

1. **Resumen**
2. **Campañas**
3. **Casos**
4. **Geometría y malla**
5. **Termoquímica**
6. **Ejecuciones**
7. **Resultados**
8. **Comparación**
9. **Sensores y ML**
10. **Evidencia**
11. **Sistema**

Una barra superior mostrará: repositorio/branch/commit, carril científico
activo, máquina de cómputo, estado de WSL/SU2/MPI, espacio libre y trabajos
activos. Todos los valores llevarán unidades visibles y conversión explícita;
no se mezclarán unidades de entrada silenciosamente.

### Jerarquía de estados

Cada caso tendrá dos estados independientes:

- **Estado de ejecución:** draft, queued, running, paused-at-checkpoint,
  completed, cancelled o failed.
- **Estado de evidencia:** unreviewed, software-feasibility,
  numerical-screen, numerically-accepted, physics-rejected o
  physics-accepted.

La etiqueta visual final debe decir, por ejemplo, `Completado · física
rechazada`, nunca sólo `Completado`. Hoy existen cero etiquetas
`physics-accepted` para ML. El caso effective-gas NPR 20 puede figurar como
`numerically-accepted`, pero su gate térmico falla y no es dato físico del
paper. El LUT a una atmósfera sólo ha demostrado factibilidad de software.

## 4. Pantallas

## 4.1 Resumen del estudio

El primer viewport debe contestar qué se está estudiando y qué puede afirmarse:

- Contadores separados de casos planeados, ejecutados, convergidos,
  numéricamente aceptados, físicamente aceptados y elegibles para ML.
- Aviso prominente mientras `physics_accepted = 0`: **No existe todavía un
  dataset físico entrenable**.
- Carriles cold-N2 y hot-methalox en dos bandas distintas, con cobertura de
  condiciones y estado de validación.
- Últimos trabajos, consumo de disco, tiempo de CPU y fallos recientes.
- Matriz resumida de gates por caso, sin reducirla a un score opaco.
- Gráfica de cobertura del DOE en `Pc-Pa-O/F`; NPR aparece como variable
  derivada.
- Enlaces directos a `HANDOFF.md`, `RUN_STATUS.md`,
  `ASSUMPTIONS_AND_EVIDENCE.md`, literatura y commit del código.

## 4.2 Campañas y DOE

- Tabla filtrable por carril, fidelidad, estado y elegibilidad.
- Editor de campaña con rangos, unidades, distribución y justificación.
- Campo NPR de sólo lectura calculado en vivo como `Pc/Pa`.
- Advertencia para `Pa > 101.325 kPa`: requiere clasificación explícita como
  cámara presurizada; no debe llamarse condición atmosférica.
- Separación visual entre nominal, exploratorio, validación y sensibilidad.
- Vista de cobertura que revele huecos y duplicados en el espacio paramétrico.
- Botón de preflight que crea una propuesta versionada; no lanza CFD todavía.

La campaña hot-methalox actual debe mostrar 48 casos CEA planeados y cero
perfiles aceptados. Una sola geometría DLR-PAR sólo permite estudiar variación
de condiciones en ese contorno; la UI debe bloquear cualquier claim de
generalización geométrica hasta registrar varias geometrías y descriptores.

## 4.3 Detalle de caso

Usar pestañas, no tarjetas anidadas:

- **Definición:** identificador, carril, propósito, fidelidad, parent/checkpoint,
  commit y archivos fuente.
- **Condiciones:** `Pc`, `Pa`, NPR derivado, `T0`, O/F, composición, estado
  termodinámico, pared y exterior.
- **Malla:** dominio, métricas, zonas y refinamiento.
- **Solver:** ecuaciones, flujo convectivo, reconstrucción, limitador,
  turbulencia, tiempo físico y pseudo-tiempo.
- **Run:** comando efectivo, recursos, progreso, logs y checkpoints.
- **Resultados:** campos, pared, shock, separación y balances.
- **Gates:** evidencia, tolerancia, resultado y responsable de revisión.
- **Provenance:** hashes y linaje completo.

La pantalla debe enseñar simultáneamente el valor amigable y la clave SU2
correspondiente. Cada valor heredado de un preset debe indicar su origen y cada
override debe quedar resaltado.

## 4.4 Geometría y malla

### Geometría

- Vista axisimétrica con eje, pared, garganta, labio y dominio externo.
- Coordenadas inspeccionables y unidades explícitas.
- Tabla de parámetros: radios, longitudes, relación de áreas, escala y fuente.
- Comparación entre contorno importado y geometría regenerada.
- Provenance del CSV/CAD y aviso de que el contorno DLR actual fue
  reconstruido y no verificado contra CAD oficial punto por punto.

### Malla

- Vista general y zoom de garganta, pared, labio, shock previsto y plume.
- Color por calidad: scaled Jacobian, ortogonalidad, skewness y aspect ratio.
- Líneas normales a pared y gráfica de altura/crecimiento de capa.
- Conteos por zona y tipo de celda; primer espesor de pared y `y+` objetivo.
- Perfiles disponibles: screen, pilot, medium y fine, con propósito permitido.
- Comparación lado a lado y estimación de memoria/tiempo antes de generar.
- Gate de malla que no confunda una malla generada con una solución convergida.

La interfaz debe explicar que `600 x 128` es screen y no produce etiquetas;
pilot/medium/fine se reservan para candidatos. Debe mostrar si el dominio
incluye plume: un dominio interno supersónico que no transmite backpressure no
puede evaluar separación inducida por presión ambiente.

## 4.5 Solver, modelos y ecuaciones

Esta pantalla es un inspector técnico y editor controlado:

- Ecuaciones activas: Euler, Navier-Stokes, RANS/URANS, energía y especies si
  aplica.
- Forma temporal: steady o dual-time; BDF1/BDF2, `dt`, pasos, tiempo físico y
  número estimado de flow-through times.
- Flujo convectivo: HLLC, SLAU2, AUSMPLUSUP2 u otro permitido por el modelo.
- Reconstrucción: orden, MUSCL, limitador y coeficiente.
- Pseudo-tiempo: CFL, adaptación, inner iterations y criterio de parada.
- Turbulencia: SST/SA, tratamiento de pared y requisitos de `y+`.
- Condiciones de frontera con diagrama de marcadores.
- Variables termodinámicas y transporte: gas ideal efectivo, LUT,
  equilibrio/frozen, viscosidad y Prandtl.

Mostrar las ecuaciones relevantes en notación legible y, junto a ellas, las
hipótesis que las cierran. No pretender que “resolver Navier-Stokes” elimina la
necesidad de modelos de química, transporte, turbulencia, pared o mezcla.

Un panel de compatibilidad debe impedir combinaciones que SU2 no admite, por
ejemplo `SLAU2` o `FARFIELD` con el camino `DATADRIVEN_FLUID` actual. Toda
incompatibilidad necesita fuente/versionado, no reglas mágicas sólo en UI.

## 4.6 Termoquímica y LUT

- Selector claro: cold N2, effective ideal gas, equilibrium LUT, frozen o
  futura química finita.
- Estado CEA/Cantera por caso: composición, `T0`, gamma efectivo, R, entalpía,
  presión y procedencia.
- Mapa del dominio termodinámico de la LUT en `rho-e`, con trayectoria de las
  celdas superpuesta.
- Resolución real de tabla, nodos, rango, puntos extrapolados y distancia al
  borde.
- Mapas y percentiles del error off-node para presión, temperatura, velocidad
  del sonido y derivadas requeridas por el solver.
- Comparación de mallas LUT sucesivas y prueba de convergencia de `x_sep`, no
  sólo conteo de nodos.
- Aviso de validez del mecanismo/polinomios; la LUT GRI-Mech histórica está
  rechazada por exceder su rango declarado.
- Comparador equilibrium versus frozen y, cuando exista, finite-rate.

La candidata NASA refinada tiene `72 x 192 = 13824` nodos. En 2000 puntos
off-node, sus errores máximos fueron aproximadamente 0.257% en temperatura,
0.212% en presión y 0.198% en velocidad del sonido al cuadrado. La UI debe
mostrar que pasó interpolación, pero que aún falta convergencia de `x_sep` y no
está lista para producción. La UI no usará un umbral basado únicamente en
`Tmax < T0`: para gas reaccionante debe auditar entalpía total con composición
consistente y balances de energía.

### Exterior y mezcla de gases

El dominio híbrido LUT actual usa productos de combustión fríos en el exterior
porque una sola definición `DATADRIVEN_FLUID` ocupa el dominio. La interfaz
debe mostrar un banner rojo: **Exterior no representa aire; model-form abierto**.
No llamarlo “atmósfera de CO2”. La aceptación física permanecerá bloqueada
hasta justificar esta aproximación o implementar/validar una formulación
productos-aire capaz de representar mezcla y especies.

## 4.7 Monitor de ejecución en vivo

Diseñar una superficie densa y estable para trabajos largos:

- Encabezado: caso, PID/job ID, host, ranks MPI, elapsed, ETA, paso físico,
  tiempo simulado y flow-through times.
- Gráficas actualizadas incrementalmente de residuales internos por variable.
- Para URANS, separar paso físico de inner iterations; no concatenar todo como
  una sola curva engañosa.
- Reducción de residual por paso y porcentaje de pasos que cumplen criterio.
- Historial de `x_sep(t)`, `x_shock(t)`, reattachment, rango móvil y drift.
- `Tmax`, `h0` excess, densidad/presión mínima, puntos fuera de LUT,
  nonphysical points, mass/energy imbalance y `y+`.
- Uso CPU/RAM, velocidad en steps/hour, tamaño de outputs y espacio restante.
- Tail estructurado del log con filtro para warning/error y acceso al log crudo.
- Línea temporal de checkpoints y outputs escritos.

Las gráficas deben distinguir “sin dato” de cero. Si todavía no existe
separación persistente, mostrar `No detectada`, no `x_sep=0`. La UI nunca
estimará un porcentaje falso de convergencia; la ETA puede basarse en throughput
observado y debe declararlo.

### Acciones

- Cancelar ordenadamente: señal al launcher, espera, terminación MPI y registro.
- Solicitar checkpoint y detener al final del segmento.
- Reanudar sólo después de validar compatibilidad de malla, modelo, variables y
  número de niveles temporales.
- Clonar configuración como nueva rama; nunca editar silenciosamente un caso
  que ya produjo resultados.
- Abrir último campo en visualizador y exportar una figura reproducible.

## 4.8 Resultados y visualización

La UI web debe cubrir inspección rápida; no necesita sustituir ParaView para
análisis volumétrico avanzado.

- Contornos 2D axisimétricos de Mach, presión, temperatura, densidad, velocidad,
  entropía y variables de turbulencia.
- Escalas lineal/log, rango bloqueado entre casos y paletas perceptuales.
- Línea de pared con `p`, `p/p0`, `Cp`, `Cf`, shear, heat flux y `y+`.
- Marcadores de shock, primera separación persistente y reattachment con
  intervalo/incertidumbre.
- Vista coordinada: seleccionar un punto en la pared ubica la misma estación
  en el campo y viceversa.
- Serie temporal y media/RMS del intervalo estadístico aceptado.
- Descarga de PNG/SVG/CSV con metadatos y unidades.
- Apertura del VTK local en ParaView mediante una acción explícita del cliente,
  nunca cargando por defecto cientos de MB en el navegador.

La definición por defecto de separación será el primer cruce downstream donde
el esfuerzo cortante firmado permanece negativo al menos 1 mm. Debe ser
configurable sólo como versión nueva del extractor y guardarse con el resultado.

## 4.9 Gates físicos y auditoría

Presentar una matriz de gates con estado `pending/pass/fail/waived`, valor,
tolerancia, evidencia, código que lo calculó, timestamp y revisor. Reglas base:

- Estados finitos y positivos; cero extrapolaciones LUT.
- Desbalance relativo de masa `<= 0.5%`.
- Desbalance de energía `<= 1%`.
- Exceso local de entalpía total `<= 1%`, evaluado con el modelo químico
  consistente.
- Convergencia interna suficiente o independencia demostrada de `dt`.
- `y+ p95 <= 1` y `y+ max <= 2`.
- Shear negativo persistente por al menos 1 mm.
- Observación de al menos tres flow-through times.
- Drift final de `x_sep <= 0.1 mm`.
- Diferencia medium/fine de `x_sep <= 0.3 mm`.
- Sensibilidades de turbulencia y termoquímica reportadas.
- Validación experimental aplicable y limitaciones declaradas.

Un waiver exige usuario, motivo y evidencia, pero **no** convierte el caso en
`physics-accepted` cuando el gate es obligatorio. Los criterios deben
versionarse en archivos de configuración y cada caso debe conservar la versión
con la que fue evaluado.

## 4.10 Comparación de casos

- Selección de 2 a 8 casos con verificación de compatibilidad.
- Tabla diff de condiciones, malla, modelos, numerics, commits y gates.
- Curvas de pared superpuestas e interpolación sólo sobre coordenada física
  común, nunca por índice de nodo.
- Campos con misma escala y herramienta de diferencia absoluta/relativa.
- Convergencia de malla y tiempo con tolerancias visibles.
- Comparación equilibrium/frozen, SST/SA, flujo numérico y pared térmica.
- Comparación de estadística de `x_sep`, no sólo snapshot final.
- Marcado automático de comparaciones inválidas, por ejemplo mezclar cold-N2
  experimental con methalox como si fueran el mismo caso.

## 4.11 Sensores y ML

- Editor de estaciones sobre el contorno, con coordenadas axial y normalizadas.
- Perfiles de sensor: rango, error FSO, bandwidth, montaje y temperatura.
- Simulación de muestreo, filtrado, aliasing, ruido y realizaciones.
- Comparador de subconjuntos de transductores y costo/beneficio.
- Registro de features, target, extractor y unidades.
- Linaje desde el label hasta caso, intervalo temporal y gates.
- Particiones agrupadas por caso CFD; todas las realizaciones de ruido de un
  caso permanecen en el mismo fold.
- Nested cross-validation y conjunto de extrapolación.
- Métricas de error en `x_sep`, calibración de incertidumbre y cobertura.

El botón **Construir dataset final** permanecerá deshabilitado mientras no
existan perfiles `physics_accepted=true`. Debe explicar el bloqueo y enlazar a
los gates fallidos. Mock data y virtual sensors se mostrarán con watermark
`NO PUBLICABLE`; múltiples realizaciones no aumentan el conteo de casos físicos.

## 4.12 Evidencia y trazabilidad

- Catálogo de publicaciones, DOI, datasets y documentos locales.
- Matriz claim-to-evidence: cada afirmación del paper enlaza a fuentes y casos.
- Registro de supuestos clasificados por evidencia.
- Historial inmutable de configuraciones, comandos y revisiones de gates.
- Exportación de un paquete de reproducción liviano con manifiesto y hashes.
- Informe para equipo en Markdown/PDF con configuración, resultados, fallos y
  limitaciones, sin copiar VTK/restarts pesados.

## 4.13 Sistema

- Detección de Windows, WSL distro, SU2 version/build flags, MPI, Python, Gmsh,
  ParaView, CEA/Cantera y rutas.
- Pruebas `SU2_CFD --help`, MPI mínimo, lectura LUT y permisos.
- Benchmark de ranks por máquina; no asumir más ranks que núcleos físicos.
- Salud de filesystem, espacio y velocidad de escritura.
- Configuración de retención, almacenamiento y directorio de artefactos.
- Sincronización Git sólo de artefactos permitidos.

## 5. Componentes de interfaz

- Tablas densas con columnas configurables, filtros persistentes y exportación.
- Badges de estado con texto además de color; accesibles para daltonismo.
- Tooltips para siglas y controles con iconos de una biblioteca estable.
- Inputs numéricos con unidades, límites, precisión y fuente.
- Controles segmentados para carril/fidelidad/modo; toggles sólo para binarios.
- Panel de diff para configuración efectiva contra preset.
- Visor de log virtualizado para archivos largos.
- Plot linked-brushing para campo, pared y tiempo.
- Confirmaciones que muestren el comando exacto antes de operaciones costosas.
- Sin cards anidadas ni hero decorativo; es una herramienta científica densa.

## 6. Arquitectura técnica sugerida

### Frontend

- React + TypeScript + Vite.
- TanStack Query para estado remoto y TanStack Table para tablas.
- Plotly.js para curvas/contornos interactivos; vtk.js sólo para datasets
  reducidos o multiresolución.
- Zustand o reducer local para estado efímero; la fuente de verdad vive en API.
- Diseño responsive orientado primero a escritorio, con monitor read-only útil
  en tablet. No intentar edición CFD compleja en móvil.

### Backend

- FastAPI + Pydantic para esquemas estrictos, unidades y OpenAPI.
- SQLAlchemy/Alembic con SQLite para un usuario y PostgreSQL al crecer a equipo.
- Worker/launcher separado del servidor web; la API jamás ejecuta strings de
  shell recibidos del navegador.
- Parser incremental de logs SU2 hacia eventos estructurados.
- Python existente se integra como librería/CLI; evitar duplicar extractores en
  frontend.
- WebSocket o Server-Sent Events para métricas en vivo; REST para entidades y
  artefactos.

### Procesamiento y visualización

- Convertir VTK a previews livianos y series derivadas en jobs secundarios.
- Parquet para historias tabulares grandes; JSON para resúmenes; CSV para
  intercambio humano; PNG/SVG para figuras reproducibles.
- Mantener ParaView como herramienta externa para inspección volumétrica
  completa.

### Despliegue inicial

- UI y API en Windows o WSL, con una sola raíz canónica del workspace.
- Launcher ejecutado dentro de WSL y supervisor de jobs local.
- Posteriormente, adaptar el mismo contrato a Slurm/HPC sin cambiar la capa de
  casos/resultados.

## 7. Esquema de datos mínimo

Todas las entidades tendrán `id`, `schema_version`, `created_at`, `created_by`
y hashes de entradas relevantes.

### Study

`name`, `description`, `repo_url`, `git_commit`, `units_policy`,
`acceptance_policy_version`.

### Campaign

`study_id`, `track` (`cold_n2_validation` o `hot_methalox_application`),
`purpose`, `doe_definition`, `geometry_set`, `status`.

### Case

`campaign_id`, `case_key`, `fidelity`, `parent_case_id`, `Pc`, `Pa`,
`npr_derived`, `of_ratio`, `T0`, `fluid_model_id`, `geometry_id`, `mesh_id`,
`solver_config_id`, `wall_model`, `ambient_model`, `provenance`.

### Geometry / Mesh

Geometría: fuente, unidades, contour hash, parámetros y verificación.

Malla: generador/versión, zonas, celdas, first-cell, quality metrics, archivo,
hash y propósito permitido.

### FluidModel / LUT

Tipo, mecanismo, composición, equilibrio/frozen, transporte, rangos,
resolución, validation metrics, referencias, archivos y limitaciones.

### SolverConfig

Versión SU2, ecuaciones, turbulence, flux, reconstruction, limiter, CFL,
time scheme, `dt`, inner iterations, boundaries y configuración efectiva.

### Run

`case_id`, estado de ejecución, launcher, host, WSL distro, comando tokenizado,
ranks, PID/job ID, timestamps, checkpoint lineage, exit code y log paths.

### MetricSample

`run_id`, physical_step, inner_iteration, simulation_time, metric_name, value,
unit y timestamp. Guardar series densas en Parquet y sólo índices/resúmenes en
DB cuando el volumen lo requiera.

### Result

Intervalo de análisis, `x_sep`, `x_shock`, reattachment, estadísticos,
balances, extrema, wall profiles, field previews, extractor version y hashes.

### GateEvaluation

`case_id/result_id`, policy/version, gate, state, observed, threshold,
evidence_uri, evaluator_commit, reviewed_by, review_time y waiver_reason.

### SensorSet / MLDataset

Estaciones y hardware; dataset con lista de casos fuente, split groups,
transformaciones, target, eligibility query y hashes. La creación falla si
cualquier fuente carece de aceptación física.

## 8. API mínima

- `GET /system/health` y `POST /system/self-test`
- `GET|POST /studies`, `/campaigns`, `/cases`
- `POST /cases/{id}/preflight`
- `POST /cases/{id}/runs` con un `config_revision_id`, nunca shell libre
- `POST /runs/{id}/checkpoint-stop`, `/resume`, `/cancel`
- `GET /runs/{id}/events` mediante SSE/WebSocket
- `GET /runs/{id}/logs?cursor=...`
- `GET /results/{id}/wall-profile` y `/field-preview`
- `POST /results/{id}/evaluate-gates`
- `GET /comparisons?...`
- `POST /sensor-sets` y `POST /ml-datasets/build`
- `GET /artifacts/{id}/metadata`; descarga por stream/range request

Las mutaciones deben aceptar idempotency key y devolver un audit event. Los
objetos publicados o ligados a una corrida son inmutables; se crea una nueva
revisión para cambiarlos.

## 9. Ejecución segura WSL/MPI

1. Construir comandos desde argumentos tipados y allowlists; nunca concatenar
   texto proporcionado por el usuario ni invocar `shell=True`.
2. Resolver y validar rutas Windows/WSL contra raíces configuradas. Rechazar
   traversal, rutas UNC no permitidas y symlinks fuera del workspace.
3. Permitir únicamente binarios SU2/MPI versionados y detectados por health
   check.
4. Limitar ranks, memoria estimada, wall time, outputs y trabajos concurrentes.
5. Ejecutar cada run en directorio único e inmutable con config efectiva y
   manifiesto.
6. Registrar argv exacto, entorno allowlisted, cwd, versiones, commit y hashes.
7. No pasar secretos al entorno del solver ni almacenar tokens en logs/DB.
8. Cancelar el process group completo de `mpirun`, no sólo el proceso padre.
9. Escribir estados mediante archivos temporales y rename atómico; comprobar
   checkpoint antes de marcarlo reanudable.
10. No ofrecer ejecución `--allow-run-as-root` salvo entorno aislado y decisión
    administrativa explícita.
11. Deshabilitar edición/eliminación de runs activos; toda limpieza es una
    operación auditada con preview de rutas y tamaños.

El preflight debe verificar malla/config/LUT existentes, hashes, memoria, disco,
compatibilidad del restart, marcadores, ranks y que el caso no sobrescribirá
artefactos previos.

## 10. Archivos grandes y retención

- Artifact store fuera de Git, organizado por `study/case/run`.
- Metadatos en DB: path relativo, tipo, tamaño, hash, generación y retención.
- Nunca servir el filesystem completo; sólo artefactos registrados.
- Previews decimados para web y VTK original bajo demanda.
- Full fields sólo en checkpoints configurados; métricas escalares se escriben
  con alta frecuencia.
- Política por clase: logs y resúmenes permanentes; restarts recientes y hitos;
  VTK intermedios expirables tras confirmación; inputs nunca se borran.
- El manifiesto local debe poder regenerar `LOCAL_ARTIFACTS_MANIFEST.csv`.
- Alertas de disco a 20/10/5% y pausa ordenada antes de agotar volumen.
- Hash y tamaño se validan antes de mover, archivar o reanudar.
- Git guardará scripts, configs, metadatos y figuras pequeñas; respetar
  `.gitignore` para VTK, DAT y mallas generadas.

## 11. Etapas de implementación

### Fase 0: Contratos y lectura

- Esquemas Pydantic, importadores read-only y catálogo de casos existentes.
- Health check de WSL/SU2/MPI y parser de logs con fixtures.
- Sin capacidad de lanzar trabajos.

### MVP 1: Monitor y auditoría

- Resumen, detalle de caso, runs existentes, logs, residuales, métricas y gates.
- Visualización de pared y campos preprocesados.
- Estados de evidencia y separación obligatoria de carriles.
- Valor inmediato: entender lo ya calculado sin poner en riesgo simulaciones.

### MVP 2: Lanzamiento controlado

- Editor mediante presets versionados, preflight, cola local, launcher seguro,
  cancelación, segmentos y checkpoints.
- Notificación de disco y provenance completa.

### Fase 3: Física y comparación

- Editor de geometría/malla, inspector LUT, comparación de caso, mesh/time-step
  studies y revisión formal de gates.

### Fase 4: Sensores y ML

- Diseño de estaciones, ruido/hardware, datasets con bloqueo por gates,
  evaluación de modelos y exportación de evidencia.

### Fase 5: Equipo/HPC

- Autenticación/roles, PostgreSQL, object storage, Slurm, revisión/aprobación y
  paquetes reproducibles para publicación.

## 12. Criterios de aceptación de la UI

### Exactitud y honestidad científica

- Al importar el repositorio actual, el dashboard reporta cero labels
  `physics-accepted` y no permite construir el dataset final.
- Distingue correctamente el caso NPR 20 presurizado (`Pa=260 kPa`) del ancla a
  una atmósfera (`Pa=101.325 kPa`, NPR aproximadamente 51.32).
- Nunca etiqueta el exterior LUT actual como aire ni como CO2 puro.
- Separa cold-N2 experimental de hot-methalox sintético en todas las vistas.
- Calcula NPR a partir de `Pc/Pa` y detecta inconsistencias de unidades.
- Un run exitoso que falla temperatura/entalpía aparece físicamente rechazado.

### Ejecución y reproducción

- El preflight reproduce config efectiva, comando, versiones y hashes antes de
  lanzar.
- Un test MPI puede iniciarse, monitorizarse, cancelarse y reanudarse desde un
  checkpoint compatible sin procesos huérfanos.
- Reiniciar UI/API no pierde el estado del trabajo; el supervisor reconcilia
  procesos y DB.
- Dos runs nunca sobrescriben archivos entre sí.

### Rendimiento y archivos

- El monitor muestra eventos nuevos en menos de 2 s sin releer el log entero.
- Una historia de un millón de muestras sigue siendo navegable mediante
  downsampling/consulta por ventana.
- La apertura de un caso no descarga VTK grandes automáticamente.
- Las alertas de disco aparecen antes de que SU2 falle por falta de espacio.

### Usabilidad

- En menos de tres acciones se llega del dashboard al gate fallido y su
  evidencia.
- Un investigador puede identificar condiciones, malla, solver, fluid model,
  commit y checkpoint de cualquier resultado desde una sola pantalla de caso.
- No hay texto truncado ni controles que cambien de tamaño entre estados.
- Teclado, contraste, focus y texto complementan toda codificación por color.

### Seguridad

- Pruebas de inyección en nombres, rutas y campos de configuración no ejecutan
  comandos arbitrarios.
- Sólo se accede a rutas registradas dentro de las raíces permitidas.
- La cancelación termina todo el grupo MPI y deja un audit event.
- La UI no expone credenciales, variables secretas ni paths privados en
  paquetes exportados.

## 13. Entregables esperados del agente implementador

1. ADRs para arquitectura, launcher, artifact store y actualización en vivo.
2. Esquemas versionados y migraciones.
3. Wireframes de las pantallas principales antes de conectar ejecución.
4. Parser SU2 probado contra logs steady, URANS, éxito, warning y fallo.
5. MVP read-only sobre este repositorio antes del launcher.
6. Threat model específico para Windows/WSL/MPI.
7. Pruebas unitarias, integración y end-to-end con un caso diminuto.
8. Manual de operación y recuperación sin depender de conocimiento tribal.

La interfaz debe hacer más fácil ejecutar el estudio, pero sobre todo más
difícil confundir factibilidad numérica con verdad física.
