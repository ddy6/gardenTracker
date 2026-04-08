export const APP_NAME = "Garden Dashboard";
export const AUTH_COOKIE_NAME = "garden_session";
export const AUTH_COOKIE_TTL_SECONDS = 60 * 60 * 24 * 14;
export const CSRF_COOKIE_NAME = "garden_csrf";
export const CSRF_FORM_FIELD_NAME = "csrf_token";
export const CSRF_TOKEN_TTL_SECONDS = AUTH_COOKIE_TTL_SECONDS;
export const DEFAULT_TIMEZONE = "America/New_York";
export const DEFAULT_AUTH_VERSION = "1";

export interface AppBindings {
  DB: D1Database;
  WORKER_NAME?: string;
  APP_PASSWORD?: string;
  SESSION_SECRET?: string;
  APP_TIMEZONE?: string;
  AUTH_VERSION?: string;
  ENABLE_DEBUG_ROUTES?: string;
}

export type AppEnv = {
  Bindings: AppBindings;
};

export function getTimezoneName(env: AppBindings): string {
  return env.APP_TIMEZONE || DEFAULT_TIMEZONE;
}

export function getWorkerName(env: AppBindings): string {
  return env.WORKER_NAME || "garden-dashboard-local";
}

export function getAuthVersion(env: AppBindings): string {
  return env.AUTH_VERSION || DEFAULT_AUTH_VERSION;
}

export function debugRoutesEnabled(env: AppBindings): boolean {
  return env.ENABLE_DEBUG_ROUTES === "true";
}
