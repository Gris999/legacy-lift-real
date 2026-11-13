# Alcance real implementado — LegacyLift MVP v0.1

> Basado en la visión original: **Discover → Understand → Assess → Plan → Modernize → Verify**.

El MVP implementa un **recorrido vertical de los sprints 1–4**, suficiente para una prueba académica
con el repositorio de ejemplo; no equivale a dar por terminadas todas las historias originales.

## Sprint 1 — Ingest (actualizado con HU-01–HU-04)

- Acceso al workspace mediante un único secreto largo.
- Crear/listar proyecto, elegir IA al crear el proyecto.
- Subir ZIP validado con límites y generador de snapshot SHA-256.
- Progreso de fase vía polling y estados persistidos.
- **Pendiente:** ingesta directa desde GitHub, usuarios múltiples, organizations y RBAC.

## Sprint 2 — Understand (vertical implementada)

- Discover: scanner determinista de extensiones, módulos, archivos y findings heurísticos.
- Understand/Assess: plantilla Markdown por fase, motor Codex/Claude o modo demo marcado sin IA.
- Inventario JSON incluye grafo mínimo de dependencias; no es una base de grafos ni grafo visual interactivo.
- **Pendiente:** análisis semántico multi-stack exhaustivo, métricas de complejidad robustas y revisión humana de hallazgos.

## Sprint 3 — Plan & Prepare (vertical implementada)

- Blueprint Markdown con una wave, pack limitado, aprobación humana.
- Baseline de SHA-256 + chequeos Python/JSON y tests opcionales Docker.
- **Pendiente:** selección gráfica de packs y waves múltiples, pruebas basadas en tráfico real.

## Sprint 4 — Modernize Safely (vertical implementada)

- Candidato separado; adaptador Codex con `workspace-write`, Claude con cambios de archivos JSON validados.
- Demo local determinista sobre Python, diff, validación, aprobación/rechazo, rollback y descarga ZIP.
- Verificación estática por defecto. Con Docker se pueden ejecutar tests Python con red bloqueada.
- Score solo cuando hay verificaciones comparables; ausencia de evidencia se indica explícitamente.
- **Pendiente:** dual-run genérico, sandbox multiusuario endurecido, despliegue automático y confidence estadístico.

## Sprint 5 — Productize (no implementado)

Organizaciones, roles, PostgreSQL multi-tenant, billing, S3, Vault, event bus, workers
realmente distribuidos, auditoría avanzada y configuraciones enterprise.

## Pruebas realizadas para esta entrega

- `pytest`: API de autenticación, alta y carga, pipeline end-to-end determinista,
  prevención de ZIP traversal, validación de ediciones de Claude.
- CLI Codex, cuota de ChatGPT y la API Claude **no han sido probados con credenciales reales aquí**.
- El frontend Angular no se pudo compilar aquí porque no estuvieron disponibles las dependencias npm.

Los resultados del examen deben demostrar la app ejecutándose y las rutas elegidas en la máquina anfitriona.

### Sprint 1 extendido (2026-11-13)

- **HU-01**: registro de usuarios con código de instalación para el primer administrador, PBKDF2, sesiones revocables, aislamiento por usuario, acceso y cierre de sesión.
- **HU-02**: edición de proyecto, integración GitHub OAuth App con PKCE S256, `repo` scope, cifrado Fernet y selección de repositorios privados/públicos. El backend clona por HTTPS sin exponer credenciales al navegador.
- **HU-03**: snapshots archivados bajo `data/projects/<id>/snapshots/<snapshot-id>/source`, manifiesto SHA-256 por archivo, commit para Git, historial y snapshot activo; se conserva la ruta `snapshot/` como copia activa para no romper las fases posteriores.
- **HU-04**: ingesta y escaneo automáticos mediante jobs persistentes, reintentos, estado/progreso por etapa, SSE autenticado mediante `fetch`, polling de respaldo. La cancelación solo se admite cuando el job aún está en cola.

**Caveats reales**: OAuth GitHub requiere OAuth App propia y callback HTTPS en despliegue remoto. Las pruebas de conexión GitHub incluyen simulación; no está verificada autorización contra una cuenta real. SSE es por proceso y DB polling, no un broker distribuido. Escaneo limitado a 300 archivos/12 MB. Snapshot archivado protegido por la app, no contra el propietario del filesystem.
