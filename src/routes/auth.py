from urllib.parse import parse_qs

from fastapi import APIRouter, Request

from auth import create_auth_cookie, request_has_valid_csrf_token, request_is_authenticated
from config import AUTH_COOKIE_NAME, AUTH_COOKIE_TTL_SECONDS, CSRF_FORM_FIELD_NAME
from ui import get_env, redirect, render_error_response, render_template_response

router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    if request_is_authenticated(request):
        return redirect("/")

    return render_template_response(request, "login.html", error_message=None)


@router.post("/login")
async def login(request: Request):
    env = get_env(request)
    body = (await request.body()).decode("utf-8")
    form_data = parse_qs(body, keep_blank_values=True)
    submitted_csrf_token = form_data.get(CSRF_FORM_FIELD_NAME, [""])[0]
    if not request_has_valid_csrf_token(request, submitted_csrf_token):
        return render_error_response(
            request,
            error_title="Refresh Required",
            error_message="The login form expired. Reload the page and try again.",
            back_url="/login",
            back_label="Back to login",
            page_title="Invalid Form Submission",
            status_code=403,
        )

    submitted_password = form_data.get("password", [""])[0]
    configured_password = getattr(env, "APP_PASSWORD", "")

    if not configured_password or submitted_password != configured_password:
        return render_template_response(request, "login.html", status_code=401, error_message="Incorrect password. Try again.")

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
async def logout(request: Request):
    body = (await request.body()).decode("utf-8")
    form_data = parse_qs(body, keep_blank_values=True)
    submitted_csrf_token = form_data.get(CSRF_FORM_FIELD_NAME, [""])[0]
    if not request_has_valid_csrf_token(request, submitted_csrf_token):
        return render_error_response(
            request,
            error_title="Refresh Required",
            error_message="The logout form expired. Reload the dashboard and try again.",
            back_url="/",
            back_label="Back to dashboard",
            page_title="Invalid Form Submission",
            status_code=403,
        )

    response = redirect("/login")
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return response
