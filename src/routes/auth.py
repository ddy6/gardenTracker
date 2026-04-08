from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from auth import create_auth_cookie, request_is_authenticated
from config import AUTH_COOKIE_NAME, AUTH_COOKIE_TTL_SECONDS
from ui import build_template_context, get_env, redirect, render_template, TEMPLATE_ENV

router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    if request_is_authenticated(request):
        return redirect("/")

    return render_template("login.html", **build_template_context(request, error_message=None))


@router.post("/login")
async def login(request: Request):
    env = get_env(request)
    body = (await request.body()).decode("utf-8")
    form_data = parse_qs(body)
    submitted_password = form_data.get("password", [""])[0]
    configured_password = getattr(env, "APP_PASSWORD", "")

    if not configured_password or submitted_password != configured_password:
        context = build_template_context(request, error_message="Incorrect password. Try again.")
        return HTMLResponse(TEMPLATE_ENV.get_template("login.html").render(**context), status_code=401)

    response = redirect("/")
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=create_auth_cookie(getattr(env, "SESSION_SECRET", "")),
        max_age=AUTH_COOKIE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


@router.post("/logout")
async def logout():
    response = redirect("/login")
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return response
