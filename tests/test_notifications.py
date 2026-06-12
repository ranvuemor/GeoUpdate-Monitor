"""Tests for notifications module."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from earth_imagery_watcher.notifications import (
    DateChangeEvent,
    EventLogger,
    NotificationSender,
)


class NotificationSenderTests(unittest.TestCase):
    def test_sender_initialization(self) -> None:
        sender = NotificationSender(
            webhook_url="https://example.com/webhook",
            email_config={
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "sender": "bot@example.com",
                "password": "secret",
            },
        )
        
        self.assertEqual(sender.webhook_url, "https://example.com/webhook")
        self.assertEqual(sender.email_config["smtp_server"], "smtp.example.com")


class EventLoggerTests(unittest.TestCase):
    def test_event_logger_initialization(self) -> None:
        logger = EventLogger()
        self.assertIsNone(logger.log_path)

    def test_event_logger_with_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            logger = EventLogger(log_path)
            
            event = DateChangeEvent(
                region_name="Test Region",
                sample_id="sample-1",
                latitude=52.5,
                longitude=13.4,
                old_normal_date="2024-01-01",
                new_normal_date="2024-02-01",
                old_historical_date=None,
                new_historical_date=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            
            success = logger.log_event(event)
            self.assertTrue(success)
            self.assertTrue(log_path.exists())
            
            with open(log_path) as f:
                lines = f.readlines()
            
            self.assertEqual(len(lines), 1)

    def test_event_logger_no_path(self) -> None:
        logger = EventLogger()
        event = DateChangeEvent(
            region_name="Test Region",
            sample_id="sample-1",
            latitude=52.5,
            longitude=13.4,
            old_normal_date="2024-01-01",
            new_normal_date="2024-02-01",
            old_historical_date=None,
            new_historical_date=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        success = logger.log_event(event)
        self.assertFalse(success)

    def test_date_change_event_creation(self) -> None:
        event = DateChangeEvent(
            region_name="Delhi",
            sample_id="delhi-1",
            latitude=28.7041,
            longitude=77.1025,
            old_normal_date="2024-01-15",
            new_normal_date="2024-02-20",
            old_historical_date="2023-12-01",
            new_historical_date="2024-02-15",
            timestamp="2024-02-21T10:30:00Z",
        )
        
        self.assertEqual(event.region_name, "Delhi")
        self.assertEqual(event.old_normal_date, "2024-01-15")
        self.assertEqual(event.new_normal_date, "2024-02-20")


if __name__ == "__main__":
    unittest.main()
