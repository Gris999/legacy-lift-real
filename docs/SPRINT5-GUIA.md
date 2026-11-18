# Sprint 5 — Organización, permisos, auditoría y reportes

Implementado directamente en la rama \`feat/sprint-5-productize\` del repositorio \`Proyecto-Software-I/legacy-lift-real\`. Se preservan los componentes compartidos, los logos y las fases de los Sprints 1–4.

## Instalación de desarrollo (Zorin/Linux)

Usa un clon o copia de seguridad antes de cambiar de rama:

\`\`\`bash
git fetch origin
git switch feat/sprint-5-productize
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q tests/test_s5_productize.py tests/test_auth.py tests/test_security.py tests/test_s4_delivery.py
uvicorn app.api:app --host 127.0.0.1 --port 8000
\`\`\`

En una terminal distinta:

\`\`\`bash
cd frontend
npm ci
npm run check:sprint5
npm run build
npm start
\`\`\`

Mantén tus variables actuales \`LEGACYLIFT_DATA_DIR\`, \`LEGACYLIFT_BOOTSTRAP_SECRET\`, credenciales de IA y configuración de GitHub en un \`.env\` local. Nunca publiques secretos en Git. Antes de iniciar por primera vez con una base existente, realiza una copia del directorio de datos: la inicialización crea tablas adicionales y enlaza proyectos previos al espacio personal de sus propietarios.

## Cómo usarlo

1. Accede con tu cuenta existente. El backend crea automáticamente un **espacio personal** y asocia tus proyectos históricos.
2. En la barra superior, abre **Organizaciones**. Allí puedes crear un equipo, consultar actividad y cuotas, exportar CSV y revisar auditoría.
3. Selecciona la organización en el diálogo **Nuevo proyecto**. Las listas de proyectos muestran solamente aquellos de organizaciones donde eres miembro.
4. Owner/Admin pueden invitar por correo y rol. Se devuelve un **código aleatorio, de un solo uso y válido por siete días**; compártelo mediante un canal privado. No hay servicio de correo saliente.
5. El invitado puede crear una cuenta en **Tengo una invitación**, aunque el registro público esté cerrado, o aceptar el código desde la consola si ya tiene cuenta.

## Roles y límites

| Rol | Lectura | Ejecutar, editar y crear proyectos | Administrar miembros | Aprobar decisiones sensibles |
| --- | --- | --- | --- | --- |
| Owner | Sí | Sí | Sí | Sí |
| Admin | Sí | Sí | Sí | Sí |
| Developer | Sí | Sí | No | No |
| Viewer | Sí | No | No | No |

Los cambios de rol y la expulsión no permiten degradar al propietario. Las aprobaciones y consentimientos de las fases existentes ahora requieren Admin/Owner. Cada organización tiene un plan \`starter\` por defecto (10 proyectos, 3 usuarios, 100 ejecuciones/mes); los contadores se obtienen de operaciones ya persistidas. Las cuotas de creación y de ejecución se verifican en el backend; los planes Team/Enterprise son **catálogos de capacidades**, sin compra o cambio público de plan.

## Reportes y auditoría

- Endpoints: \`GET /api/organizations\`, \`GET /api/organizations/{id}/reports\`, \`/reports.csv\`, \`/usage\`, \`/audit\`.
- Los reportes muestran proyectos, snapshots, fases, intentos y decisiones. El CSV neutraliza nombres que comienzan como fórmulas de hojas de cálculo.
- La auditoría de mutaciones almacena tipo de acción y recurso, jamás cuerpos HTTP, credenciales o código.
- La auditoría es **best effort y no es un log inmutable/a prueba de manipulación**. Para cumplimiento empresarial se requiere un almacén externo append-only.

## Límites antes de producción

La base continúa en **SQLite**. No se implementó todavía la migración a PostgreSQL ni se validó el uso de varios workers con transacciones distribuidas. Los tokens siguen en \`localStorage\`; para un SaaS público hay que pasar a cookies HttpOnly con defensa CSRF. El billing está en estado **no configurado**: no hay Stripe, cobro por tarjeta, suscripciones pagadas ni facturas. GitHub OAuth ya existe por cuenta; no se creó aún la integración para Pull Requests automáticos de organización. Los workers que ejecutan código externo necesitan separación por VM y controles operativos adicionales.

Este sprint añade capacidades de operación y gestión de equipos sobre el MVP, **no equivale a certificación enterprise o despliegue SaaS productivo**.
