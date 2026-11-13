# LegacyLift AI — Visión del producto y alcance MVP

> **Understand first. Modernize safely.**

**Versión:** 3.0 · 11 de noviembre de 2026  
**Estado:** alcance académico reducido, basado en la visión, el backlog maestro, los cinco sprints y la arquitectura originales de LegacyLift AI.  
**Propósito:** entregar un recorrido funcional completo, no una plataforma empresarial terminada.

## 1. Visión y problema

**LegacyLift AI** ayuda a comprender, evaluar, planificar, modernizar y verificar sistemas de software existentes mediante un flujo progresivo asistido por IA. No es un conversor de sintaxis ni un chat genérico: antes de cambiar el código reconstruye su estructura y comportamiento; después propone transformaciones limitadas y comprueba sus resultados con evidencia.

Resuelve un problema frecuente del software legado: documentación escasa, reglas de negocio poco visibles, dependencias antiguas y riesgo de introducir regresiones al refactorizar o migrar. El valor del producto es **reducir ese riesgo**, no prometer modernización automática infalible.

La primera versión está destinada a **un desarrollador/evaluador** que moderniza **un sistema pequeño por proyecto** y lo demuestra desde una aplicación web. Mantiene las cuatro preguntas centrales de la visión original:

1. **¿Qué tengo?** Inventario, tecnologías, módulos, dependencias y hallazgos.
2. **¿Cómo funciona?** Arquitectura, relaciones, flujos y reglas de negocio con evidencia.
3. **¿Cómo debería modernizarlo?** Assessment, estrategias, arquitectura objetivo y waves.
4. **¿Cómo sé que es confiable?** Baseline, tests, comparación, resultados, aprobación y reversión.

## 2. Flujo principal obligatorio

Se conservan las **seis etapas originales**; la generación de documentación se integra en **Understand**, no sustituye Assess. La preparación del baseline sucede **antes** de modificar código.

```text
Repositorio / ZIP
    │
    ▼
[1] DISCOVER ─── Inventario + Source Snapshot reproducible
    │
    ▼
[2] UNDERSTAND ─ Arquitectura + conocimiento + documentación
    │
    ▼
[3] ASSESS ───── Hallazgos + riesgos + recomendaciones justificadas
    │
    ▼
[4] PLAN ─────── Blueprint + arquitectura objetivo + wave(s)
    │              + aprobación del plan + pack + baseline + tests
    ▼
[5] MODERNIZE ── Transformación en copia aislada + diff
    │
    ▼
[6] VERIFY ───── Build/lint/tests + comparación con baseline
                   + confidence + decisión humana
                   ├── Aceptar → exportar versión/artefactos
                   └── Rechazar → rollback/reintentar
```

### 1. Discover — ¿Qué existe?

- El operador crea un **Project** con su **Legacy System** y agrega una fuente: repositorio Git accesible o ZIP.
- Se ejecuta una sesión de escaneo y se fija un **Source Snapshot** (commit/hash y copia inmutable de referencia).
- Se produce inventario de archivos, lenguajes, frameworks, dependencias, módulos y puntos de entrada. Errores y progreso son visibles.

**Salida:** manifiesto del snapshot e inventario técnico; todavía no se altera el código.

### 2. Understand — ¿Cómo funciona?

- A partir del snapshot, la IA explica responsabilidades, arquitectura actual, dependencias y flujos relevantes.
- Reconstruye un **grafo de conocimiento mínimo** (nodos y relaciones entre módulos/servicios/archivos) y registra reglas de negocio **con referencias al código**; marca como hipótesis lo no comprobado.
- Genera documentación Markdown: visión técnica, mapa de módulos y reglas/contratos identificados.

**Salida:** documentación y representación de conocimiento consultables y exportables. No se necesita una base de grafos.

### 3. Assess — ¿Qué conviene cambiar?

- Registra **Findings** con severidad, ubicación, justificación y evidencia.
- Evalúa señales disponibles: complejidad observada, deuda técnica, dependencias, mantenibilidad, riesgo y presencia de pruebas.
- Propone una estrategia por componente: **Keep, Stabilize, Encapsulate, Rehost, Replatform, Refactor, Rearchitect, Rewrite, Replace o Retire**, aunque el MVP **solo ejecutará las estrategias que implemente su pack**.

**Salida:** Assessment explicable y recomendaciones priorizadas; ninguna puntuación se presenta como prueba de seguridad.

### 4. Plan & Prepare — ¿Cómo modernizar con control?

- Crea un **Modernization Blueprint** que vincula hallazgos, estrategia, arquitectura actual/objetivo, archivos afectados y criterios de aceptación.
- Divide el trabajo en **Migration Waves** ordenadas; el MVP permite **una wave ejecutable** para la demostración y muestra dependencias/prioridades.
- El operador **aprueba o rechaza el plan** antes de editar código.
- Selecciona un **Migration Pack versionado** apropiado para el repositorio de prueba (detectores, prompts, reglas y validadores); no se anuncian stacks no implementados.
- Prepara el **Behavioral Baseline** con pruebas existentes o casos reproducibles de entrada/salida; si faltan verificaciones, registra explícitamente esa carencia.

**Salida:** plan aprobado, pack elegido, baseline y conjunto de checks; el código original permanece intacto.

### 5. Modernize — ¿Qué cambia?

- Ejecuta una **Migration Run** sobre una rama/copia de trabajo del snapshot, **nunca** sobre la fuente original.
- El agente ejecuta instrucciones específicas del pack para refactorización o transformación soportada, dentro del alcance aprobado.
- Registra archivos modificados, logs, artefactos y **diff** por archivo. El operador puede revisar los cambios.

**Salida:** versión candidata, patch y trazabilidad entre plan, wave, pack y cambios realizados.

### 6. Verify — ¿Conserva el comportamiento?

- Ejecuta **build, lint y tests** cuando el proyecto disponga de comandos reconocidos y permitidos; no ejecuta instrucciones arbitrarias de código desconocido sin revisión/aislamiento.
- Compara los resultados disponibles con el **Behavioral Baseline**; un **dual run** equivalente puede usarse en la demo si el caso lo permite, pero no se finge si no hay infraestructura o entradas comparables.
- Calcula o presenta un **Migration Confidence Score orientativo**, sustentado en checks ejecutados y evidencia. Distingue `aprobado`, `fallido` y `sin evidencia suficiente`.
- El operador **aprueba/rechaza la migración**. Se permite **rollback** a la copia anterior y exportación del resultado aprobado (ZIP/patch, documentación y reporte). En el MVP, **deployment** significa entregar una versión candidata reproducible; no se despliega automáticamente software transformado a producción.

**Salida:** informe de validación, divergencias, decisión humana y artefactos finales.

## 3. Qué preservamos y qué simplificamos

| Concepto original | Decisión en el MVP |
|---|---|
| Project → LegacySystem → Repository → ScanSession → SourceSnapshot | Una pantalla de proyecto/fuente y un snapshot reproducible; la sesión de escaneo queda registrada como una fase. |
| AnalysisRun, Findings, Metrics, Assessment | Ejecuciones por fase; resultados estructurados/Markdown con evidencia. |
| Knowledge Graph + Intermediate Representation | Nodos y edges básicos en JSON; sin ontología universal ni servidor de grafos. |
| Modernization Plan, Architecture, Migration Waves | Un blueprint con arquitectura actual/objetivo y una wave ejecutable. |
| Migration Packs | Un pack implementado y versionado para **un escenario conocido**; arquitectura extensible a otros. |
| Behavioral Baseline, Tests, MigrationRun, ValidationRun | Permanecen en el proceso y deben estar vinculados a la misma versión fuente. |
| Migration Confidence Score, Approvals, Rollback | Se conservan; score basado en evidencia y decisiones explícitas. |
| AIRun, PromptTemplate, Jobs, Reports/Audit | Prompts versionados en archivos; ejecuciones y artefactos con metadatos de origen. |
| Organization, Membership, RBAC, ProjectAccess, multi-tenancy | **Fuera del MVP**; un operador y acceso protegido a una instancia personal. |
| Billing, entitlements, múltiples proveedores, SSO, Enterprise | Aplazados; no se crean tablas vacías. |
| Object storage, Vault, Redis/BullMQ, workers distribuidos | Archivos y procesos locales controlados; sin necesidad de servicios externos. |

La equivalencia buscada es **mantener el recorrido y sus decisiones**, no reproducir todas las entidades, pantallas o variantes de un SaaS empresarial.

## 4. Alcance de la prueba académica

### Incluido

- Aplicación web con **un operador**, sesión propia protegida y proyectos persistentes.
- Fuente ZIP validado (Git como extensión posterior); soporte para un repositorio de prueba de stack conocido.
- Snapshot reproducible e inventario; análisis, documentación, conocimiento, findings y assessment.
- Blueprint, pack, wave, baseline y aprobación de plan.
- Transformación real en copia, diff, checks, comparación y decisión final.
- Reintentos por fase, progreso visible y descarga de artefactos/reportes.
- **Prompts internos automáticos**: el usuario selecciona fase y aprueba decisiones; no escribe instrucciones libres.
- Despliegue **autogestionado en el PC del operador**, accesible mediante IPv6 desde otra red cuando haya conectividad, HTTPS y firewall configurados.

### Fuera del alcance de examen

- Multiusuario, organizaciones, tenancy, invitaciones, administración de roles y seguridad cross-tenant.
- Planes, suscripciones, cobros, facturas, medición comercial de uso.
- Catálogo extenso de lenguajes, conversiones automáticas universales o migración masiva.
- Agregación de muchos proveedores y facturación de clientes mediante sus tokens; el MVP sí incluye Codex CLI y Claude API como dos adaptadores opcionales.
- Migraciones en paralelo, colas distribuidas, microservicios, RLS, S3 y Vault.
- Deployment automático de aplicaciones migradas en infraestructura productiva.
- Garantías de equivalencia sin pruebas o baseline suficientes.

## 5. Arquitectura técnica implementada (MVP 0.1)

```text
Browser remoto -- HTTPS / IPv6 --> Reverse proxy
                                     ├─ Angular 20 (assets estáticos)
                                     └─ /api → FastAPI (solo loopback)
                                                ├─ Auth multiusuario, sesiones revocables (Sprint 1)
                                                ├─ REST + polling de progreso
                                                ├─ Orquestador de fases / prompts
                                                ├─ SQLite + carpetas de proyecto
                                                ├─ Snapshot y candidato independientes
                                                └─ Adaptadores: Codex CLI / Claude API / demo sin IA
                                                               └─ Análisis y modernización
```

- **Frontend:** Angular standalone, UI oscura inspirada en componentes shadcn/ui (estilos propios, no la librería React).
- **Backend:** Python/FastAPI (no Spring Boot). Endpoints en `backend/app/api.py` y servicios desacoplados.
- **Motor IA:** ChatGPT vía **Codex CLI** autenticado en el host mediante `codex login`; Claude mediante **Anthropic Messages API** y `CLAUDE_API_KEY`. El proveedor demo aplica reglas deterministas y no simula una IA.
- **Persistencia:** SQLite para proyectos y ejecuciones; archivos JSON y Markdown en el filesystem. No se usa Prisma.
- **Ejecución:** ThreadPoolExecutor con estado persistido; interfaz que consulta progreso cada pocos segundos. No se afirma que exista SSE o un worker distribuido.
- **Validación:** Python AST/JSON de manera predeterminada. Opcionalmente `unittest` en Docker restringido, si está instalado y se habilita.
- **Despliegue:** el reverse proxy debe gestionar TLS sobre IPv6 y dejar API y ejecutor en loopback. El código original no se modifica.

El modelo académico no es una plataforma multi-tenant ni un servicio seguro para cargar repositorios de desconocidos. Para clientes se requiere endurecimiento, ejecución realmente aislada, autorización por usuario/tenant, observabilidad y colas.

## 6. Persistencia efectivamente implementada

En lugar de generar tablas empresariales antes de necesitarlas, el MVP almacena dos agregados relacionales:

| Tabla | Campos | Responsabilidad |
|---|---|---|
| `projects` | `id`, `name`, `system_name`, `provider`, `source_filename`, `snapshot_hash`, `plan_approved`, `migration_decision`, `created_at` | Contexto único del operador, origen y decisiones |
| `phase_runs` | `id`, `project_id`, `phase`, `status`, `started_at`, `finished_at`, `provider`, `prompt_hash`, `summary`, `error`, `data_json` | Trazabilidad del estado, proveedor, artefacto y evidencia por fase |

En el filesystem se mantienen carpetas de snapshot original, candidato y artefactos. Así se preservan los conceptos originales **Project / SourceSnapshot / AnalysisRun / Blueprint / Baseline / MigrationRun / ValidationRun**, sin duplicar sus entidades como tablas separadas. Las relaciones se vuelven explícitas al evolucionar a PostgreSQL, tenencia y procesos distribuidos.

## 7. Prompts y fases sin escritura manual

El frontend presenta botones **Descubrir → Comprender → Evaluar → Preparar plan → Modernizar → Verificar**. Cada acción ejecuta un contrato del backend: tipo de fase, `snapshotId` y decisión cuando corresponda. El backend carga una plantilla versionada, selecciona los archivos pertinentes, adjunta artefactos previos y envía la tarea al agente.

```text
backend/app/prompts/
  understand.md
  assess.md
  plan.md
  modernize.md
backend/app/inspection.py      # discover y chequeos deterministas
backend/app/pipeline.py        # baseline, acciones, validación, approvals
backend/app/ai.py              # adaptadores Codex CLI / Claude API
```

**Reglas del orquestador:**

1. Cada fase posee **inputs, outputs y permisos** definidos; `Discover`, `Understand`, `Assess` y `Plan` no editan la fuente.
2. Cada etapa utiliza el snapshot fijado y los artefactos **persistidos** de fases anteriores; no depende solo de la memoria conversacional.
3. Las instrucciones de IA se pueden cambiar/versionar en el backend durante el desarrollo, sin cambiar la UI; un prompt no concede permisos que el agente no tenga.
4. `Modernize` requiere un **plan aprobado** y usa una copia de trabajo; `Verify` ejecuta checks explícitos; no permite aceptar si esos checks fallaron, y declara evidencia insuficiente cuando no hay pruebas comparables.
5. Un fallo mantiene el historial, muestra su motivo y permite reintentar la fase sin perder el original.

El operador **puede** añadir notas, pero no son necesarias para completar el proceso. El acceso a ChatGPT mediante OAuth está sujeto a autorización y límites de la cuenta; no implica acceso ilimitado a modelos ni habilita a compartir una suscripción con otros usuarios.

## 8. Plan de entregas

| Sprint original | MVP correspondiente | Resultado verificable |
|---|---|---|
| **1. Ingest** | Acceso local, proyecto, fuente, scanning, snapshot y progreso | Código importado y versión reproducible |
| **2. Understand** | Discover, Understand, Assess y ejecución de IA | Inventario, conocimiento, documentación y recomendaciones |
| **3. Plan & Prepare** | Blueprint, wave, pack, aprobación y baseline/tests | Plan aprobado antes de cualquier cambio |
| **4. Modernize Safely** | Migración, diff, Verify, score, decisión, rollback/exportación | Cambio real con evidencia y salida descargable |
| **5. Productize** | **Posterior al examen** | Reporting avanzado, multiusuario, billing, integraciones, enterprise |

## 9. Criterios de aceptación globales

- Se puede repetir una demo **en un repositorio real de ejemplo**, con fases ordenadas y estados visibles.
- El sistema genera snapshot, documentación, assessment, plan, baseline, diff y reporte de validación, **sin prompts escritos por el operador**.
- El proyecto original permanece intacto y hay dos decisiones humanas diferenciadas: **aprobar plan** y **aprobar resultado**.
- Se registra qué modelo, plantilla y snapshot originaron cada artefacto y qué verificaciones se ejecutaron.
- Un test inexistente, una comparación imposible o un fallo no se presentan como validados; el score incluye cobertura y límites de la evidencia.
- La app se abre por HTTPS desde otra red usando IPv6, con autenticación y sin exponer las credenciales ni el servicio del agente.

## 10. Evolución posterior

Una vez que el flujo sea confiable, pueden incorporarse varios Migration Packs, un Knowledge Graph más rico, workers distribuidos, importación de repositorios privados, pull requests, varios usuarios/organizaciones, RLS, object storage, políticas de retención y capacidades comerciales. Esas características **no bloquean** la prueba académica del núcleo de modernización.

---

### Correspondencia con los documentos anteriores

Este recorte toma como referencia la **visión LegacyLift AI**, el **backlog maestro**, el **plan de cinco sprints**, y las decisiones de **base de datos** y **multi-tenancy** compartidas por el equipo. Conserva el orden y los conceptos de modernización; cambia deliberadamente arquitectura, persistencia y alcance comercial para una instancia académica monousuario.

### Decisiones implementadas del Sprint 1

El Sprint 1 fue ampliado respecto del MVP inicial: cuentas individuales (todavía sin organizaciones
ni roles empresariales), GitHub OAuth App con PKCE, snapshots históricos inmutables con uno activo,
escaneo automático, jobs persistentes y SSE. Estas capacidades son base para posteriores sprints,
pero no equivalen a completar multi-tenancy, GitHub Apps de permisos finos ni workers distribuidos.
