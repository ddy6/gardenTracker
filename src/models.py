from dataclasses import dataclass


def _maybe_none(value):
    if value is None or type(value).__name__ == "JsNull":
        return None
    return value


def _int_or_none(value):
    value = _maybe_none(value)
    if value is None or value == "":
        return None
    return int(value)


@dataclass(slots=True)
class PlantSummary:
    id: int
    name: str
    location: str | None
    notes: str | None
    watering_interval_days: int | None
    last_watered_date: str | None
    created_at: str | None
    updated_at: str | None

    @classmethod
    def from_row(cls, row):
        return cls(
            id=int(row["id"]),
            name=row["name"],
            location=_maybe_none(row.get("location")),
            notes=_maybe_none(row.get("notes")),
            watering_interval_days=_int_or_none(row.get("watering_interval_days")),
            last_watered_date=_maybe_none(row.get("last_watered_date")),
            created_at=_maybe_none(row.get("created_at")),
            updated_at=_maybe_none(row.get("updated_at")),
        )

    @property
    def location_display(self) -> str:
        return self.location or "Unassigned"

    @property
    def last_watered_display(self) -> str:
        return self.last_watered_date or "Never"

    @property
    def schedule_display(self) -> str:
        if self.watering_interval_days is None:
            return "No schedule"
        return f"Every {self.watering_interval_days} day{'s' if self.watering_interval_days != 1 else ''}"

    @property
    def note_preview(self) -> str:
        if not self.notes or not self.notes.strip():
            return "No notes yet."

        note = self.notes.strip()
        if len(note) <= 96:
            return note
        return f"{note[:93].rstrip()}..."
