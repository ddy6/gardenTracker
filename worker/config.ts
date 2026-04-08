export const APP_NAME = "Garden Dashboard";
export const AUTH_COOKIE_NAME = "garden_session";
export const AUTH_COOKIE_TTL_SECONDS = 60 * 60 * 24 * 14;
export const CSRF_COOKIE_NAME = "garden_csrf";
export const CSRF_FORM_FIELD_NAME = "csrf_token";
export const CSRF_TOKEN_TTL_SECONDS = AUTH_COOKIE_TTL_SECONDS;
export const DEFAULT_TIMEZONE = "America/New_York";

export interface AppBindings {
  DB: D1Database;
  WORKER_NAME?: string;
  APP_PASSWORD?: string;
  SESSION_SECRET?: string;
  APP_TIMEZONE?: string;
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
