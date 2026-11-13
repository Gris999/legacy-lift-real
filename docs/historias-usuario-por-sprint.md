# LegacyLift AI — Historias de usuario compactas por sprint

> **Understand first. Modernize safely.**

**Versión:** 3.0 · 11 de noviembre de 2026  
**Base:** backlog maestro y agrupación original de **5 sprints funcionales**.  
**MVP de examen:** sprints 1–4; Sprint 5 registrado como evolución futura.  
**Sprint 1 actualizado:** usuarios reales con proyectos privados por usuario y GitHub OAuth; siguen sin existir organizaciones, RBAC de equipo ni facturación.

## Reglas comunes

- Cada historia es **vertical y demostrable** en Angular + backend; se termina con pruebas y evidencia de punta a punta, no solo con pantallas.
- Las fases originales se mantienen: **Discover → Understand → Assess → Plan → Modernize → Verify**. La ingesta se realiza antes de Discover y la preparación de baseline antes de Modernize.
- El usuario **no escribe prompts**: el backend carga plantillas versionadas y pasa archivos/artefactos entre etapas. Los resultados y errores se guardan.
- Nunca se altera la fuente original; los planes y las migraciones exigen **aprobaciones separadas**.
- Se diferencian hallazgos observados, inferencias de IA y verificaciones ejecutadas. Ausencia de pruebas significa **sin evidencia suficiente**, no éxito.
- Los procesos largos muestran estado y permiten reintentar; el agente opera en un workspace aislado, con comandos autorizados.
- OpenSpec se recomienda para cambios de contratos, seguridad, persistencia o ejecución que alteren el alcance acordado.

## Sprint 1 — Ingest

**Meta:** acceder a la app, cargar un sistema legado y obtener una versión reproducible.  
**Fases de origen:** Foundation, Projects & Legacy Systems, Source Ingestion y Jobs.

| ID | Historia | Criterios de aceptación |
|---|---|---|
| **HU-01** | Como operador, quiero acceder a LegacyLift y ver el estado de Codex CLI, Claude API o demo sin IA. | Registro, inicio de sesión y cierre con sesiones revocables; el backend gestiona credenciales de Codex en el host y CLAUDE_API_KEY en FastAPI; no las expone a Angular. |
| **HU-02** | Como operador, quiero crear un proyecto, registrar su sistema legacy y agregar el código desde un ZIP o fuente de ejemplo. | Se guarda origen y nombre; se valida el ZIP; se conserva una copia de trabajo sin sobrescribir el original. |
| **HU-03** | Como operador, quiero escanear la fuente y generar un `SourceSnapshot`. | Snapshot asociado a proyecto con commit/hash y manifiesto; inventario básico de archivos, tecnologías y dependencias; versión de referencia inmutable. |
| **HU-04** | Como operador, quiero consultar progreso y errores del scanning y futuras operaciones. | Estados pendiente/ejecutando/completado/fallido; consulta periódica del progreso; resultados persistidos y reintentos controlados. |

**Demo del sprint:** iniciar sesión → proyecto/sistema → fuente → escaneo → snapshot → inventario.  
**Cierre:** un repositorio real queda listo para analizarse sin perder su versión de origen.

## Sprint 2 — Understand

**Meta:** convertir código en comprensión, evaluación y recomendaciones basadas en evidencia.  
**Fases de origen:** Discover, Understand, Assess y AI Foundation.

| ID | Historia | Criterios de aceptación |
|---|---|---|
| **HU-05** | Como ingeniero, quiero ejecutar **Discover** para conocer componentes y problemas del snapshot. | `AnalysisRun` lógico por fase; inventario ampliado, dependencias, findings y métricas con referencias a archivos; no modifica código. |
| **HU-06** | Como ingeniero, quiero ejecutar **Understand** para documentar arquitectura y reglas del sistema. | Documentación Markdown, mapa sencillo de nodos/relaciones, reglas/procesos con evidencia; inferencias sin soporte quedan identificadas para revisión. |
| **HU-07** | Como ingeniero, quiero ejecutar **Assess** para conocer riesgos y estrategias de modernización. | Assessment explicable (deuda, riesgo, mantenibilidad/testabilidad) y recomendaciones por módulo; scores no aparecen sin evidencias; IA usa prompts versionados automáticamente. |

**Demo del sprint:** snapshot → Discover → documentación/grafo → findings/assessment → recomendaciones.  
**Cierre:** el operador puede explicar qué tiene, cómo funciona y qué conviene modernizar, con artefactos descargables.

## Sprint 3 — Plan & Prepare

**Meta:** tomar decisiones antes de tocar el código y crear evidencias comparables.  
**Fases de origen:** Plan y Migration Packs & Preparation.

| ID | Historia | Criterios de aceptación |
|---|---|---|
| **HU-08** | Como operador, quiero generar un **Modernization Blueprint** para elegir una modernización progresiva. | Arquitectura actual/objetivo, estrategia por unidad, alcance, riesgos, priorización y **una Migration Wave** ejecutable con sus dependencias. |
| **HU-09** | Como operador, quiero aprobar el plan y seleccionar el **Migration Pack** compatible con el sistema. | La decisión queda registrada; un plan rechazado no permite transformación; el pack muestra escenario, versión, prompts y validadores realmente soportados. |
| **HU-10** | Como ingeniero, quiero generar un **Behavioral Baseline** y preparar tests antes de migrar. | Evidencia de entradas/salidas o suite existente asociada al snapshot; checks reproducibles; cualquier ausencia de baseline/tests queda señalada. |

**Demo del sprint:** assessment → plan + wave → revisión/aprobación → pack → baseline/tests.  
**Cierre:** existe un plan aprobado y una referencia verificable del comportamiento antes de la transformación; todavía no se ha modificado la fuente original.

## Sprint 4 — Modernize Safely

**Meta:** ejecutar una transformación real, examinar sus cambios y demostrar qué se pudo verificar.  
**Fases de origen:** Modernize y Verify.

| ID | Historia | Criterios de aceptación |
|---|---|---|
| **HU-11** | Como ingeniero, quiero ejecutar una **Migration Run** conforme al plan aprobado. | Solo modifica una copia/branch; usa pack y wave aprobados; registra estado, archivos transformados, errores y artefactos. |
| **HU-12** | Como ingeniero, quiero revisar el **diff** y los logs para entender el resultado. | Comparación antes/después por archivo, resumen por cambio y descarga de patch; el resultado continúa siendo candidato hasta aprobación. |
| **HU-13** | Como ingeniero, quiero ejecutar **Verify** y comparar la versión candidata con el baseline. | Build/lint/tests/validadores permitidos; comparación de pruebas Python con Docker solo si está activada; dual run queda pendiente; divergencias y evidencia visibles; confidence score orientativo sin falsear checks no ejecutados. |
| **HU-14** | Como operador, quiero aprobar/rechazar la migración y poder recuperar o entregar una versión. | Decisión humana registrada; rechazo/rollback restituye la copia anterior; aprobación permite exportar ZIP/patch, documentación y reporte de validación. La entrega no implica despliegue automático a producción. |

**Demo del sprint:** plan aprobado → transformación → diff → Verify/baseline → confidence → aprobación o rollback → exportación.  
**Cierre:** modernización real y trazable, con resultado verificable; el original sigue intacto.

## Sprint 5 — Productize (posterior al examen)

**No es parte del MVP.** Se conserva la etapa del roadmap original para evitar confundir funciones futuras con capacidades entregadas.

| ID | Historia futura | Alcance resumido |
|---|---|---|
| **HU-15** | Como responsable, quiero reportes, auditoría e integraciones para operar y seguir modernizaciones. | Reportes históricos, controles de acceso, trazabilidad avanzada y conexiones Git. |
| **HU-16** | Como administrador de una organización, quiero gestionar miembros, suscripción y políticas empresariales. | Organizations/memberships/RBAC, billing, entitlements, secrets gestionados, despliegues privados y capacidades enterprise. |

**Criterio de inicio:** solo después de estabilizar los cuatro sprints del núcleo; exige rediseñar autorización y multi-tenancy, no habilitarlo solamente desde frontend.

## Secuencia, dependencias y demo final

```text
SPRINT 1    Acceso → Project/LegacySystem → Source → Scan → Snapshot
    ↓
SPRINT 2    Discover → Understand (Knowledge + Docs) → Assess
    ↓
SPRINT 3    Plan → Wave/Pack → Aprobación → Baseline/Tests
    ↓
SPRINT 4    Modernize → Diff → Verify → Confidence → Aprobar / Rollback / Exportar
    ↓
SPRINT 5    Productize (futuro)
```

**Demo académica mínima:** cargar un repositorio de prueba real, producir un snapshot, explicar su arquitectura y reglas, mostrar findings y assessment, aprobar una wave, registrar un baseline, generar una modificación visible, ejecutar las verificaciones posibles, revisar el diff y exportar la evidencia. Ningún paso exige escribir un prompt a mano.

### Definición de terminado del MVP

1. **Trazabilidad:** cada fase conserva `snapshotId`, estado, versión del prompt/modelo cuando corresponde y enlaces a sus artefactos.
2. **Seguridad:** frontend/API accesibles bajo sesión y HTTPS por IPv6; tokens y agente solo en host; ejecución de código con límites y revisión.
3. **Control humano:** el plan y la migración tienen decisiones explícitas e independientes; existe rollback/reintento.
4. **Validación honesta:** tests, baseline y divergencias quedan evidenciados; si no hay suficientes pruebas, se informa y no se afirma equivalencia.
5. **Entrega:** resultados visibles en Angular y descargables (documentación, plan, código propuesto, diff, informe).

### Correspondencia con el backlog original

- **Sprint 1:** sintetiza HU-001–HU-015 (sin administración de organizaciones y roles).
- **Sprint 2:** sintetiza HU-016–HU-025 y HU-031–HU-033.
- **Sprint 3:** sintetiza HU-026–HU-030 y HU-034–HU-036.
- **Sprint 4:** sintetiza HU-037–HU-046.
- **Sprint 5, fuera del MVP:** sintetiza HU-047–HU-058. Los tests en Docker y los resultados de IA deben validarse en el equipo real antes de declarar completos los criterios de aceptación restantes.

Los identificadores **HU-01 a HU-16** pertenecen a esta versión simplificada; no sustituyen los números originales del backlog maestro.
