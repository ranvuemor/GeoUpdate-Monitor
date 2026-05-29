import tempfile
import unittest
from pathlib import Path

from earth_imagery_watcher.database import CheckResult, Database


class DatabaseTests(unittest.TestCase):
    def test_initialize_insert_and_retrieve_latest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "watcher.sqlite"
            database = Database(db_path)
            database.initialize()

            result = CheckResult(
                region_id="region-1",
                region_name="Region One",
                sample_id="point-1",
                latitude=52.5,
                longitude=13.4,
                normal_imagery_date="2024-05-01",
                historical_latest_date="2024-06-01",
                effective_latest_date="2024-06-01",
                normal_raw_text="Imagery Date: May 2024",
                historical_raw_text="Imagery Date: June 2024",
                normal_confidence=87.5,
                historical_confidence=91.0,
                status="manual",
                zoom_range_m=100000,
                checked_at="2026-05-29T09:00:00+00:00",
            )

            database.save_check(result)
            latest = database.latest_for_sample("point-1", region_id="region-1")

            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest.normal_imagery_date, "2024-05-01")
            self.assertEqual(latest.historical_latest_date, "2024-06-01")
            self.assertEqual(latest.effective_latest_date, "2024-06-01")
            self.assertEqual(latest.normal_raw_text, "Imagery Date: May 2024")
            self.assertEqual(latest.historical_raw_text, "Imagery Date: June 2024")
            self.assertEqual(latest.normal_confidence, 87.5)
            self.assertEqual(latest.historical_confidence, 91.0)
            self.assertEqual(latest.status, "manual")
            self.assertEqual(latest.zoom_range_m, 100000)


if __name__ == "__main__":
    unittest.main()
