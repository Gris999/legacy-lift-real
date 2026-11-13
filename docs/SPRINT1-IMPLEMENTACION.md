# LegacyLift AI — Sprint 1: implementación y guía de aplicación

## Decisiones acordadas

1. **HU-01**: usuarios reales, correo y contraseña, login/logout, sesiones revocables con expiración.
2. **HU-02**: repositorios públicos/privados mediante una **GitHub OAuth App** (OAuth + PKCE).
3. **HU-03**: múltiples snapshots de origen inmutables por proyecto; uno activo.
4. **HU-03**: ingesta → inventario y Discover de forma automática.
5. **HU-04**: jobs persistentes con progreso, SSE y fallback polling.

## Parcheo incremental

A partir del ZIP original, **en la raíz `legacylift-mvp`**:

```bash
git apply --check LegacyLift-S1-01-HU01-Auth.patch && git apply LegacyLift-S1-01-HU01-Auth.patch
git apply --check LegacyLift-S1-02-HU02-GitHub-OAuth.patch && git apply LegacyLift-S1-02-HU02-GitHub-OAuth.patch
git apply --check LegacyLift-S1-03-HU03-Snapshots.patch && git apply LegacyLift-S1-03-HU03-Snapshots.patch
git apply --check LegacyLift-S1-04-HU04-Jobs-SSE.patch && git apply LegacyLift-S1-04-HU04-Jobs-SSE.patch
```

Si el proyecto está modificado previamente, crea un commit o backup y revisa `git status` antes de aplicar.
Los cuatro parches fueron generados de forma secuencial, no intercambiable.

## Variables `.env`

En la raíz, copia `.env.example` como `.env`. Para registrar el **primer usuario**, genera:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Coloca el resultado en `LEGACYLIFT_BOOTSTRAP_SECRET`. La contraseña personal (12+ caracteres)
se introduce en la web. El código de instalación se utiliza **solo** para la primera cuenta.
El primer usuario recibe rol `owner` y hereda proyectos anteriores que no tenían propietario.
Para permitir altas siguientes cambia **temporalmente** `LEGACYLIFT_ALLOW_REGISTRATION=true`.

### GitHub OAuth

Crea una OAuth App en GitHub Developer Settings. Para localhost:

- Homepage URL: `http://localhost:4200`
- Callback URL: `http://localhost:8000/api/github/callback`

En `.env` establece:

```dotenv
GITHUB_OAUTH_CLIENT_ID=...
GITHUB_OAUTH_CLIENT_SECRET=...
GITHUB_OAUTH_CALLBACK_URL=http://localhost:8000/api/github/callback
GITHUB_OAUTH_RETURN_URL=http://localhost:4200/?github=connected
LEGACYLIFT_ENCRYPTION_KEY=...
```

Genera el último valor:

```bash
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

No pegues la key de GitHub en Angular. `repo` es un **scope amplio**, visible al usuario durante
la autorización. No es una GitHub App con permisos finos. Para una instancia pública en IPv6,
usa dominio HTTPS y configura las dos URLs con ese dominio en GitHub y en `.env`.
El proxy debe enrutar `/api` hacia FastAPI. La cuenta GitHub y la contraseña de LegacyLift
son credenciales independientes.

## Arranque y pruebas

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
uvicorn app.api:app --host 127.0.0.1 --port 8000
# otra terminal: cd frontend && npm install && npm start
```

## Recorrido de aceptación

1. Registra la primera cuenta con su código de instalación; crea otro usuario habilitando temporalmente altas.
2. Crea un proyecto y confirma que el otro usuario no puede leerlo ni enumerarlo.
3. Conecta GitHub mediante OAuth y selecciona un repositorio. También puedes subir ZIP sin GitHub.
4. Comprueba que POST upload/git devuelve `202` con un job; consulta `/api/projects/{id}/jobs`.
5. Confirma que el escaneo crea el inventario automáticamente y que `inventory.md` está visible.
6. Importa otra versión y comprueba que ambas aparecen en el historial, con hashes distintos.
7. Activa una versión anterior; las fases posteriores deben invalidarse y el código archivado no cambiar.
8. Prueba subida ZIP inválida; el job termina `failed` y puede reintentarse, sin alterar el snapshot activo.
9. Comprueba streaming `/api/projects/{id}/events` con la sesión y polling de fallback.

## Contratos principales

- `POST /api/auth/register`, `/api/auth/login`, `/api/auth/logout`; `GET /api/auth/config`, `/api/auth/me`.
- `GET/POST /api/projects`, `PATCH /api/projects/{id}`.
- `POST /api/github/connect`, `GET /api/github/callback`, `/api/github/status`, `/api/github/repos`.
- `POST /api/projects/{id}/upload` (ZIP), `/api/projects/{id}/git` (GitHub OAuth), ambos `202`.
- `GET /api/projects/{id}/snapshots`, `POST .../snapshots/{sid}/activate`.
- `GET /api/projects/{id}/jobs`, `POST .../jobs/{jid}/retry`, `POST .../jobs/{jid}/cancel` (solo cola).
- `GET /api/projects/{id}/events?after=N` con cabecera Authorization Bearer y SSE.

## Límites conocidos

- Hasta **300 archivos y 12 MB** de código aceptado, sin enlaces simbólicos ni archivos con secretos comunes.
- SSE usa SQLite y actualizaciones por polling; funciona en una instancia y no reemplaza Redis/BullMQ o un broker.
- Las tareas que ya están corriendo no se pueden cancelar sin riesgo; solo se cancela la cola.
- Escaneo actual es inventario/heurística. El análisis profundo pertenece al Sprint 2.
- La opción de registrar usuarios adicionales mediante `LEGACYLIFT_ALLOW_REGISTRATION` es temporal;
  invitaciones y administración de equipos siguen fuera de Sprint 1.
- OAuth real con GitHub y compilación Angular completa requieren comprobación en el equipo con dependencias y credenciales configuradas.
