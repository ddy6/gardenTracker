import assert from "node:assert/strict";
import test from "node:test";

import { app } from "../worker/index.ts";
import type { AppBindings } from "../worker/config.ts";

interface FakePreparedStatement {
  bind: (...params: Array<string | number | null>) => FakePreparedStatement;
  all: <T>() => Promise<{ results: T[] }>;
  first: <T>() => Promise<T | null>;
  run: <T>() => Promise<D1Result<T>>;
}

function createFakeDatabase(): D1Database {
  return {
    prepare(statement: string): FakePreparedStatement {
      return {
        bind(): FakePreparedStatement {
          return this;
        },
        async all<T>(): Promise<{ results: T[] }> {
          if (statement.includes("FROM plants")) {
            return { results: [] };
          }
          return { results: [] };
        },
        async first<T>(): Promise<T | null> {
          if (statement.includes("SELECT 1 AS ok")) {
            return { ok: 1 } as T;
          }
          return null;
        },
        async run<T>(): Promise<D1Result<T>> {
          return { success: true } as D1Result<T>;
        },
      };
    },
  } as D1Database;
}

function createEnv(overrides: Partial<AppBindings> = {}): AppBindings {
  return {
    DB: createFakeDatabase(),
    APP_PASSWORD: "test-password",
    SESSION_SECRET: "test-session-secret",
    APP_TIMEZONE: "America/New_York",
    AUTH_VERSION: "1",
    ENABLE_DEBUG_ROUTES: "false",
    ...overrides,
  };
}

function getSetCookies(response: Response): string[] {
  const headers = response.headers as Headers & { getSetCookie?: () => string[] };
  if (typeof headers.getSetCookie === "function") {
    return headers.getSetCookie();
  }

  const cookie = response.headers.get("set-cookie");
  return cookie ? [cookie] : [];
}

function getCookieValue(response: Response, cookieName: string): string {
  const cookie = getSetCookies(response).find((value) => value.startsWith(`${cookieName}=`));
  assert.ok(cookie, `Expected ${cookieName} cookie to be set`);
  return cookie.split(";", 1)[0];
}

function getCsrfToken(html: string): string {
  const match = html.match(/name="csrf_token" value="([^"]+)"/);
  assert.ok(match, "Expected CSRF token field in HTML");
  return match[1];
}

async function login(env: AppBindings): Promise<{ authCookie: string; response: Response }> {
  const loginPage = await app.request("/login", undefined, env);
  assert.equal(loginPage.status, 200);

  const csrfCookie = getCookieValue(loginPage, "garden_csrf");
  const csrfToken = getCsrfToken(await loginPage.text());

  const response = await app.request(
    "https://garden.example/login",
    {
      method: "POST",
      headers: {
        "content-type": "application/x-www-form-urlencoded",
        cookie: csrfCookie,
      },
      body: new URLSearchParams({
        csrf_token: csrfToken,
        password: env.APP_PASSWORD || "",
      }).toString(),
    },
    env,
  );

  assert.equal(response.status, 303);
  return {
    authCookie: getCookieValue(response, "garden_session"),
    response,
  };
}

test("GET /login returns hardened HTML headers", async () => {
  const response = await app.request("/login", undefined, createEnv());

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(response.headers.get("referrer-policy"), "same-origin");
  assert.equal(response.headers.get("x-content-type-options"), "nosniff");
  assert.equal(response.headers.get("x-frame-options"), "DENY");
  assert.match(response.headers.get("content-security-policy") || "", /script-src 'none'/);
  assert.doesNotMatch(response.headers.get("content-security-policy") || "", /unsafe-inline/);
});

test("POST /login issues an authenticated cookie and redirects", async () => {
  const env = createEnv();
  const { authCookie, response } = await login(env);

  assert.match(authCookie, /^garden_session=/);
  assert.equal(response.headers.get("location"), "/");

  const dashboardResponse = await app.request(
    "/",
    {
      headers: {
        cookie: authCookie,
      },
    },
    env,
  );

  assert.equal(dashboardResponse.status, 200);
  assert.match(await dashboardResponse.text(), /No plants yet/);
});

test("changing APP_PASSWORD invalidates existing sessions", async () => {
  const originalEnv = createEnv({ APP_PASSWORD: "alpha-password" });
  const { authCookie } = await login(originalEnv);

  const response = await app.request(
    "/",
    {
      headers: {
        cookie: authCookie,
      },
    },
    createEnv({ APP_PASSWORD: "beta-password" }),
  );

  assert.equal(response.status, 303);
  assert.equal(response.headers.get("location"), "/login");
});

test("changing AUTH_VERSION invalidates existing sessions", async () => {
  const originalEnv = createEnv({ AUTH_VERSION: "1" });
  const { authCookie } = await login(originalEnv);

  const response = await app.request(
    "/",
    {
      headers: {
        cookie: authCookie,
      },
    },
    createEnv({ AUTH_VERSION: "2" }),
  );

  assert.equal(response.status, 303);
  assert.equal(response.headers.get("location"), "/login");
});

test("debug route is hidden in production and available when explicitly enabled", async () => {
  const productionEnv = createEnv({ ENABLE_DEBUG_ROUTES: "false" });
  const { authCookie } = await login(productionEnv);

  const hiddenResponse = await app.request(
    "/debug/d1",
    {
      headers: {
        cookie: authCookie,
      },
    },
    productionEnv,
  );

  assert.equal(hiddenResponse.status, 404);

  const previewEnv = createEnv({ ENABLE_DEBUG_ROUTES: "true" });
  const { authCookie: previewCookie } = await login(previewEnv);
  const debugResponse = await app.request(
    "/debug/d1",
    {
      headers: {
        cookie: previewCookie,
      },
    },
    previewEnv,
  );

  assert.equal(debugResponse.status, 200);
  assert.deepEqual(await debugResponse.json(), { ok: true, error: null });
});
