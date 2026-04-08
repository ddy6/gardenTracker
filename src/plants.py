from db import execute, fetch_all, fetch_one
from models import PlantSummary
from plant_form import PlantWritePayload

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

GET_PLANT_QUERY = """
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
WHERE id = ?
"""

CREATE_PLANT_QUERY = """
INSERT INTO plants (
    name,
    location,
    notes,
    watering_interval_days,
    last_watered_date,
    created_at,
    updated_at
)
VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
"""

UPDATE_PLANT_QUERY = """
UPDATE plants
SET
    name = ?,
    location = ?,
    notes = ?,
    watering_interval_days = ?,
    last_watered_date = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?
"""

DELETE_PLANT_QUERY = """
DELETE FROM plants
WHERE id = ?
"""


async def list_plants(env) -> list[PlantSummary]:
    rows = await fetch_all(env, LIST_PLANTS_QUERY)
    return [PlantSummary.from_row(row) for row in rows]


async def get_plant(env, plant_id: int) -> PlantSummary | None:
    row = await fetch_one(env, GET_PLANT_QUERY, plant_id)
    if not row:
        return None
    return PlantSummary.from_row(row)


async def create_plant(env, payload: PlantWritePayload) -> None:
    await execute(
        env,
        CREATE_PLANT_QUERY,
        payload.name,
        payload.location,
        payload.notes,
        payload.watering_interval_days,
        payload.last_watered_date,
    )


async def update_plant(env, plant_id: int, payload: PlantWritePayload) -> None:
    await execute(
        env,
        UPDATE_PLANT_QUERY,
        payload.name,
        payload.location,
        payload.notes,
        payload.watering_interval_days,
        payload.last_watered_date,
        plant_id,
    )


async def delete_plant(env, plant_id: int) -> None:
    await execute(env, DELETE_PLANT_QUERY, plant_id)
