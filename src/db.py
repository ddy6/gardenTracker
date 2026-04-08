def get_database(env):
    database = getattr(env, "DB", None)
    if database is None:
        raise RuntimeError("Missing D1 binding: DB")
    return database


def _to_python(value):
    return value.to_py() if hasattr(value, "to_py") else value


async def execute(env, statement: str, *params):
    prepared = get_database(env).prepare(statement)
    if params:
        prepared = prepared.bind(*params)
    return await prepared.run()


async def fetch_all(env, statement: str, *params):
    result = await execute(env, statement, *params)
    rows = list(getattr(result, "results", []) or [])
    return [_to_python(row) for row in rows]


async def fetch_one(env, statement: str, *params):
    prepared = get_database(env).prepare(statement)
    if params:
        prepared = prepared.bind(*params)
    row = await prepared.first()
    return _to_python(row)


async def ping_database(env) -> tuple[bool, str | None]:
    try:
        await execute(env, "SELECT 1 AS ok")
        return True, None
    except Exception as exc:  # pragma: no cover - exercised in Worker runtime
        return False, str(exc)
