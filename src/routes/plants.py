from fastapi import APIRouter, HTTPException, Request

from auth import request_is_authenticated
from plant_form import PlantFormValues, parse_plant_form_body, validate_plant_form
from plant_status import get_today, normalize_status_filter
from plants import create_plant, delete_plant, get_plant, mark_plant_watered, update_plant
from ui import build_template_context, get_env, redirect, render_template, with_query

router = APIRouter()


def require_authentication(request: Request):
    if not request_is_authenticated(request):
        return redirect("/login")
    return None


def get_redirect_status(request: Request) -> str | None:
    status_filter = normalize_status_filter(request.query_params.get("status"))
    return None if status_filter == "all" else status_filter


def dashboard_redirect(notice: str | None = None, *, status_filter: str | None = None):
    return redirect(with_query("/", notice=notice, status=status_filter))


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
    context = build_template_context(
        request,
        page_title=page_title,
        form_title=form_title,
        submit_label=submit_label,
        form_action=form_action,
        form_values=form_values,
        errors=errors or {},
        back_url=back_url,
    )
    return render_template("plant_form.html", **context) if status_code == 200 else render_template_with_status("plant_form.html", status_code, **context)


def render_template_with_status(name: str, status_code: int, **context):
    response = render_template(name, **context)
    response.status_code = status_code
    return response


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
    form_values = parse_plant_form_body(await request.body())
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
    existing_plant = await get_plant(get_env(request), plant_id)
    if existing_plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    form_values = parse_plant_form_body(await request.body())
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
    env = get_env(request)
    plant = await get_plant(env, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    await mark_plant_watered(env, plant_id, get_today(env).isoformat())
    return dashboard_redirect("watered", status_filter=status_filter)
