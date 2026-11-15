# LegacyLift — Sprint 3: Plan & Prepare

> Base obligatoria: Sprint 1 + UI/UX + branding + Angular 22 + logos + Sprint 2 + fix sesiones + fix interacciones. Cada parche de Sprint 3 depende del anterior.

## Historias implementadas

| Historia | Alcance entregado | Límite explícito |
|---|---|---|
| HU-08 | Modernization Blueprint validado, versionado (revisiones inmutables), edición visual de title/strategy/goal/risk/acceptance y waves con dependencias, JSON y Markdown. | La arquitectura objetivo no está garantizada por IA; la propuesta estática es revisable. |
| HU-09 | Registro de Migration Packs, compatibilidad evaluada en servidor, aprobación independiente de Blueprint y waves, selección de wave activa. | Solo `safe-refactor@1.0` está habilitado; las migraciones entre lenguajes siguen en catálogo como **planificadas, no ejecutables**. |
| HU-10 | Inventario de suites conocidas, baseline de comprobaciones estáticas, propuestas de casos de IA que requieren revisión, consentimiento de ejecución por snapshot/plan/wave. | La ejecución de tests del repositorio solo existe para **Python unittest** en Docker local de desarrollo y está desactivada por defecto. No se ejecuta ni implementa automáticamente un caso de prueba propuesto. |

## Pantallas Angular

La navegación superior del workspace ahora usa nueve pestañas: **Fuente**, **Discover**, **Understand**, **Assess**, **Plan**, **Baseline**, **Modernize**, **Verify** y **Evidencias**. La barra permanece visible (*sticky*) y se desplaza horizontalmente en pantallas pequeñas. Los controles de cada fase comparten el panel de acciones. La información persistente del proyecto permanece en los indicadores superiores.

Las vistas de Sprint 3 están organizadas en `frontend/src/app/features/planning/` con `.component.ts`, `.component.html` y `.component.css` junto a cada componente. Los estilos específicos no se añaden a CSS global.

## Flujo de aceptación

1. Importar un proyecto y completar Discover, Understand y Assess.
2. Generar **Plan**. Abrir **Plan**, revisar el Blueprint, editarlo y guardar la revisión.
3. Aprobar el **Blueprint**. Consultar la compatibilidad de sus waves con los packs disponibles.
4. Aprobar una wave compatible y seleccionarla. La aprobación de una wave dependiente exige aprobar primero sus predecesoras.
5. Abrir **Baseline**. Ver la lista de tests y los resultados disponibles. Autorizar ejecución solo si se desea utilizar el worker.
6. Si se seleccionó Claude/Codex y existe consentimiento de envío de código para ese proveedor y snapshot, solicitar casos de prueba de IA; revisar las propuestas individualmente. **No son tests ejecutables**.
7. Ejecutar **Baseline** y revisar `baseline.md` / `baseline.json`. Si Docker no está habilitado, `tests.status=not_run`.
8. Modificar el Blueprint: crea una nueva revisión, revoca aprobaciones y deja inválidos baseline y migraciones previas.
9. Probar Modernize solo con una wave aprobada y pack operativo, confirmando que los archivos transformados pertenecen a la wave.

## Worker para código legado: decisión arquitectónica

**Solo desarrollo local:** interfaz `TestWorker`, adaptador `DockerLocalWorker`, sin ejecución del código cargado en FastAPI. Un administrador puede habilitarlo de forma optativa en `.env`:

```dotenv
LEGACYLIFT_ENV=development
LEGACYLIFT_WORKER_MODE=docker-local
LEGACYLIFT_TEST_IMAGE=python:3.12-alpine
```

Precargar la imagen de confianza por separado con `docker pull python:3.12-alpine`; la app nunca ejecuta pull sobre petición de un usuario. Se requiere autorización explícita de la wave, snapshot y revisión de Blueprint activos. Docker usa red deshabilitada, montaje de fuente solo lectura, usuario sin privilegios, todas las capacidades retiradas, root filesystem readonly y límites de CPU, memoria, procesos y tiempo.

**No habilitar `docker-local` para un SaaS abierto o código arbitrario no confiable.** Los contenedores comparten kernel; para ejecución hostil la siguiente etapa requiere VM efímera separada del backend, workers remotos con tokens de operación de un solo uso, cuotas, aislamiento de red, resultados firmados, almacenamiento temporal, auditoría y limpieza. El adaptador remoto y la infraestructura de VM **no están implementados** en el Sprint 3.

No se ejecuta `composer install`, `npm install`, `mvn`, `gradle`, Dockerfiles del repositorio, scripts arbitrarios ni tests de COBOL/PHP/Java automáticamente. Baseline estático y detección de tests funcionan sin Docker.

## Parches y validación

Los tres `.patch` se aplican en orden sobre la versión mencionada:

1. `LegacyLift-S3-01-HU08-Blueprint.patch`
2. `LegacyLift-S3-02-HU09-Migration-Packs.patch`
3. `LegacyLift-S3-03-HU10-Baseline-Workspace.patch`

```bash
cd backend && python -m pytest -q
cd ../frontend && npm run check:architecture && npm run check:ui && npm run check:branding && npm run check:sprint2 && npm run check:session && npm run check:interactions && npm run check:sprint3
npm install && npm run build
```

Los verificadores Node de estructura no reemplazan la compilación Angular ni una prueba real del navegador. Con credenciales externas, probar consentimiento y autenticación OAuth en una instalación local antes de un despliegue público.
