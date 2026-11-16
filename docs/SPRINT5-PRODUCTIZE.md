# Sprint 5 — Productize (HU-15 y HU-16)

Rama exclusiva: `feat/sprint-5-productize`. Los sprints 1–4 se mantienen intactos en `main`.

## Alcance implementable de esta iteración

- Organizaciones y membresías con roles `owner`, `admin`, `developer` y `viewer`.
- Aislamiento en **todos** los endpoints de proyectos a través de una comprobación centralizada; migración compatible de proyectos anteriores a espacios personales.
- Invitaciones de un solo uso, ligadas al correo y con vencimiento.
- Auditoría de acciones relevantes sin registrar tokens ni código fuente.
- Reportes históricos y exportación CSV con protección frente a fórmulas.
- Planes y cuotas locales verificables (proyectos, usuarios, ejecuciones), **sin procesamiento real de pagos**.
- Consola Angular 22 en componentes separados, sin sustituir el branding ni el flujo de trabajo existente.

## Límites explícitos

La base sigue siendo SQLite para las pruebas locales del MVP. Migrar a PostgreSQL requiere otro cambio de infraestructura, migraciones verificadas y pruebas bajo concurrencia antes de habilitar múltiples workers SaaS. Los planes están aprovisionados en servidor: no existe checkout, facturación fiscal ni cobro de tarjetas. El GitHub OAuth existente es individual; la creación automática de PR de organización queda pendiente. Los workers Docker locales no deben ejecutar código de clientes no confiable en producción.

## Verificaciones de aceptación

- Un usuario de otra organización no puede ver, exportar ni mutar un proyecto por adivinar su ID.
- Viewer puede consultar sin modificar; Developer puede ejecutar operaciones autorizadas; Admin/Owner gestionan el equipo y las aprobaciones sensibles.
- El propietario no puede eliminarse ni degradarse.
- Los registros de auditoría y los informes no incluyen credenciales ni contenido de código.
- Los proyectos históricos siguen accesibles para sus propietarios.
- Las cuotas no se cambian mediante APIs públicas de autoservicio.

La entrega a `main` **no es automática**; los commits se publican directamente en la rama de Sprint 5.
