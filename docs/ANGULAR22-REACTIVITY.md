# LegacyLift — Reactividad de Angular 22 (Sprint 2)

## Incidente: login completado sin actualizar la pantalla

La compilación era correcta y las peticiones `POST /api/auth/login`, `GET /api/auth/me` y `GET /api/projects` devolvían 200, pero el formulario seguía en «Procesando…». Los botones «Nuevo proyecto» modificaban `vm.showCreate` sin abrir el diálogo y, por tanto, no aparecían solicitudes de creación en Network.

**Causa:** en Angular 22 los componentes son `OnPush` por defecto. El `WorkspaceFacade` había conservado un gran número de campos mutables ordinarios al migrar desde Angular 20; cambiar una propiedad de un servicio desde un callback de HTTP, un evento de otro componente o un job de SSE no notificaba a los componentes que la mostraban.

## Contrato del estado compartido

- Las propiedades de `WorkspaceFacade` leídas desde las plantillas son ahora getters/setters respaldados por `signal<T>()`.
- Las plantillas siguen usando `vm.showCreate`, `vm.authenticated`, `vm.projects`, etc. **No hay cambios en los contratos de las features.**
- El getter lee la signal en el contexto del componente y registra su dependencia; el setter notifica automáticamente a las vistas interesadas.
- Para objetos, listas y conjuntos hay que crear una referencia nueva en cada modificación: `this.selected = {...this.selected, code_consent: approved}`, `this.reviewDraft = {...this.reviewDraft, [id]: text}`. Mutaciones in-place no disparan las signals.
- El servicio de sesión conserva el almacenamiento persistente y la distinción entre `401` y errores temporales. Esta corrección es de **renderizado y estado**, no una nueva estrategia de tokens.
- Al cambiar de cuenta, limpiamos proyectos, selección, hallazgos y borradores, e invalidamos respuestas antiguas.

## Pruebas y aceptación en Zorin

```bash
cd frontend
npm run check:session
npm run check:interactions
npm run check:architecture
npm run check:ui
npm run check:branding
npm run check:sprint2
npm run build
npm start
```

Los comprobadores `check:session` y `check:interactions` son pruebas de persistencia de sesión y **contratos estructurales**; `ng build` comprueba las plantillas reales. Sigue siendo necesaria una prueba manual de navegador (idealmente automatizada más adelante con Playwright):

1. Vaciar sesión mediante «Cerrar sesión»; iniciar sesión y verificar que «Procesando» desaparece sin recargar.
2. Confirmar que el nombre, lista de proyectos y notificaciones aparecen sin `F5`.
3. Pulsar «Nuevo proyecto» en sidebar y en estado vacío: el modal debe abrirse sin HTTP aún.
4. Introducir nombre y sistema; enviar y observar `POST /api/projects` (200/201) y el proyecto nuevo en el sidebar.
5. Cerrar modal, abrir guía, seleccionar proyecto y verificar que la UI cambia inmediatamente.
6. Recargar; debe permanecer autenticado y recuperar el nombre desde `/api/auth/me`.
7. Simular caída temporal de backend: no debe revocar la sesión por un 502.

Para una instancia pública posterior, la persistencia de bearer tokens en `localStorage` sigue siendo una **limitación de seguridad**. Planificar cookies `HttpOnly` + protección CSRF antes de habilitar acceso externo.
