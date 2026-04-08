from fastapi import APIRouter, Request

from auth import request_is_authenticated
from plant_status import build_dashboard_plants, build_dashboard_summary, get_today
from plants import list_plants
from ui import build_template_context, get_env, redirect, render_template

router = APIRouter()

NOTICE_MESSAGES = {
    "created": "Plant added.",
    "updated": "Plant updated.",
    "deleted": "Plant deleted.",
    "watered": "Plant marked as watered.",
}


@router.get("/")
async def dashboard(request: Request):
    if not request_is_authenticated(request):
        return redirect("/login")

    env = get_env(request)
    today = get_today(env)
    plants = await list_plants(env)
    dashboard_plants = build_dashboard_plants(plants, today)
    summary = build_dashboard_summary(dashboard_plants)
    notice_key = request.query_params.get("notice")
    context = build_template_context(
        request,
        dashboard_plants=dashboard_plants,
        notice_message=NOTICE_MESSAGES.get(notice_key),
        today=today.isoformat(),
        **summary,
    )
    return render_template("dashboard.html", **context)
