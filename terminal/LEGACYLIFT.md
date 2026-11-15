# LegacyLift AI — Terminal (TUI en Go)

Fork de [Crush](https://github.com/charmbracelet/crush) adaptado a LegacyLift AI.
**No es un chat:** no se escriben prompts. Al abrirlo ejecuta automáticamente las fases documentadas
sobre la carpeta actual y guarda cada resultado como un archivo Markdown en `.legacylift/`.

| # | Fase | Artefacto |
|---|---|---|
| 01 | Discover | `.legacylift/01-discover.md` |
| 02 | Understand | `.legacylift/02-understand.md` |
| 03 | Assess | `.legacylift/03-assess.md` |
| 04 | Plan | `.legacylift/04-plan.md` |
| 05 | Baseline | `.legacylift/05-baseline.md` |
| 06 | Modernize | `.legacylift/06-modernize.md` (cambios solo en `.legacylift/candidate/`) |
| 07 | Verify | `.legacylift/07-verify.md` |

- **El código original nunca se modifica**: Modernize trabaja sobre una copia en `.legacylift/candidate/`.
- **Independiente del backend**: no necesita el servidor FastAPI ni la base de datos; solo una carpeta con código.
- Las instrucciones de cada fase están en `internal/legacylift/phases/*.md` (se pueden editar).

## Compilar

Requiere Go 1.27+.

```bash
cd terminal
go build -o legacylift .
```

## Usar con IA local (Ollama) — recomendado

```bash
ollama serve                 # en otra terminal
ollama pull qwen3.5:9b       # o cualquier modelo con soporte de herramientas
cd /ruta/al/sistema-legado
/ruta/a/legacylift           # detecta Ollama y crea crush.json automáticamente
```

Elegir modelo: `legacylift --model ollama/qwen3.5:9b` o `LEGACYLIFT_MODEL=qwen3.5:9b legacylift`.

## Modo liviano (automático con Ollama)

Los modelos locales chicos (4B–9B) no manejan bien el prompt largo de Crush ni sus 30+ herramientas.
Con Ollama se activa el **modo liviano**: el programa lee el código (con números de línea), corre las
pruebas y calcula el diff, y la IA solo analiza y escribe cada informe. En Modernize la IA devuelve el
archivo completo y el programa lo guarda solo en `.legacylift/candidate/`.
Forzar: `--lite` (también con nube) o `--full` (modo agente completo).

Prueba real con `qwen3.5:9b` (Apple M5, 16 GB) sobre `demo-source`: las 7 fases completas en ~30 min;
Understand encontró las 3 reglas de negocio, Modernize refactorizó `calculator.py` y Verify confirmó
que las 3 pruebas pasan sobre la candidata.

## Usar con proveedores en la nube

Funcionan todos los proveedores de Crush (Anthropic, OpenAI, OpenRouter, Gemini, Groq, …):

```bash
export ANTHROPIC_API_KEY=...
legacylift --model anthropic/claude-sonnet-5-5
```

También se pueden configurar en `crush.json` del proyecto.

## Opciones

```bash
legacylift --from understand --until plan   # solo algunas fases
legacylift --plain                          # salida en texto (sin TUI), útil en CI
legacylift --cwd /ruta/al/proyecto          # otra carpeta
legacylift phases                           # lista las fases
```

En la pantalla: `q` cancela. No hay campo para escribir.

## Qué se cambió respecto de Crush

- `internal/legacylift/`: fases, ejecutor, pantalla (TUI) y configuración automática de Ollama.
- `internal/cmd/phases.go`: el comando principal ejecuta las fases en lugar del chat.
- `internal/cmd/root.go`: se quitó el chat interactivo y el comando `run` (prompts libres).

## Licencia

Crush se distribuye bajo **FSL-1.1-MIT** (ver `LICENSE.md`), que se conserva en este fork.
Permite uso, modificación y fines académicos; no permite ofrecerlo como producto que compita con Crush.
Cada versión pasa a MIT dos años después de publicada.
