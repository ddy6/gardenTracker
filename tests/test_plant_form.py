import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from plant_form import PlantFormValues, parse_plant_form_body, validate_plant_form


class PlantFormTests(unittest.TestCase):
    def test_parse_plant_form_body_preserves_blank_values(self):
        values = parse_plant_form_body(
            b"name=Basil&location=&notes=&watering_interval_days=&last_watered_date="
        )

        self.assertEqual(values.name, "Basil")
        self.assertEqual(values.location, "")
        self.assertEqual(values.watering_interval_days, "")

    def test_validate_plant_form_accepts_valid_payload(self):
        payload, errors = validate_plant_form(
            PlantFormValues(
                name="Tomato",
                location="Bed A",
                notes="Needs trellis soon.",
                watering_interval_days="2",
                last_watered_date="2026-04-08",
            )
        )

        self.assertEqual(errors, {})
        self.assertEqual(payload.name, "Tomato")
        self.assertEqual(payload.watering_interval_days, 2)

    def test_validate_plant_form_rejects_invalid_interval_and_date(self):
        payload, errors = validate_plant_form(
            PlantFormValues(
                name="Pepper",
                watering_interval_days="0",
                last_watered_date="04/08/2026",
            )
        )

        self.assertIsNone(payload)
        self.assertIn("watering_interval_days", errors)
        self.assertIn("last_watered_date", errors)


if __name__ == "__main__":
    unittest.main()
