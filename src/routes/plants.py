from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request

from auth import request_has_valid_csrf_token, request_is_authenticated
from config import CSRF_FORM_FIELD_NAME
from plant_form import PlantFormValues, parse_plant_form_body, validate_plant_form
from plant_status import get_today, normalize_status_filter
from plants import create_plant, delete_plant, get_plant, mark_plant_watered, update_plant
from ui import get_env, redirect, render_error_response, render_template_response, with_query

def require_authentication(request: Request):
    if not request_is_authenticated(request):
        return redirect("/login")
    return None


def get_redirect_status(request: Request) -> str | None:
    status_filter = normalize_status_filter(request.query_params.get("status"))
    return None if status_filter == "all" else status_filter


def dashboard_redirect(notice: str | None = None, *, status_filter: str | None = None):
    return redirect(with_query("/", notice=notice, status=status_filter))


def read_submitted_csrf_token(body: bytes) -> str:
    form_data = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return form_data.get(CSRF_FORM_FIELD_NAME, [""])[0]


def csrf_failure_response(request: Request, *, back_url: str, back_label: str):
    return render_error_response(
        request,
        error_title="Refresh Required",
        error_message="This form is no longer valid. Reload the page and try again.",
        back_url=back_url,
        back_label=back_label,
        page_title="Invalid Form Submission",
        status_code=403,
    )


def render_plant_form(
    request: Request,
    *,
    form_title: str,
    submit_label: str,
    form_action: str,
    form_values: PlantFormValues,
    errors: dict[str, str] | None = None,
    page_title: str,
    back_url: str = "/",
    status_code: int = 200,
):
    return render_template_response(
        request,
        "plant_form.html",
        page_title=page_title,
        form_title=form_title,
        submit_label=submit_label,
        form_action=form_action,
        form_values=form_values,
        errors=errors or {},
        back_url=back_url,
        status_code=status_code,
    )


def create_router() -> APIRouter:
    router = APIRouter()

    @router.get("/plants/new")
    async def new_plant_page(request: Request):
        unauthorized = require_authentication(request)
        if unauthorized:
            return unauthorized

        status_filter = get_redirect_status(request)
        return render_plant_form(
            request,
            page_title="Add Plant",
            form_title="Add Plant",
            submit_label="Save plant",
            form_action=with_query("/plants/new", status=status_filter),
            form_values=PlantFormValues(),
            back_url=with_query("/", status=status_filter),
        )

    @router.post("/plants/new")
    async def create_plant_action(request: Request):
        unauthorized = require_authentication(request)
        if unauthorized:
            return unauthorized

        status_filter = get_redirect_status(request)
        body = await request.body()
        if not request_has_valid_csrf_token(request, read_submitted_csrf_token(body)):
            return csrf_failure_response(
                request,
                back_url=with_query("/plants/new", status=status_filter),
                back_label="Back to add plant",
            )

        form_values = parse_plant_form_body(body)
        payload, errors = validate_plant_form(form_values)
        if errors:
            return render_plant_form(
                request,
                page_title="Add Plant",
                form_title="Add Plant",
                submit_label="Save plant",
                form_action=with_query("/plants/new", status=status_filter),
                form_values=form_values,
                errors=errors,
                back_url=with_query("/", status=status_filter),
                status_code=400,
            )

        await create_plant(get_env(request), payload)
        return dashboard_redirect("created", status_filter=status_filter)

    @router.get("/plants/{plant_id}/edit")
    async def edit_plant_page(request: Request, plant_id: int):
        unauthorized = require_authentication(request)
        if unauthorized:
            return unauthorized

        status_filter = get_redirect_status(request)
        plant = await get_plant(get_env(request), plant_id)
        if plant is None:
            raise HTTPException(status_code=404, detail="Plant not found")

        return render_plant_form(
            request,
            page_title=f"Edit {plant.name}",
            form_title=f"Edit {plant.name}",
            submit_label="Save changes",
            form_action=with_query(f"/plants/{plant_id}/edit", status=status_filter),
            form_values=PlantFormValues.from_plant(plant),
            back_url=with_query("/", status=status_filter),
        )

    @router.post("/plants/{plant_id}/edit")
    async def update_plant_action(request: Request, plant_id: int):
        unauthorized = require_authentication(request)
        if unauthorized:
            return unauthorized

        status_filter = get_redirect_status(request)
        body = await request.body()
        if not request_has_valid_csrf_token(request, read_submitted_csrf_token(body)):
            return csrf_failure_response(
                request,
                back_url=with_query(f"/plants/{plant_id}/edit", status=status_filter),
                back_label="Back to edit plant",
            )

        existing_plant = await get_plant(get_env(request), plant_id)
        if existing_plant is None:
            raise HTTPException(status_code=404, detail="Plant not found")

        form_values = parse_plant_form_body(body)
        payload, errors = validate_plant_form(form_values)
        if errors:
            return render_plant_form(
                request,
                page_title=f"Edit {existing_plant.name}",
                form_title=f"Edit {existing_plant.name}",
                submit_label="Save changes",
                form_action=with_query(f"/plants/{plant_id}/edit", status=status_filter),
                form_values=form_values,
                errors=errors,
                back_url=with_query("/", status=status_filter),
                status_code=400,
            )

        await update_plant(get_env(request), plant_id, payload)
        return dashboard_redirect("updated", status_filter=status_filter)

    @router.post("/plants/{plant_id}/delete")
    async def delete_plant_action(request: Request, plant_id: int):
        unauthorized = require_authentication(request)
        if unauthorized:
            return unauthorized

        status_filter = get_redirect_status(request)
        body = await request.body()
        if not request_has_valid_csrf_token(request, read_submitted_csrf_token(body)):
            return csrf_failure_response(
                request,
                back_url=with_query("/", status=status_filter),
                back_label="Back to dashboard",
            )

        plant = await get_plant(get_env(request), plant_id)
        if plant is None:
            raise HTTPException(status_code=404, detail="Plant not found")

        await delete_plant(get_env(request), plant_id)
        return dashboard_redirect("deleted", status_filter=status_filter)

    @router.post("/plants/{plant_id}/water")
    async def mark_plant_watered_action(request: Request, plant_id: int):
        unauthorized = require_authentication(request)
        if unauthorized:
            return unauthorized

        status_filter = get_redirect_status(request)
        body = await request.body()
        if not request_has_valid_csrf_token(request, read_submitted_csrf_token(body)):
            return csrf_failure_response(
                request,
                back_url=with_query("/", status=status_filter),
                back_label="Back to dashboard",
            )

        env = get_env(request)
        plant = await get_plant(env, plant_id)
        if plant is None:
            raise HTTPException(status_code=404, detail="Plant not found")

        await mark_plant_watered(env, plant_id, get_today(env).isoformat())
        return dashboard_redirect("watered", status_filter=status_filter)

    return router
