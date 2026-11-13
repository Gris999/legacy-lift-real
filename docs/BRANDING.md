# Identidad LegacyLift — implementación UI

**Fuente oficial:** [Proyecto-Software-I/frontend, rama `feat/29-branding`, carpeta `public/branding`](https://github.com/Proyecto-Software-I/frontend/tree/feat/29-branding/public/branding).

## Qué proviene de los recursos reales

- Los exportados `logo-dark` y `symbol-dark` se usan sobre fondos oscuros (trazo claro); `logo-light` y `symbol-light` sobre fondos claros (trazo oscuro).
- La identidad provista es **monocromática**. No se dedujo ni inventó un color primario corporativo adicional.
- Iconos de navegador y Apple/Android proceden de `favicon/`; el favicon también se ajusta al tema de la interfaz.
- Los archivos se descargan en `frontend/public/branding/official` **sin modificar las imágenes** y verificando la SHA de blob Git de cada archivo. `npm start`, `npm run build` y `npm run build:dev` sincronizan primero los recursos, usando caché local cuando ya están descargados.

## Colores de interfaz, no una guía corporativa oficial

El directorio original contiene recursos visuales, no una guía de color/espaciado. Los valores de `src/styles/tokens.css` son **decisiones UI propuestas**, alineadas con el negro/blanco del logotipo. El acento neutro se define por `--color-accent`, y el contraste del texto del botón con `--color-on-accent`. Los colores verdes, rojos y azules se reservan para **estados**, no para la identidad de marca.

## Cambiar el tema

`ThemeService` es la fuente única de verdad. Inicialmente respeta `prefers-color-scheme` y después la elección guardada en `localStorage` (`legacylift_theme`). Actualiza `data-theme` en el elemento raíz; ningún componente funcional debe guardar su propia copia del modo.

## Reglas para futuros sprints

1. Usar `<ll-brand-logo variant="full|symbol"/>`. Solo para fondos permanentemente oscuros, `[inverse]="true"` fuerza la imagen clara del logo. **No dibujar ni reconstruir el isotipo** con iconos o texto.
2. No usar colores hexadecimales en páginas nuevas: consumir tokens semánticos de `tokens.css`. Para un tono nuevo, añadir una pareja oscura/clara y comprobar contraste.
3. Usar los componentes `ui/shared` para acciones, estados y métricas; Material Symbols de Google Fonts únicamente para iconos funcionales, **no para sustituir el logotipo**.
4. No modificar los SVG/PNG/WebP oficiales. Si cambia la rama, revisar primero los archivos y hashes esperados de `scripts/sync-branding.mjs` antes de actualizarlos.
5. Validar con `npm run check:ui`, `npm run check:branding`, `npm run build` y comprobación manual en ambos temas a 360px, 768px y desktop.

## Primera instalación

```bash
cd frontend
npm run sync:branding   # requiere acceso a GitHub la primera vez
npm run check:ui
npm run check:branding
npm run build
npm start
```

Si no hay Internet, y ya existen imágenes sincronizadas verificadas, el comando funciona desde caché. No se incluye una versión redibujada de la marca para suplir imágenes oficiales ausentes.


## Actualización: logos recortados entregados por el equipo

La marca completa se sirve desde `frontend/public/branding/custom/logo-dark.webp`
(blanco para fondos oscuros) y `logo-light.webp` (negro para fondos claros).
Son variantes transparentes y recortadas de los dos WebP proporcionados.
La segunda imagen original venía casi blanca sobre fondo blanco y con un bloque oscuro
ajeno al logotipo; para obtener contornos iguales en los dos temas se reutilizó
la silueta precisa de la primera imagen, tintada en negro/blanco.

Los logos completos ya **no** se descargan en `sync:branding`: están versionados
en el frontend. La sincronización externa queda para favicons e isotipos.
No volver a usar zoom, posiciones absolutas ni recorte del lienzo en CSS.
Utilizar siempre el componente compartido `<ll-brand-logo>` en pantallas nuevas.
