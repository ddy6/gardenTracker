from pathlib import Path
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from auth import request_is_authenticated
from config import APP_NAME, get_timezone_name, get_worker_name

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(name: str, **context) -> HTMLResponse:
    template = TEMPLATE_ENV.get_template(name)
    return HTMLResponse(template.render(**context))


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def with_query(path: str, **params) -> str:
    filtered = {key: value for key, value in params.items() if value not in (None, "")}
    query = urlencode(filtered)
    return f"{path}?{query}" if query else path


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
