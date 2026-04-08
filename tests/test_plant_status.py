import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models import PlantSummary
from plant_status import (
    build_dashboard_plants,
    build_dashboard_summary,
    filter_dashboard_plants,
    normalize_status_filter,
)


def make_plant(*, plant_id: int, name: str, interval: int | None, last_watered: str | None):
    return PlantSummary(
        id=plant_id,
        name=name,
        location=None,
        notes=None,
        watering_interval_days=interval,
        last_watered_date=last_watered,
        created_at=None,
        updated_at=None,
    )


class PlantStatusTests(unittest.TestCase):
    def test_status_assignment_and_sorting(self):
        today = date(2026, 4, 8)
        plants = [
            make_plant(plant_id=1, name="Good", interval=5, last_watered="2026-04-07"),
            make_plant(plant_id=2, name="Overdue", interval=2, last_watered="2026-04-01"),
            make_plant(plant_id=3, name="Due Soon", interval=2, last_watered="2026-04-07"),
            make_plant(plant_id=4, name="No Schedule", interval=None, last_watered=None),
            make_plant(plant_id=5, name="Needs Baseline", interval=4, last_watered=None),
        ]

        dashboard_plants = build_dashboard_plants(plants, today)

        self.assertEqual(
            [item.plant.name for item in dashboard_plants],
            ["Overdue", "Needs Baseline", "Due Soon", "Good", "No Schedule"],
        )
        self.assertEqual(dashboard_plants[0].status_key, "overdue")
        self.assertEqual(dashboard_plants[1].status_key, "due-soon")
        self.assertEqual(dashboard_plants[2].status_key, "due-soon")
        self.assertEqual(dashboard_plants[3].status_key, "good")
        self.assertEqual(dashboard_plants[4].status_key, "no-schedule")

    def test_summary_counts(self):
        today = date(2026, 4, 8)
        dashboard_plants = build_dashboard_plants(
            [
                make_plant(plant_id=1, name="Overdue", interval=1, last_watered="2026-04-01"),
                make_plant(plant_id=2, name="Soon", interval=2, last_watered="2026-04-07"),
                make_plant(plant_id=3, name="No Schedule", interval=None, last_watered=None),
            ],
            today,
        )

        summary = build_dashboard_summary(dashboard_plants)

        self.assertEqual(summary["total_plants"], 3)
        self.assertEqual(summary["overdue_count"], 1)
        self.assertEqual(summary["due_soon_count"], 1)
        self.assertEqual(summary["good_count"], 0)
        self.assertEqual(summary["no_schedule_count"], 1)

    def test_status_filtering(self):
        today = date(2026, 4, 8)
        dashboard_plants = build_dashboard_plants(
            [
                make_plant(plant_id=1, name="Overdue", interval=1, last_watered="2026-04-01"),
                make_plant(plant_id=2, name="Soon", interval=2, last_watered="2026-04-07"),
                make_plant(plant_id=3, name="Good", interval=5, last_watered="2026-04-08"),
            ],
            today,
        )

        self.assertEqual(normalize_status_filter(None), "all")
        self.assertEqual(normalize_status_filter("not-a-filter"), "all")
        self.assertEqual(normalize_status_filter("good"), "good")
        self.assertEqual(
            [item.plant.name for item in filter_dashboard_plants(dashboard_plants, "due-soon")],
            ["Soon"],
        )
        self.assertEqual(
            [item.plant.name for item in filter_dashboard_plants(dashboard_plants, "all")],
            ["Overdue", "Soon", "Good"],
        )


if __name__ == "__main__":
    unittest.main()
