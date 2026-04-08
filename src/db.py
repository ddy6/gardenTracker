async def ping_database(env) -> tuple[bool, str | None]:
    database = getattr(env, "DB", None)
    if database is None:
        return False, "Missing D1 binding: DB"

    try:
        await database.prepare("SELECT 1 AS ok").run()
        return True, None
    except Exception as exc:  # pragma: no cover - exercised in Worker runtime
        return False, str(exc)
