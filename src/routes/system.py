from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from auth import request_is_authenticated
from db import ping_database
from ui import get_env

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return JSONResponse({"ok": True})


@router.get("/debug/d1")
async def debug_d1(request: Request):
    if not request_is_authenticated(request):
        return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)

    db_ok, db_error = await ping_database(get_env(request))
    status_code = 200 if db_ok else 500
    return JSONResponse({"ok": db_ok, "error": db_error}, status_code=status_code)
