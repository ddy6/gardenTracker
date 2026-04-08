from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from auth import create_auth_cookie, request_is_authenticated
from config import APP_NAME, AUTH_COOKIE_NAME, AUTH_COOKIE_TTL_SECONDS, get_timezone_name, get_worker_name
from db import ping_database

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI()


def render_template(name: str, **context) -> HTMLResponse:
    template = TEMPLATE_ENV.get_template(name)
    return HTMLResponse(template.render(**context))


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def get_env(request: Request):
    return request.scope["env"]


def build_template_context(request: Request, **extra):
    env = get_env(request)
    return {
        "app_name": APP_NAME,
        "is_authenticated": request_is_authenticated(request),
        "timezone_name": get_timezone_name(env),
        "worker_name": get_worker_name(env),
        **extra,
    }


@app.get("/healthz")
async def healthz():
    return JSONResponse({"ok": True})


@app.get("/login")
async def login_page(request: Request):
    if request_is_authenticated(request):
        return redirect("/")

    return render_template("login.html", **build_template_context(request, error_message=None))


@app.post("/login")
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


@app.post("/logout")
async def logout():
    response = redirect("/login")
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return response


@app.get("/")
async def home(request: Request):
    if not request_is_authenticated(request):
        return redirect("/login")

    env = get_env(request)
    db_ok, db_error = await ping_database(env)
    return render_template(
        "home.html",
        **build_template_context(
            request,
            db_ok=db_ok,
            db_error=db_error,
        ),
    )


@app.get("/debug/d1")
async def debug_d1(request: Request):
    if not request_is_authenticated(request):
        return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)

    db_ok, db_error = await ping_database(get_env(request))
    status_code = 200 if db_ok else 500
    return JSONResponse({"ok": db_ok, "error": db_error}, status_code=status_code)
