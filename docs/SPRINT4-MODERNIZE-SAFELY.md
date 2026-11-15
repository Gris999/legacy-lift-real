# Sprint 4 — Modernize Safely

## Alcance

- HU-11: la API **solo encola** intentos persistentes; un worker separado los procesa; candidatos inmutables con hash. Se vinculan snapshot, blueprint, wave y pack.
- HU-12: resumen no técnico basado en líneas reales; selección por **archivo completo** y comentarios; diff completo bajo demanda. No hay selección por hunk.
- HU-13: Verify es otro trabajo reclamado por worker; compara baseline estático y pruebas autorizadas. La clasificación `verified_within_tests` **solo verifica los casos cubiertos**, nunca equivalencia general.
- HU-14: aprobación humana y aceptación escrita del riesgo cuando falta evidencia; divergencias bloquean aprobación; ZIP, .patch e informe a partir del candidato revisado.

## Worker aislado

La API no ejecuta Modernize ni Verify. Ejecuta `docker compose -f compose.migration-worker.yml up --build` desde la raíz del proyecto en desarrollo. Configura `CLAUDE_API_KEY` solo si utilizas Claude. **La imagen Docker proporcionada no prueba resistencia a código hostil**: un SaaS deberá tener VM efímera dedicada, firewall/egress allowlist, broker de jobs, almacenamiento de snapshots de solo lectura y credenciales mínimas. El contenedor de desarrollo monta `data/` con acceso de escritura; nunca montes el socket Docker, tu home ni secretos adicionales. Codex requiere autenticación y configuración independientes dentro del worker.

La configuración `LEGACYLIFT_MIGRATION_WORKER_MODE=separate` es obligatoria para iniciar el worker. El backend FastAPI no consume esos trabajos por sí mismo. Para un ejemplo determinista sin conexión ni tokens, puedes ejecutar desde `backend/` en otro proceso:

```
LEGACYLIFT_MIGRATION_WORKER_MODE=separate python -m app.migration_worker --once
```

Esta ejecución local sirve para pruebas de flujo; no es aislamiento seguro para código no confiable.

## Presupuestos y límites

Máximo `LEGACYLIFT_MAX_MIGRATION_ATTEMPTS=3` por snapshot/blueprint/wave (tope absoluto 10). Cada intento se solicita manualmente. El Codex CLI tiene timeout de 330 s y Claude de 180 s en los adaptadores actuales. No se ha implementado presupuestación precisa por tokens ni por USD: la API no debe afirmar que la ha aplicado. Los packs COBOL y migraciones de lenguaje continúan planificados/no ejecutables.

## Secuencia real

1. Finaliza baseline con autorización de ejecución si se necesitan pruebas.
2. Desde Modernize inicia una ejecución: se crea un intento en cola.
3. Worker reclama intento, valida ámbito, crea código candidato sin modificar fuente, conserva su snapshot inmutable.
4. Revisa resumen, comenta y selecciona archivos. Para ver cambios técnicos, abre diff individual.
5. Verify encola una segunda operación de worker sobre **esos archivos** y guarda hash/veredicto.
6. Acepta o rechaza: divergencias no se aprueban. Si no se demuestra equivalencia, se exige una justificación mínima; la aprobación es manual y explícita.
7. Descarga ZIP, diff e informe. No se crea automáticamente ningún PR GitHub.

## Limitaciones

- SQLite se comparte entre API y worker local, adecuado para MVP mononodo, no para workers remotos sin broker.
- Un candidato se guarda de forma inmutable en la aplicación y mediante permisos de solo lectura: esto NO protege contra el propietario del proceso o alguien con acceso directo al disco.
- Los informes son basados en diferencias y pruebas reales; no se inventan explicaciones semánticas ni equivalencia total.
- Los cambios se seleccionan por archivo completo, sin aprobación selectiva de hunks.
- Verificación dinámica disponible únicamente para suites Python unittest con consentimiento y `LEGACYLIFT_WORKER_MODE=docker-local`, en entornos de desarrollo. COBOL/PHP/Java requieren adaptadores futuros.
- Nuevas waves no se ejecutan automáticamente; requieren su propio baseline/consentimiento.
