# LegacyLift — Corrección de sesiones (Sprint 2, parche incremental)

## Problema resuelto

El frontend guardaba el bearer en `sessionStorage` y llamaba a `logout()` ante **cualquier** fallo de `GET /api/auth/me`, incluso HTTP 502 o cortes de red. `logout()` revocaba la sesión en SQLite, por lo que una interrupción breve podía expulsar al usuario después del registro e impedir crear proyectos. El nombre visible solo existía en memoria y se perdía hasta que `/auth/me` respondiera.

## Contrato actual

- `AuthSessionService` es la fuente única del token para `HttpInterceptorFn`, SSE y la fachada.
- Guarda `access_token`, `expires_at` y el perfil mínimo (`username`) en `localStorage`, bajo `legacylift_auth_v2`. La expiración es la devuelta por el **backend**, nunca un TTL renovado al recargar.
- Migra automáticamente el `legacylift_session` anterior de `sessionStorage` (el backend validará su vigencia).
- Cuando `/auth/me` responde 200, actualiza nombre y usuario, luego carga proyectos y proveedores.
- Solo HTTP **401** de una petición autenticada invalida el token. Las respuestas 502/503, timeouts, errores de red y errores de otras operaciones muestran el fallo, pero **no revocan la sesión**.
- Se descartan respuestas retrasadas de peticiones pertenecientes a otra sesión para evitar que datos de otro usuario aparezcan después del logout.
- El logout explícito revoca el token en SQLite e inmediatamente limpia el estado local.
- El evento `storage` actualiza otras pestañas si el usuario entra o sale en una de ellas.

## Pruebas

Desde `frontend`: `npm run check:session` (10 casos: persistencia, expiración, migración, nombre, errores y SSE).
También: `npm run check:architecture && npm run check:ui && npm run check:branding && npm run check:sprint2 && npm run build`.

Desde `backend`: `python -m pytest -q`.

Prueba manual de aceptación:

1. Registrar usuario; sin recargar crear un proyecto en modo Demo.
2. Recargar la página: comprobar que siguen el usuario, los proyectos y la sesión.
3. Cerrar el navegador y volver a abrir: el login sigue activo mientras no pasen las 12 horas del servidor.
4. Detener FastAPI durante una consulta `/auth/me` o una recarga; la pantalla debe ofrecer **Reintentar conexión**, sin cerrar la sesión. Reiniciar FastAPI y pulsar reintentar.
5. Cerrar sesión explícitamente; comprobar que deja de estar autenticado también después de recargar.
6. Acceder desde dos pestañas del mismo origen y comprobar la sincronización del logout.

## Seguridad y limitaciones

`localStorage` permite persistencia entre cierres del navegador, pero un script inyectado por una vulnerabilidad XSS podría leer el bearer. Se mantienen tokens opacos, almacenados como SHA-256 en SQLite, revocables y con expiración de 12 horas. Para exponer LegacyLift a Internet, se recomienda **migrar a cookies HttpOnly + Secure + SameSite y protección CSRF**, además de HTTPS y una CSP estricta. Este parche no realiza esa migración porque alteraría los contratos de SSE y GitHub OAuth.

No modifica el servidor, ni `data/`, ni `.env`, ni los contratos HTTP.
