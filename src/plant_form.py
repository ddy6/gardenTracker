from dataclasses import dataclass
from datetime import date
from urllib.parse import parse_qs


@dataclass(slots=True)
class PlantFormValues:
    name: str = ""
    location: str = ""
    notes: str = ""
    watering_interval_days: str = ""
    last_watered_date: str = ""

    @classmethod
    def from_row(cls, row):
        return cls(
            name=row["name"],
            location=row.get("location") or "",
            notes=row.get("notes") or "",
            watering_interval_days="" if row.get("watering_interval_days") in (None, "") else str(row["watering_interval_days"]),
            last_watered_date=row.get("last_watered_date") or "",
        )

    @classmethod
    def from_plant(cls, plant):
        return cls(
            name=plant.name,
            location=plant.location or "",
            notes=plant.notes or "",
            watering_interval_days="" if plant.watering_interval_days is None else str(plant.watering_interval_days),
            last_watered_date=plant.last_watered_date or "",
        )


@dataclass(slots=True)
class PlantWritePayload:
    name: str
    location: str | None
    notes: str | None
    watering_interval_days: int | None
    last_watered_date: str | None


def _read_first(form_data, key: str) -> str:
    return form_data.get(key, [""])[0].strip()


def parse_plant_form_body(body: bytes) -> PlantFormValues:
    form_data = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return PlantFormValues(
        name=_read_first(form_data, "name"),
        location=_read_first(form_data, "location"),
        notes=_read_first(form_data, "notes"),
        watering_interval_days=_read_first(form_data, "watering_interval_days"),
        last_watered_date=_read_first(form_data, "last_watered_date"),
    )


def validate_plant_form(values: PlantFormValues) -> tuple[PlantWritePayload | None, dict[str, str]]:
    errors: dict[str, str] = {}

    name = values.name.strip()
    if not name:
        errors["name"] = "Plant name is required."

    watering_interval_days = None
    if values.watering_interval_days:
        try:
            watering_interval_days = int(values.watering_interval_days)
        except ValueError:
            errors["watering_interval_days"] = "Watering interval must be a whole number."
        else:
            if watering_interval_days <= 0:
                errors["watering_interval_days"] = "Watering interval must be greater than zero."

    last_watered_date = values.last_watered_date or None
    if last_watered_date:
        try:
            date.fromisoformat(last_watered_date)
        except ValueError:
            errors["last_watered_date"] = "Last watered date must use YYYY-MM-DD."

    if errors:
        return None, errors

    return (
        PlantWritePayload(
            name=name,
            location=values.location or None,
            notes=values.notes or None,
            watering_interval_days=watering_interval_days,
            last_watered_date=last_watered_date,
        ),
        {},
    )
