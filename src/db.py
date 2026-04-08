def get_database(env):
    database = getattr(env, "DB", None)
    if database is None:
        raise RuntimeError("Missing D1 binding: DB")
    return database


async def execute(env, statement: str, *params):
    prepared = get_database(env).prepare(statement)
    if params:
        prepared = prepared.bind(*params)
    return await prepared.run()


async def fetch_all(env, statement: str, *params):
    result = await execute(env, statement, *params)
    return list(getattr(result, "results", []) or [])


async def fetch_one(env, statement: str, *params):
    prepared = get_database(env).prepare(statement)
    if params:
        prepared = prepared.bind(*params)
    return await prepared.first()


async def ping_database(env) -> tuple[bool, str | None]:
    try:
        await execute(env, "SELECT 1 AS ok")
        return True, None
    except Exception as exc:  # pragma: no cover - exercised in Worker runtime
        return False, str(exc)
