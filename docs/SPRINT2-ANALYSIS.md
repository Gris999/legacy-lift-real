# Sprint 2 — Análisis basado en evidencia

## Discover (HU-05)
Escáner extensible en `backend/app/analysis/scanner.py` sin ejecutar código importado.
Incluye PHP, JS, TS, Python, Java, COBOL y lenguajes auxiliares; COBOL usa inspección léxica de `COPY`, `CALL`, `PROGRAM-ID` y secciones, no un parser semántico completo.
Los porcentajes por lenguaje se calculan por **bytes de archivos con extensión reconocida**; no equivalen a GitHub Linguist. El inventario se conserva por `snapshot_id` y se publican eventos `analysis-progress` durante el escaneo.

Límites por defecto: `LEGACYLIFT_MAX_ZIP_MB=64`, `LEGACYLIFT_MAX_SOURCE_MB=128`, `LEGACYLIFT_MAX_FILES=5000`, `LEGACYLIFT_MAX_FILE_MB=5`. No configurar sin evaluar capacidad de RAM y disco.

El API `GET /api/projects/{pid}/analysis/discover` devuelve análisis asociado al snapshot activo y último progreso conocido.

## Seguridad
No se ejecuta código del repositorio. Las importaciones ZIP siguen rechazando rutas inseguras, symlinks y secretos de nombres conocidos. Análisis estático heurístico no equivale a auditoría de seguridad.

## Understand (HU-06)
`GET /api/projects/{pid}/analysis/files` lista archivos reconocidos. `PUT /analysis/selection` guarda una selección válida por snapshot; cambiarla invalida análisis descendientes.
`POST /api/projects/{pid}/analysis/consent` solicita permiso **explícito por snapshot y proveedor**. La selección limita los fragmentos incluidos en las solicitudes de análisis. Codex ejecuta Understand/Assess en una copia temporal con solo los archivos seleccionados, como medida adicional; no es sandbox de contenedores ni garantiza aislamiento del host. Plan y Modernize también exigen autorización; Modernize trabaja sobre la copia completa del candidato.

Los lotes de código y archivos que quedaron fuera figuran en `understand.json`. Por defecto, máximo 3 lotes de 26000 caracteres para Understand (`ANALYSIS_MAX_AI_BATCHES`, `ANALYSIS_BATCH_CHARS` configurables; el límite ambiental prevalece).
Reglas de negocio de IA son **propuestas no confirmadas**; se validan rutas y líneas de evidencia, no la semántica. `GET/PATCH /analysis/reviews` permite confirmar, descartar y comentar, preservando la decisión por snapshot.

## Assess (HU-07)
`assessment.json` y `assessment.md` contienen métricas contadas, reglas heurísticas y recomendaciones. `confidence_score` es `null` sin baseline/calibración. Las propuestas de IA sin evidencia localizable se omiten; las aceptadas siguen pendientes de revisión humana. Se publican métricas parciales antes de que termine la consulta de IA.

Las fases Understand y Assess son independientes y reproducibles sobre el snapshot activo, pero la aprobación de un hallazgo **no equivale** a aprobación de un Modernization Blueprint o de una migración.

## Flujo de interfaz
Tras importar ZIP o GitHub, se muestran en tiempo real porcentajes aproximados de lenguajes por bytes. Discover presenta un grafo seleccionable de módulos. Los controles de privacidad y selección aparecen antes de las acciones de IA; una cola de hallazgos permite revisión humana. Assess ofrece métricas y estrategias con indicación de evidencia y límites.

## Límites pendientes
- COBOL se analiza léxicamente; no se parsean semánticamente copybooks, CICS, JCL ni dialectos particulares.
- El grafo representa dependencias locales detectadas estáticamente; no llamadas dinámicas.
- SQLite y un pool local siguen siendo adecuados para una demo/instancia única; distribución multi-worker queda para Productize.
- La selección reduce lo enviado en prompts de análisis; no es una DLP ni redacción automática de secretos embebidos en código. No importar repositorios con secretos sensibles.
- La actualización progresiva se basa en eventos y polling, no representa streaming token a token de cada modelo.

La tabla `phase_runs` incorpora `snapshot_id` para nuevas ejecuciones; ejecuciones antiguas permanecen con valor `NULL` durante la migración sin inventar procedencia.
