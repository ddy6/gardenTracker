from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config import get_timezone_name

STATUS_SORT_ORDER = {
    "overdue": 0,
    "due-soon": 1,
    "good": 2,
    "no-schedule": 3,
}


@dataclass(slots=True)
class DashboardPlant:
    plant: object
    status_key: str
    status_label: str
    next_due_date: date | None
    next_due_display: str
    due_hint: str
    sort_rank: int


def get_today(env) -> date:
    timezone_name = get_timezone_name(env)
    try:
        return datetime.now(ZoneInfo(timezone_name)).date()
    except (ZoneInfoNotFoundError, ValueError):
        return date.today()


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def format_due_date(value: date | None, today: date) -> str:
    if value is None:
        return "No schedule"
    if value == today:
        return "Today"
    if value == today + timedelta(days=1):
        return "Tomorrow"
    return value.isoformat()


def format_due_hint(next_due_date: date | None, today: date, *, has_schedule: bool) -> str:
    if not has_schedule:
        return "Set a watering interval to track due dates."
    if next_due_date is None:
        return "Needs a last watered date."

    delta_days = (next_due_date - today).days
    if delta_days < 0:
        overdue_days = abs(delta_days)
        return f"Overdue by {overdue_days} day{'s' if overdue_days != 1 else ''}."
    if delta_days == 0:
        return "Due today."
    if delta_days == 1:
        return "Due tomorrow."
    return f"Due in {delta_days} days."


def build_dashboard_plant(plant, today: date) -> DashboardPlant:
    if plant.watering_interval_days is None:
        status_key = "no-schedule"
        next_due_date = None
    else:
        last_watered_date = parse_iso_date(plant.last_watered_date)
        if last_watered_date is None:
            next_due_date = today
        else:
            next_due_date = last_watered_date + timedelta(days=plant.watering_interval_days)

        days_until_due = (next_due_date - today).days
        if days_until_due < 0:
            status_key = "overdue"
        elif days_until_due <= 2:
            status_key = "due-soon"
        else:
            status_key = "good"

    status_label = {
        "overdue": "Overdue",
        "due-soon": "Due soon",
        "good": "Good",
        "no-schedule": "No schedule",
    }[status_key]

    return DashboardPlant(
        plant=plant,
        status_key=status_key,
        status_label=status_label,
        next_due_date=next_due_date,
        next_due_display=format_due_date(next_due_date, today),
        due_hint=format_due_hint(next_due_date, today, has_schedule=plant.watering_interval_days is not None),
        sort_rank=STATUS_SORT_ORDER[status_key],
    )


def build_dashboard_plants(plants: list, today: date) -> list[DashboardPlant]:
    dashboard_plants = [build_dashboard_plant(plant, today) for plant in plants]
    return sorted(
        dashboard_plants,
        key=lambda item: (
            item.sort_rank,
            item.next_due_date or date.max,
            item.plant.name.lower(),
            item.plant.id,
        ),
    )


def build_dashboard_summary(dashboard_plants: list[DashboardPlant]) -> dict[str, int]:
    overdue_count = sum(1 for item in dashboard_plants if item.status_key == "overdue")
    due_soon_count = sum(1 for item in dashboard_plants if item.status_key == "due-soon")
    no_schedule_count = sum(1 for item in dashboard_plants if item.status_key == "no-schedule")
    return {
        "total_plants": len(dashboard_plants),
        "overdue_count": overdue_count,
        "due_soon_count": due_soon_count,
        "no_schedule_count": no_schedule_count,
    }
