# Garden Dashboard Cloudflare App

This repo now contains the live Cloudflare Worker for Garden Dashboard. The app behavior is built and deployed; the current task is security hardening for public beta on `garden.paropter.com`.

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
- `npm run test:worker` passes for the active TypeScript Worker
- auth cookies now invalidate when `APP_PASSWORD` changes
- `AUTH_VERSION` can invalidate all sessions without changing the password
- `/debug/d1` is disabled by default and only available when `ENABLE_DEBUG_ROUTES=true`
- HTML responses now send strict CSP and baseline browser hardening headers
- `wrangler deploy --dry-run` and `wrangler deploy --dry-run --env preview` both bundle successfully

Active workstream:

- Cloudflare-side beta hardening and final production verification

## Remaining Work

- put Cloudflare Access in front of `garden.paropter.com`
- add a WAF/rate-limit rule for `POST /login`
- review managed WAF/Bot settings and decide on HSTS for the zone
- deploy this security slice and verify production headers, session invalidation, and debug-route shutdown
- decide whether production should start with starter plants or remain empty
- add any remaining presentation polish that still matters for handoff

## Project Layout

- `worker/index.ts`: active Cloudflare Worker entrypoint and route registration
- `worker/auth.ts`: signed auth cookie, session-scope invalidation, and CSRF helpers
- `worker/plants.ts`: D1 access, form validation, plant models, and dashboard status logic
- `worker/render.ts`: HTML page rendering helpers for login, dashboard, forms, and errors
- `tests/worker_security.test.ts`: direct Node-run Worker security tests
- `src/assets/`: static assets served by Workers
- `migrations/0001_initial_schema.sql`: initial D1 schema
- `src/*.py` and `src/routes/*.py`: previous Python Worker implementation retained as reference while the TypeScript Worker becomes the deployable path
- `tests/test_auth_helpers.py`: stdlib-only smoke tests for auth and CSRF helpers
- `tests/test_plant_form.py`: plant form parsing and validation tests
- `tests/test_models.py`: model normalization and display helper tests
- `tests/test_plant_status.py`: watering status and dashboard sorting tests

## Security Rollout

Code-side hardening in this repo now assumes these runtime vars exist:

- `APP_PASSWORD`
- `SESSION_SECRET`
- `APP_TIMEZONE`
- `AUTH_VERSION`
- `ENABLE_DEBUG_ROUTES`

Current intended values:

- production:
  - `AUTH_VERSION=1`
  - `ENABLE_DEBUG_ROUTES=false`
- preview/local:
  - `AUTH_VERSION=1`
  - `ENABLE_DEBUG_ROUTES=true`

Operational notes:

- changing `APP_PASSWORD` now invalidates existing sessions after the new Worker version deploys
- bump `AUTH_VERSION` when you want to force-log-out every user without changing the password
- keep `ENABLE_DEBUG_ROUTES=false` in production

## Cloudflare Actions

These are still manual:

1. Create a Cloudflare Access self-hosted application for `garden.paropter.com`.
2. Add allow rules for the specific beta-user email addresses.
3. Add a WAF rate-limit rule for `POST /login`.
4. Review Managed WAF rules, Bot Fight Mode, and HSTS for `paropter.com`.
5. After deploying this commit, verify the production headers and confirm `/debug/d1` is gone on the public domain.

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

Run the direct Worker security tests:

```bash
npm run test:worker
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
- `GET /debug/d1`: preview/local-only D1 probe endpoint when `ENABLE_DEBUG_ROUTES=true`
