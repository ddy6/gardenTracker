APP_NAME = "Garden Dashboard"
AUTH_COOKIE_NAME = "garden_session"
AUTH_COOKIE_TTL_SECONDS = 60 * 60 * 24 * 14
DEFAULT_TIMEZONE = "America/New_York"


def get_timezone_name(env) -> str:
    return getattr(env, "APP_TIMEZONE", DEFAULT_TIMEZONE)


def get_worker_name(env) -> str:
    return getattr(env, "WORKER_NAME", "garden-dashboard-local")
