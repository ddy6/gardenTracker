import base64
import hashlib
import hmac
import secrets
import time

from config import (
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_TTL_SECONDS,
    CSRF_COOKIE_NAME,
    CSRF_TOKEN_TTL_SECONDS,
)


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def create_auth_cookie(secret: str, now: int | None = None, ttl_seconds: int = AUTH_COOKIE_TTL_SECONDS) -> str:
    issued_at = int(time.time() if now is None else now)
    expires_at = issued_at + ttl_seconds
    payload = f"garden|{expires_at}"
    return f"{payload}|{_sign(payload, secret)}"


def is_valid_auth_cookie(cookie_value: str | None, secret: str, now: int | None = None) -> bool:
    if not cookie_value or not secret:
        return False

    parts = cookie_value.split("|")
    if len(parts) != 3:
        return False

    prefix, expires_at_text, signature = parts
    if prefix != "garden":
        return False

    try:
        expires_at = int(expires_at_text)
    except ValueError:
        return False

    current_time = int(time.time() if now is None else now)
    if expires_at <= current_time:
        return False

    expected = _sign(f"{prefix}|{expires_at}", secret)
    return hmac.compare_digest(signature, expected)


def create_authenticated_csrf_token(auth_cookie_value: str, secret: str) -> str:
    if not auth_cookie_value or not secret:
        return ""
    return f"csrf-auth|{_sign(auth_cookie_value, secret)}"


def create_csrf_token(secret: str, now: int | None = None, ttl_seconds: int = CSRF_TOKEN_TTL_SECONDS) -> str:
    issued_at = int(time.time() if now is None else now)
    expires_at = issued_at + ttl_seconds
    nonce = secrets.token_urlsafe(16)
    payload = f"csrf|{expires_at}|{nonce}"
    return f"{payload}|{_sign(payload, secret)}"


def is_valid_csrf_token(token_value: str | None, secret: str, now: int | None = None) -> bool:
    if not token_value or not secret:
        return False

    parts = token_value.split("|")
    if len(parts) != 4:
        return False

    prefix, expires_at_text, nonce, signature = parts
    if prefix != "csrf" or not nonce:
        return False

    try:
        expires_at = int(expires_at_text)
    except ValueError:
        return False

    current_time = int(time.time() if now is None else now)
    if expires_at <= current_time:
        return False

    expected = _sign(f"{prefix}|{expires_at}|{nonce}", secret)
    return hmac.compare_digest(signature, expected)


def csrf_tokens_match(submitted_token: str | None, cookie_token: str | None, secret: str, now: int | None = None) -> bool:
    if not submitted_token or not cookie_token:
        return False
    if not hmac.compare_digest(submitted_token, cookie_token):
        return False
    return is_valid_csrf_token(cookie_token, secret, now)


def get_csrf_token_for_request(request) -> str:
    env = request.scope.get("env")
    secret = getattr(env, "SESSION_SECRET", "") if env is not None else ""
    auth_cookie_value = request.cookies.get(AUTH_COOKIE_NAME)
    if is_valid_auth_cookie(auth_cookie_value, secret):
        return create_authenticated_csrf_token(auth_cookie_value, secret)

    existing_token = request.cookies.get(CSRF_COOKIE_NAME)
    if is_valid_csrf_token(existing_token, secret):
        return existing_token
    return create_csrf_token(secret)


def request_has_valid_csrf_token(request, submitted_token: str | None) -> bool:
    env = request.scope.get("env")
    if env is None:
        return False

    secret = getattr(env, "SESSION_SECRET", "")
    auth_cookie_value = request.cookies.get(AUTH_COOKIE_NAME)
    if is_valid_auth_cookie(auth_cookie_value, secret):
        expected_token = create_authenticated_csrf_token(auth_cookie_value, secret)
        return bool(submitted_token and expected_token and hmac.compare_digest(submitted_token, expected_token))

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    return csrf_tokens_match(submitted_token, cookie_token, secret)


def request_is_authenticated(request) -> bool:
    env = request.scope.get("env")
    if env is None:
        return False

    secret = getattr(env, "SESSION_SECRET", "")
    cookie_value = request.cookies.get(AUTH_COOKIE_NAME)
    return is_valid_auth_cookie(cookie_value, secret)
