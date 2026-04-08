# Garden Dashboard Cloudflare App

This repo now contains a completed product implementation and an active Cloudflare runtime fallback. The app behavior is already built; the current task is getting the deployable Worker layer onto Cloudflare cleanly.

## Status

As of April 8, 2026:

Verified successfully:

- local Python Worker spike proved the product logic and D1 schema
- signed auth cookie issuance and protected route access
- CSRF protection on login, logout, and plant POST routes
- plant create/edit/delete flows
- watering status calculation, urgency sorting, and summary counters
- dashboard status filters with filter-preserving add/edit/delete/water flows
- TypeScript/Hono fallback Worker now ports the same route surface and D1-backed behavior
- `npm run check` passes for the fallback Worker
- `wrangler deploy --dry-run --env preview` bundles the fallback Worker successfully

Active workstream:

- preview validation and deployment readiness

## Remaining Work

- deploy the TypeScript preview Worker to Cloudflare and run the full smoke checks there
- decide whether production should start with starter plants or an empty dashboard
- add remaining presentation extras that still matter for handoff, mainly favicon/final branding polish
- complete production cutover on the chosen Cloudflare subdomain and verify HTTPS/mobile behavior

## Project Layout

- `worker/index.ts`: active Cloudflare Worker entrypoint and route registration
- `worker/auth.ts`: signed auth cookie and CSRF helpers for the fallback Worker
- `worker/plants.ts`: D1 access, form validation, plant models, and dashboard status logic
- `worker/render.ts`: HTML page rendering helpers for login, dashboard, forms, and errors
- `src/templates/error.html`: styled fallback page for invalid form submissions
- `src/assets/`: static assets served by Workers
- `migrations/0001_initial_schema.sql`: initial D1 schema
- `src/*.py` and `src/routes/*.py`: previous Python Worker implementation retained as reference while the TypeScript Worker becomes the deployable path
- `tests/test_auth_helpers.py`: stdlib-only smoke tests for auth and CSRF helpers
- `tests/test_plant_form.py`: plant form parsing and validation tests
- `tests/test_models.py`: model normalization and display helper tests
- `tests/test_plant_status.py`: watering status and dashboard sorting tests

## Phase 1 Next Tasks

- validate preview deploy in Cloudflare using the TypeScript Worker
- add any final dashboard polish after preview feedback
- decide whether to ship with starter seed data or an empty first-run state
- harden deployment notes for preview and production cutover

## Local Setup

The active runtime now uses a standard TypeScript Worker with Hono.

1. Install dependencies:

```bash
npm install
```

2. Copy the local secrets template:

```bash
cp .dev.vars.example .dev.vars
```

3. Create your D1 databases and replace the IDs in `wrangler.jsonc`.

Suggested names:

- `garden-dashboard-production`
- `garden-dashboard-preview`

4. Apply the schema locally:

```bash
npm run d1:migrate:local
```

5. Start the local dev server:

```bash
npm run dev
```

## Useful Commands

Type-check the fallback Worker:

```bash
npm run check
```

Create a preview D1 database:

```bash
npx wrangler d1 create garden-dashboard-preview
```

Create a production D1 database:

```bash
npx wrangler d1 create garden-dashboard-production
```

Apply preview migrations:

```bash
npm run d1:migrate:preview
```

Apply production migrations:

```bash
npm run d1:migrate:prod
```

Deploy the preview environment:

```bash
npm run deploy:preview
```

Deploy production:

```bash
npm run deploy
```

Python spike regression tests:

```bash
python3 -m unittest tests/test_auth_helpers.py tests/test_models.py tests/test_plant_form.py tests/test_plant_status.py
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
