# LegacyLift frontend — arquitectura mediana (Angular 22)

## Estructura

- `core/api`: capa HTTP, DTO e interceptor; componentes nunca construyen rutas API.
- `core/state/workspace.facade.ts`: estado y coordinación del flujo actual, SSE y polling; no tiene plantillas ni CSS.
- `core/theme`: única fuente de verdad del tema.
- `features/auth`: login y registro.
- `features/shell`: composición, sidebar y topbar.
- `features/projects`: dashboard, ingesta Git/ZIP, snapshots y diálogos de proyecto.
- `features/pipeline`: etapas, decisiones y ejecución.
- `features/artifacts`: lectura/exportación de evidencias.
- `shared/ui`: componentes reutilizables sin llamadas HTTP. Cada componente tiene carpeta con `.ts`, `.html`, `.css`.
- `src/styles`: **solo** tokens, reset y primitivas compartidas (botones, inputs, utilidades de formularios). Ninguna regla específica de una feature va aquí.

## Reglas que deben seguir nuevos sprints

1. Componentes `standalone`, `inject()` y `templateUrl`/`styleUrl` en carpetas por feature.
2. Nunca generar nuevos CSS globales para formularios/paneles de feature. Mantenerlos junto al componente.
3. Reutilizar `llButton`, `ll-icon`, `ll-status-badge`, `ll-metric-card`, `ll-dialog`, `ll-section-heading`, `ll-brand-logo`.
4. El `WorkspaceFacade` mantiene el comportamiento previo sin refactor masivo de reactividad; introducir señales o stores locales gradualmente y con pruebas de regresión.
5. Cambios de dominio/HTTP van a `core/api` y al backend, no a HTML ni a servicios de UI.
6. No modificar el branding oficial: `npm run sync:branding` valida integridad.
7. Antes de integrar: `npm run check:architecture`, `npm run check:ui`, `npm run check:branding`, `npm run build` y pruebas backend.

## Versiones

Angular 22.2, TypeScript 6.0, Node.js compatible (22.22.3+, 24.15+ o 26.x); RxJS 7.8.
Mantiene `Zone.js` durante esta migración para preservar el comportamiento de `WorkspaceFacade` y actualizar plantillas con sus observables y SSE. La migración zoneless es **otro cambio**, requiere señales y pruebas E2E.

## Logo

`ll-brand-logo` es el único componente autorizado para usar imágenes de identidad corporativa. Se usa `size="hero"` para login (hasta 430px), y `size="sidebar"` en navegación (hasta 242px). El componente escoge el recurso claro/oscuro según el tema y recorta **solo por CSS** los márgenes transparentes del lienzo cuadrado original; evita limitar la imagen a 61px de alto.
