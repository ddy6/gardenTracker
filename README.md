# Garden Dashboard Worker Spike

This repo currently contains the Phase 0 spike for a Cloudflare-native build of the Garden Dashboard app.

## Goals

The spike is meant to prove four things before full implementation:

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

## Local Setup

Cloudflare's current Python Worker flow uses `uv` and `pywrangler`.

1. Install `uv` if it is not already installed.
2. Sync the Python environment:

```bash
uv sync
```

3. Copy the local secrets template:

```bash
cp .dev.vars.example .dev.vars
```

4. Create your D1 databases and replace the placeholder IDs in `wrangler.jsonc`.

Suggested names:

- `garden-dashboard-production`
- `garden-dashboard-preview`

5. Apply the schema locally:

```bash
uv run pywrangler d1 migrations apply DB --local
```

6. Start the local dev server:

```bash
uv run pywrangler dev
```

## Useful Commands

Run the stdlib auth helper test:

```bash
python3 -m unittest tests/test_auth_helpers.py
```

Create a preview D1 database:

```bash
uv run pywrangler d1 create garden-dashboard-preview
```

Create a production D1 database:

```bash
uv run pywrangler d1 create garden-dashboard-production
```

Deploy the preview environment:

```bash
uv run pywrangler deploy --env preview
```

Deploy production:

```bash
uv run pywrangler deploy
```

## Current Routes

- `GET /healthz`: simple JSON health check
- `GET /login`: spike login page
- `POST /login`: checks shared password and sets signed cookie
- `POST /logout`: clears auth cookie
- `GET /`: protected HTML page showing cookie + D1 status
- `GET /debug/d1`: protected D1 probe endpoint
