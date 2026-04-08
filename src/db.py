try:
    from pyodide.ffi import jsnull
except ImportError:  # pragma: no cover - local CPython test fallback
    jsnull = None


def get_database(env):
    database = getattr(env, "DB", None)
    if database is None:
        raise RuntimeError("Missing D1 binding: DB")
    return database


def _is_js_null(value) -> bool:
    return value is jsnull or type(value).__name__ == "JsNull"


def _to_python(value):
    value = value.to_py() if hasattr(value, "to_py") else value
    if _is_js_null(value):
        return None
    if isinstance(value, dict):
        return {key: _to_python(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_python(item) for item in value]
    return value


def _normalize_param(value):
    if value is None and jsnull is not None:
        return jsnull
    return value


async def execute(env, statement: str, *params):
    prepared = get_database(env).prepare(statement)
    if params:
        prepared = prepared.bind(*[_normalize_param(param) for param in params])
    return await prepared.run()


async def fetch_all(env, statement: str, *params):
    result = await execute(env, statement, *params)
    rows = list(getattr(result, "results", []) or [])
    return [_to_python(row) for row in rows]


async def fetch_one(env, statement: str, *params):
    prepared = get_database(env).prepare(statement)
    if params:
        prepared = prepared.bind(*[_normalize_param(param) for param in params])
    row = await prepared.first()
    return _to_python(row)


async def ping_database(env) -> tuple[bool, str | None]:
    try:
        await execute(env, "SELECT 1 AS ok")
        return True, None
    except Exception as exc:  # pragma: no cover - exercised in Worker runtime
        return False, str(exc)
