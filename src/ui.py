from pathlib import Path
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth import get_csrf_token_for_request, request_is_authenticated
from config import APP_NAME, CSRF_COOKIE_NAME, CSRF_FORM_FIELD_NAME, CSRF_TOKEN_TTL_SECONDS, get_timezone_name, get_worker_name

def _templates_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def build_template_environment():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    return Environment(
        loader=FileSystemLoader(str(_templates_dir())),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_template(name: str, **context) -> HTMLResponse:
    template = build_template_environment().get_template(name)
    return HTMLResponse(template.render(**context))


def apply_csrf_cookie(request: Request, response, csrf_token: str):
    if request_is_authenticated(request):
        return response
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=CSRF_TOKEN_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


def render_template_response(request: Request, name: str, *, status_code: int = 200, **extra):
    csrf_token = extra.pop("csrf_token", get_csrf_token_for_request(request))
    response = render_template(
        name,
        **build_template_context(
            request,
            csrf_token=csrf_token,
            csrf_field_name=CSRF_FORM_FIELD_NAME,
            **extra,
        ),
    )
    response.status_code = status_code
    return apply_csrf_cookie(request, response, csrf_token)


def render_error_response(
    request: Request,
    *,
    error_title: str,
    error_message: str,
    back_url: str,
    back_label: str,
    page_title: str,
    status_code: int,
):
    return render_template_response(
        request,
        "error.html",
        status_code=status_code,
        page_title=page_title,
        error_title=error_title,
        error_message=error_message,
        back_url=back_url,
        back_label=back_label,
    )


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
