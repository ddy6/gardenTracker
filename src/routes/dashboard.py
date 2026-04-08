from fastapi import APIRouter, Request

from auth import request_is_authenticated
from plants import list_plants
from ui import build_template_context, get_env, redirect, render_template

router = APIRouter()

NOTICE_MESSAGES = {
    "created": "Plant added.",
    "updated": "Plant updated.",
    "deleted": "Plant deleted.",
}


@router.get("/")
async def dashboard(request: Request):
    if not request_is_authenticated(request):
        return redirect("/login")

    plants = await list_plants(get_env(request))
    scheduled_plants = sum(1 for plant in plants if plant.watering_interval_days is not None)
    notice_key = request.query_params.get("notice")
    context = build_template_context(
        request,
        plants=plants,
        total_plants=len(plants),
        scheduled_plants=scheduled_plants,
        unscheduled_plants=len(plants) - scheduled_plants,
        notice_message=NOTICE_MESSAGES.get(notice_key),
    )
    return render_template("dashboard.html", **context)
