"""Tests for configuration module."""

import json
import tempfile
import unittest
from pathlib import Path

from earth_imagery_watcher.config import (
    ConfigManager,
    EarthConfig,
    IdleConfig,
    NotificationConfig,
    ScheduleRule,
    WatcherConfig,
    create_default_config_file,
)


class ConfigTests(unittest.TestCase):
    def test_earth_config_defaults(self) -> None:
        config = EarthConfig()
        self.assertTrue(config.open_earth_pro)
        self.assertEqual(config.point_delay_seconds, 5)
        self.assertTrue(config.capture_date_crop)
        self.assertEqual(config.crop_width, 500)
        self.assertEqual(config.crop_height, 120)

    def test_idle_config_defaults(self) -> None:
        config = IdleConfig()
        self.assertFalse(config.wait_until_idle)
        self.assertEqual(config.idle_minutes, 10)

    def test_notification_config_defaults(self) -> None:
        config = NotificationConfig()
        self.assertFalse(config.enabled)
        self.assertIsNone(config.email_recipients)

    def test_watcher_config_nested_normalization(self) -> None:
        config = WatcherConfig(
            earth={"open_earth_pro": False, "point_delay_seconds": 10},
            idle={"wait_until_idle": True, "idle_minutes": 5},
        )
        self.assertIsInstance(config.earth, EarthConfig)
        self.assertFalse(config.earth.open_earth_pro)
        self.assertEqual(config.earth.point_delay_seconds, 10)
        self.assertIsInstance(config.idle, IdleConfig)
        self.assertTrue(config.idle.wait_until_idle)
        self.assertEqual(config.idle.idle_minutes, 5)

    def test_schedule_rule_creation(self) -> None:
        rule = ScheduleRule(
            name="daily-check",
            geojson_path="regions/delhi.geojson",
            frequency="daily",
            hour_of_day=8,
        )
        self.assertEqual(rule.name, "daily-check")
        self.assertEqual(rule.frequency, "daily")
        self.assertEqual(rule.hour_of_day, 8)

    def test_config_manager_defaults(self) -> None:
        manager = ConfigManager()
        config = manager.config
        self.assertIsNotNone(config)
        self.assertIsInstance(config.earth, EarthConfig)

    def test_config_manager_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            manager = ConfigManager(config_path)
            config = WatcherConfig(
                db_path="custom.sqlite",
                earth=EarthConfig(open_earth_pro=False),
            )
            manager.save(config)
            
            self.assertTrue(config_path.exists())
            
            manager2 = ConfigManager(config_path)
            self.assertEqual(manager2.config.db_path, "custom.sqlite")
            self.assertFalse(manager2.config.earth.open_earth_pro)

    def test_create_default_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            create_default_config_file(config_path)
            
            self.assertTrue(config_path.exists())
            
            with open(config_path) as f:
                data = json.load(f)
            
            self.assertEqual(data["version"], "1")
            self.assertIn("earth", data)
            self.assertIn("idle", data)


if __name__ == "__main__":
    unittest.main()
