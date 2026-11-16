# Fine-tuning de la IA local de LegacyLift

Objetivo: que un modelo local chico (Qwen3-4B) ejecute las 7 fases en **modo agente reducido**
(`legacylift --mode agent`) con calidad cercana a un modelo grande.

## Fase B — Proyectos de práctica con verdad conocida

```bash
python3 finetune/generar_proyectos.py --salida datos --train 60 --valid 10 --test 10 --semilla 7
```

- 80 proyectos legacy en Python, JavaScript, Java y Go (chicos, medianos y grandes).
- Reglas de negocio parametrizadas y defectos sembrados (TODO, `== True`, paréntesis redundantes,
  código muerto, duplicación, código comentado, excepciones silenciadas).
- Pruebas exactas (detectan, por ejemplo, que se quite un redondeo).
- La verdad conocida queda en `datos/meta/<split>/<id>.json`, **fuera** del proyecto.
- Los dominios `biblioteca` y `envios` solo aparecen en `test` (generalización).

## Evaluación automática (sin otra IA)

```bash
python3 finetune/evaluar.py --datos datos --split valid --trabajo <carpeta-con-copias> --salida eval.json
```

Mide: reglas encontradas, defectos encontrados, citas `archivo:línea` válidas, español,
original intacto, Modernize con cambios reales y pruebas que pasan, y honestidad de Verify.
