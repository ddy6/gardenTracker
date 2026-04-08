from fastapi import APIRouter, Request

from auth import request_is_authenticated
from plant_status import (
    STATUS_FILTER_LABELS,
    build_dashboard_plants,
    build_dashboard_summary,
    filter_dashboard_plants,
    get_today,
    normalize_status_filter,
)
from plants import list_plants
from ui import get_env, redirect, render_template_response, with_query

NOTICE_MESSAGES = {
    "created": "Plant added.",
    "updated": "Plant updated.",
    "deleted": "Plant deleted.",
    "watered": "Plant marked as watered.",
}
FILTER_ORDER = ("all", "overdue", "due-soon", "good", "no-schedule")


def create_router() -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def dashboard(request: Request):
        if not request_is_authenticated(request):
            return redirect("/login")

        env = get_env(request)
        today = get_today(env)
        plants = await list_plants(env)
        dashboard_plants = build_dashboard_plants(plants, today)
        summary = build_dashboard_summary(dashboard_plants)
        active_status_filter = normalize_status_filter(request.query_params.get("status"))
        visible_dashboard_plants = filter_dashboard_plants(dashboard_plants, active_status_filter)
        notice_key = request.query_params.get("notice")
        filter_counts = {
            "all": summary["total_plants"],
            "overdue": summary["overdue_count"],
            "due-soon": summary["due_soon_count"],
            "good": summary["good_count"],
            "no-schedule": summary["no_schedule_count"],
        }
        status_filters = [
            {
                "key": key,
                "label": STATUS_FILTER_LABELS[key],
                "count": filter_counts[key],
                "is_active": key == active_status_filter,
                "url": with_query("/", status=None if key == "all" else key),
            }
            for key in FILTER_ORDER
        ]
        return render_template_response(
            request,
            "dashboard.html",
            dashboard_plants=visible_dashboard_plants,
            notice_message=NOTICE_MESSAGES.get(notice_key),
            today=today.isoformat(),
            active_status_filter=active_status_filter,
            active_status_label=STATUS_FILTER_LABELS[active_status_filter],
            status_filters=status_filters,
            visible_plants_count=len(visible_dashboard_plants),
            new_plant_url=with_query("/plants/new", status=None if active_status_filter == "all" else active_status_filter),
            **summary,
        )

    return router
