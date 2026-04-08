from db import fetch_all
from models import PlantSummary

LIST_PLANTS_QUERY = """
SELECT
    id,
    name,
    location,
    notes,
    watering_interval_days,
    last_watered_date,
    created_at,
    updated_at
FROM plants
ORDER BY datetime(created_at) DESC, id DESC
"""


async def list_plants(env) -> list[PlantSummary]:
    rows = await fetch_all(env, LIST_PLANTS_QUERY)
    return [PlantSummary.from_row(row) for row in rows]
