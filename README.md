# Garden Dashboard Cloudflare App

This repo now contains a completed Phase 0 platform spike and an active Phase 1 implementation with real plant CRUD and a watering-aware, filterable dashboard.

## Status

Phase 0 and the core Phase 1 application slices were completed on April 8, 2026.

Verified successfully:

- local Python Worker boot via `pywrangler`
- FastAPI HTML route rendering
- static asset serving
- D1 local migration and query execution
- signed auth cookie issuance and protected route access
- CSRF protection on login, logout, and plant POST routes
- plant create/edit/delete flows
- watering status calculation, urgency sorting, and summary counters
- dashboard status filters with filter-preserving add/edit/delete/water flows
- protected D1 route returning success

Active workstream:

- preview validation and deployment readiness

## Remaining Work

- apply migrations to the preview D1 database and verify preview deploy behavior
- deploy the preview Worker and run the same smoke checks against Cloudflare, not just local `pywrangler`
- decide whether production should start with starter plants or an empty dashboard
- add remaining presentation extras that still matter for handoff, mainly favicon/final branding polish
- complete production cutover on the chosen Cloudflare subdomain and verify HTTPS/mobile behavior

## Phase 0 Goals

The platform spike was used to prove four things before full implementation:

- FastAPI can render HTML inside a Python Worker
- a signed auth cookie can be set and read
- a D1 binding can be queried
- static assets can be served alongside Worker-rendered routes

## Project Layout

- `src/entry.py`: Cloudflare Worker entrypoint
- `src/app.py`: FastAPI app assembly and router registration
- `src/auth.py`: signed auth cookie and CSRF helpers
- `src/db.py`: reusable D1 query helpers
- `src/models.py`: lightweight view models for dashboard data
- `src/plants.py`: first plant query layer backed by D1
- `src/plant_status.py`: watering status, due-date, and dashboard summary logic
- `src/routes/`: route modules split by responsibility
- `src/ui.py`: template rendering and shared request context
- `src/templates/`: server-rendered HTML templates
- `src/templates/error.html`: styled fallback page for invalid form submissions
- `src/assets/`: static assets served by Workers
- `migrations/0001_initial_schema.sql`: initial D1 schema
- `tests/test_auth_helpers.py`: stdlib-only smoke tests for auth and CSRF helpers
- `tests/test_plant_form.py`: plant form parsing and validation tests
- `tests/test_models.py`: model normalization and display helper tests
- `tests/test_plant_status.py`: watering status and dashboard sorting tests

## Phase 1 Next Tasks

- validate preview migrations and preview deploy in Cloudflare
- add any final dashboard polish after preview feedback
- decide whether to ship with starter seed data or an empty first-run state
- harden deployment notes for preview and production cutover

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

Run the full current test suite:

```bash
python3 -m unittest tests/test_auth_helpers.py tests/test_models.py tests/test_plant_form.py tests/test_plant_status.py
```

Run only the stdlib auth helper test:

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
- `GET /login`: shared-password login page
- `POST /login`: checks shared password and sets signed cookie
- `POST /logout`: clears auth cookie
- `GET /`: protected watering dashboard with sorted plant statuses and status filters
  Query params: `status=all|overdue|due-soon|good|no-schedule`, optional `notice=<flash-key>`
- `GET /plants/new`: add plant form
- `POST /plants/new`: create plant
- `GET /plants/{id}/edit`: edit plant form
- `POST /plants/{id}/edit`: update plant
- `POST /plants/{id}/water`: mark a plant as watered today
- `POST /plants/{id}/delete`: delete plant
- `GET /debug/d1`: protected D1 probe endpoint
