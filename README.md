# Garden Dashboard Cloudflare App

This repo now contains a completed Phase 0 platform spike and is ready to move into Phase 1 implementation for the real app skeleton.

## Status

Phase 0 was completed on April 8, 2026.

Verified successfully:

- local Python Worker boot via `pywrangler`
- FastAPI HTML route rendering
- static asset serving
- D1 local migration and query execution
- signed auth cookie issuance and protected route access
- protected D1 route returning success

Active workstream:

- Phase 1 project bootstrap and real app skeleton

## Phase 0 Goals

The platform spike was used to prove four things before full implementation:

- FastAPI can render HTML inside a Python Worker
- a signed auth cookie can be set and read
- a D1 binding can be queried
- static assets can be served alongside Worker-rendered routes

## Project Layout

- `src/entry.py`: Cloudflare Worker entrypoint
- `src/app.py`: FastAPI app and spike routes
- `src/auth.py`: signed auth cookie helpers
- `src/db.py`: D1 ping helper
- `src/templates/`: server-rendered HTML templates
- `src/assets/`: static assets served by Workers
- `migrations/0001_initial_schema.sql`: initial D1 schema
- `tests/test_auth_helpers.py`: stdlib-only smoke tests for cookie signing

## Phase 1 Next Tasks

- refactor the spike routes into stable auth and plant route modules
- replace the temporary protected home page with the real dashboard shell
- turn the current D1 probe layer into reusable plant query helpers
- add base layout partials needed for the production UI
- validate preview migrations and preview deploy in Cloudflare
- keep the current auth flow, but wire it into the real dashboard routes

## Local Setup

Cloudflare's current Python Worker flow uses `uv` and `pywrangler`.

1. Create and activate a Python virtualenv if needed.
2. Install the Python dependencies:

```bash
pip install fastapi jinja2 workers-py workers-runtime-sdk uv
```

3. Install Wrangler locally:

```bash
npm install --save-dev wrangler
```

4. Copy the local secrets template:

```bash
cp .dev.vars.example .dev.vars
```

5. Create your D1 databases and replace the placeholder IDs in `wrangler.jsonc`.

Suggested names:

- `garden-dashboard-production`
- `garden-dashboard-preview`

6. Apply the schema locally:

```bash
./node_modules/.bin/wrangler d1 migrations apply DB --local
```

7. Start the local dev server:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/pywrangler dev --ip 127.0.0.1 --port 8787
```

## Useful Commands

Run the stdlib auth helper test:

```bash
python3 -m unittest tests/test_auth_helpers.py
```

Create a preview D1 database:

```bash
./node_modules/.bin/wrangler d1 create garden-dashboard-preview
```

Create a production D1 database:

```bash
./node_modules/.bin/wrangler d1 create garden-dashboard-production
```

Apply preview migrations:

```bash
./node_modules/.bin/wrangler d1 migrations apply DB --env preview
```

Apply production migrations:

```bash
./node_modules/.bin/wrangler d1 migrations apply DB --env ""
```

Deploy the preview environment:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/pywrangler deploy --env preview
```

Deploy production:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/pywrangler deploy
```

## Current Routes

- `GET /healthz`: simple JSON health check
- `GET /login`: spike login page
- `POST /login`: checks shared password and sets signed cookie
- `POST /logout`: clears auth cookie
- `GET /`: protected HTML page showing cookie + D1 status
- `GET /debug/d1`: protected D1 probe endpoint

These routes are temporary spike routes and should be replaced or refactored during Phase 1.
