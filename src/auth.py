import base64
import hashlib
import hmac
import time

from config import AUTH_COOKIE_NAME, AUTH_COOKIE_TTL_SECONDS


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


def request_is_authenticated(request) -> bool:
    env = request.scope.get("env")
    if env is None:
        return False

    secret = getattr(env, "SESSION_SECRET", "")
    cookie_value = request.cookies.get(AUTH_COOKIE_NAME)
    return is_valid_auth_cookie(cookie_value, secret)
