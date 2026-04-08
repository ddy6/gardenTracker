import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models import PlantSummary


class PlantSummaryTests(unittest.TestCase):
    def test_from_row_normalizes_fields(self):
        row = {
            "id": "7",
            "name": "Basil",
            "location": None,
            "notes": "Pinch top leaves often to keep it bushy.",
            "watering_interval_days": "3",
            "last_watered_date": None,
            "created_at": "2026-04-08T12:00:00",
            "updated_at": "2026-04-08T12:00:00",
        }

        plant = PlantSummary.from_row(row)

        self.assertEqual(plant.id, 7)
        self.assertEqual(plant.location_display, "Unassigned")
        self.assertEqual(plant.schedule_display, "Every 3 days")
        self.assertEqual(plant.last_watered_display, "Never")

    def test_note_preview_truncates_long_copy(self):
        plant = PlantSummary(
            id=1,
            name="Tomato",
            location="Bed A",
            notes="A" * 120,
            watering_interval_days=None,
            last_watered_date=None,
            created_at=None,
            updated_at=None,
        )

        self.assertTrue(plant.note_preview.endswith("..."))
        self.assertLessEqual(len(plant.note_preview), 96)


if __name__ == "__main__":
    unittest.main()
