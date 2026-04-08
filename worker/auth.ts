import type { Context } from "hono";
import { deleteCookie, getCookie, setCookie } from "hono/cookie";

import {
  AUTH_COOKIE_NAME,
  AUTH_COOKIE_TTL_SECONDS,
  CSRF_COOKIE_NAME,
  CSRF_TOKEN_TTL_SECONDS,
  getAuthVersion,
  type AppBindings,
  type AppEnv,
} from "./config.ts";

const encoder = new TextEncoder();

function nowInSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

function toBase64Url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function sign(payload: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(payload));
  return toBase64Url(signature);
}

function randomNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return toBase64Url(bytes.buffer);
}

function getSecret(env: AppBindings): string {
  return env.SESSION_SECRET || "";
}

async function getSessionScope(env: AppBindings): Promise<string> {
  const secret = getSecret(env);
  const password = env.APP_PASSWORD || "";
  const authVersion = getAuthVersion(env);
  if (!secret || !password) {
    return "";
  }

  const scope = await sign(`session-scope|${password}|${authVersion}`, secret);
  return scope.slice(0, 24);
}

export async function createAuthCookie(
  env: AppBindings,
  now = nowInSeconds(),
  ttlSeconds = AUTH_COOKIE_TTL_SECONDS,
): Promise<string> {
  const secret = getSecret(env);
  const sessionScope = await getSessionScope(env);
  if (!secret || !sessionScope) {
    return "";
  }

  const expiresAt = now + ttlSeconds;
  const payload = `garden|${sessionScope}|${expiresAt}`;
  return `${payload}|${await sign(payload, secret)}`;
}

export async function isValidAuthCookie(
  cookieValue: string | undefined,
  env: AppBindings,
  now = nowInSeconds(),
): Promise<boolean> {
  const secret = getSecret(env);
  const expectedScope = await getSessionScope(env);
  if (!cookieValue || !secret) {
    return false;
  }

  const parts = cookieValue.split("|");
  if (parts.length !== 4) {
    return false;
  }

  const [prefix, sessionScope, expiresAtText, signature] = parts;
  if (prefix !== "garden") {
    return false;
  }
  if (!expectedScope || sessionScope !== expectedScope) {
    return false;
  }

  const expiresAt = Number.parseInt(expiresAtText, 10);
  if (!Number.isFinite(expiresAt) || expiresAt <= now) {
    return false;
  }

  const expected = await sign(`${prefix}|${sessionScope}|${expiresAt}`, secret);
  return signature === expected;
}

export async function createAuthenticatedCsrfToken(
  authCookieValue: string,
  secret: string,
): Promise<string> {
  if (!authCookieValue || !secret) {
    return "";
  }
  return `csrf-auth|${await sign(authCookieValue, secret)}`;
}

export async function createCsrfToken(
  secret: string,
  now = nowInSeconds(),
  ttlSeconds = CSRF_TOKEN_TTL_SECONDS,
): Promise<string> {
  const expiresAt = now + ttlSeconds;
  const payload = `csrf|${expiresAt}|${randomNonce()}`;
  return `${payload}|${await sign(payload, secret)}`;
}

export async function isValidCsrfToken(
  tokenValue: string | undefined,
  secret: string,
  now = nowInSeconds(),
): Promise<boolean> {
  if (!tokenValue || !secret) {
    return false;
  }

  const parts = tokenValue.split("|");
  if (parts.length !== 4) {
    return false;
  }

  const [prefix, expiresAtText, nonce, signature] = parts;
  if (prefix !== "csrf" || !nonce) {
    return false;
  }

  const expiresAt = Number.parseInt(expiresAtText, 10);
  if (!Number.isFinite(expiresAt) || expiresAt <= now) {
    return false;
  }

  const expected = await sign(`${prefix}|${expiresAt}|${nonce}`, secret);
  return signature === expected;
}

export async function csrfTokensMatch(
  submittedToken: string | undefined,
  cookieToken: string | undefined,
  secret: string,
): Promise<boolean> {
  if (!submittedToken || !cookieToken || submittedToken !== cookieToken) {
    return false;
  }
  return isValidCsrfToken(cookieToken, secret);
}

export async function getCsrfTokenForRequest(c: Context<AppEnv>): Promise<string> {
  const secret = getSecret(c.env);
  const authCookieValue = getCookie(c, AUTH_COOKIE_NAME);
  if (await isValidAuthCookie(authCookieValue, c.env)) {
    return createAuthenticatedCsrfToken(authCookieValue as string, secret);
  }

  const existingToken = getCookie(c, CSRF_COOKIE_NAME);
  if (await isValidCsrfToken(existingToken, secret)) {
    return existingToken as string;
  }
  return createCsrfToken(secret);
}

export async function requestHasValidCsrfToken(
  c: Context<AppEnv>,
  submittedToken: string | undefined,
): Promise<boolean> {
  const secret = getSecret(c.env);
  const authCookieValue = getCookie(c, AUTH_COOKIE_NAME);
  if (await isValidAuthCookie(authCookieValue, c.env)) {
    const expectedToken = await createAuthenticatedCsrfToken(authCookieValue as string, secret);
    return Boolean(submittedToken && expectedToken && submittedToken === expectedToken);
  }

  const cookieToken = getCookie(c, CSRF_COOKIE_NAME);
  return csrfTokensMatch(submittedToken, cookieToken, secret);
}

export async function requestIsAuthenticated(c: Context<AppEnv>): Promise<boolean> {
  const cookieValue = getCookie(c, AUTH_COOKIE_NAME);
  return isValidAuthCookie(cookieValue, c.env);
}

export async function setAuthCookieOnContext(c: Context<AppEnv>): Promise<void> {
  const requestUrl = new URL(c.req.url);
  const cookieValue = await createAuthCookie(c.env);
  if (!cookieValue) {
    throw new Error("Authentication is not configured correctly.");
  }
  setCookie(c, AUTH_COOKIE_NAME, cookieValue, {
    maxAge: AUTH_COOKIE_TTL_SECONDS,
    httpOnly: true,
    sameSite: "Lax",
    secure: requestUrl.protocol === "https:",
    path: "/",
  });
  deleteCookie(c, CSRF_COOKIE_NAME, { path: "/" });
}

export function clearSessionCookies(c: Context<AppEnv>): void {
  deleteCookie(c, AUTH_COOKIE_NAME, { path: "/" });
  deleteCookie(c, CSRF_COOKIE_NAME, { path: "/" });
}

export function applyAnonymousCsrfCookie(
  c: Context<AppEnv>,
  csrfToken: string,
  isAuthenticated: boolean,
): void {
  if (isAuthenticated) {
    return;
  }

  const requestUrl = new URL(c.req.url);
  setCookie(c, CSRF_COOKIE_NAME, csrfToken, {
    maxAge: CSRF_TOKEN_TTL_SECONDS,
    httpOnly: true,
    sameSite: "Lax",
    secure: requestUrl.protocol === "https:",
    path: "/",
  });
}
