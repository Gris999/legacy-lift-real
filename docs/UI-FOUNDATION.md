# LegacyLift UI — base de diseño del Sprint 1

Esta refactorización modifica únicamente la presentación Angular sobre **los cuatro parches del Sprint 1**; no introduce endpoints, cambia modelos de FastAPI ni altera la secuencia del pipeline.

## Principios

1. **Jerarquía por tarea**: fuente y progreso antes que opciones técnicas; Pipeline y Evidencia como pasos siguientes.
2. **Un componente compartido para un patrón repetido**: no duplicar lógica de botones, estados, avisos, iconos, tarjetas ni diálogos.
3. **Consistencia semántica**: nunca depender solo del color para comunicar estado; todos los estados llevan texto.
4. **Accesibilidad**: `aria-live` en avisos, foco visible, tamaños táctiles adecuados, campos con `label` y títulos de diálogo. Respetar `prefers-reduced-motion`.
5. **Responsive funcional**: el menú móvil se puede abrir y cerrar; nunca ocultar una acción importante solo por el ancho.
6. **Sin romper comportamiento**: importar ZIP, conectar GitHub, historial, jobs SSE/polling, crear/editar proyectos, fases, decisiones y exportar conservan sus handlers y API originales.

## Archivos y responsabilidades

```text
frontend/src/
  index.html               — Google Fonts (DM Sans + JetBrains Mono + Material Symbols Outlined)
  styles.css               — punto único de importación de estilos
  styles/
    tokens.css             — colores semánticos, espaciados, radios, escalas
    base.css               — reset, tipografía, foco, iconos
    components.css         — controles y componentes compartidos
    layout.css             — layouts y composiciones de páginas
    responsive.css         — tablet, móvil y movimiento reducido
  app/
    ui/shared/
      button.directive.ts       — variantes sobre botones nativos, sin interceptar eventos
      icon.component.ts         — Material Symbols, decorativos (acciones deben tener nombre)
      status-badge.component.ts — estado textual + color + icono
      metric-card.component.ts  — KPI con progreso opcional accesible
      notice.component.ts       — error/éxito con rol y acción de descartar
      dialog.component.ts       — overlay, título y cierre consistente
      section-heading.component.ts — encabezados de secciones
    ui/stage-card.component.ts — fase de pipeline
```

## Reglas para siguientes sprints

- Para **nuevas acciones**, usar el atributo `llButton` con `variant` (`primary`, `secondary`, `ghost`, `danger`), sin crear otra clase visual ad hoc.
- Para **iconos**, usar `<ll-icon name="..."/>` con nombres de [Material Symbols](https://fonts.google.com/icons). Su componente es decorativo; si el botón solo lleva un icono, dar nombre accesible al `button`.
- Para **estados**, usar `<ll-status-badge [status]="estado"/>` y extender su mapeo si aparece un nuevo estado; no usar colores solo.
- Para **KPI**, usar `<ll-metric-card>`.
- Para **modales**, usar `<ll-dialog>`; **notificaciones**, `<ll-notice>`.
- Para **estilos**, ampliar los tokens semánticos antes de usar valores sueltos. Estilos globales compartidos a `components.css`; estilos de layout a `layout.css`.
- `api.service.ts` es el único límite HTTP de la vista: nuevos sprints deben colocar su acceso a datos allí o en servicios separados, no directamente en componentes visuales.
- No mover decisiones o pipelines a componentes visuales: el componente visual debe recibir un estado y emitir una intención.
- `npm run check:ui` verifica invariantes del diseño y evita regresiones estructurales comunes. La prueba definitiva sigue siendo `npm run build` y pruebas de navegador/teclado.

## Limitaciones conocidas

- La fuente Material Symbols se descarga de Google Fonts: requiere conexión a Internet; se puede alojar localmente cuando se implante un modo offline.
- La vista principal todavía mantiene coordinación de estado en `AppComponent`. Al añadir nuevas secciones, extraer un *feature container* por sección y dejar los componentes `ui/shared` agnósticos del dominio.
- `ll-dialog` usa el elemento nativo `<dialog>` y `showModal()`, con gestión de foco por el navegador. Los flujos complejos aún necesitan pruebas E2E de accesibilidad.
- El proyecto original no incluye Playwright ni pruebas E2E de Angular. Añadirlas en el sprint de calidad sin acoplarlas a selectores de estilo.

## Integración de identidad y temas

Ver `docs/BRANDING.md`: `BrandLogoComponent`, `ThemeService`, tokens duales y sincronización íntegra de los assets oficiales desde GitHub. Las páginas futuras no deben copiar rutas de PNG ni crear paletas nuevas.


## Angular 22 feature-first refactor

Los estilos globales ahora contienen solo `tokens.css`, `base.css`, `primitives.css`. Los estilos de cada página y componente viven junto a su HTML y TS. Consultar `FRONTEND-ARCHITECTURE.md`.
