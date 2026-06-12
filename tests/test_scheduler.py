"""Tests for scheduler module."""

import time
import unittest
from datetime import datetime, timezone

from earth_imagery_watcher.scheduler import ScheduledJob, SimpleScheduler


class SchedulerTests(unittest.TestCase):
    def test_scheduled_job_interval_is_due(self) -> None:
        call_count = [0]
        
        def callback() -> None:
            call_count[0] += 1
        
        job = ScheduledJob(
            job_id="test",
            callback=callback,
            frequency="interval",
            interval_minutes=1,
            start_immediately=False,
        )
        
        now = datetime.now(timezone.utc)
        self.assertFalse(job.is_due(now))
        
        # Set last_run to 2 minutes ago
        job.last_run = datetime.fromtimestamp(now.timestamp() - 120, tz=timezone.utc)
        self.assertTrue(job.is_due(now))

    def test_scheduled_job_hourly_is_due(self) -> None:
        job = ScheduledJob(
            job_id="test",
            callback=lambda: None,
            frequency="hourly",
            minute=30,
            start_immediately=False,
        )
        
        now_at_30 = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        self.assertTrue(job.is_due(now_at_30))
        
        now_at_31 = datetime(2024, 1, 1, 12, 31, 0, tzinfo=timezone.utc)
        self.assertFalse(job.is_due(now_at_31))

    def test_scheduled_job_daily_is_due(self) -> None:
        job = ScheduledJob(
            job_id="test",
            callback=lambda: None,
            frequency="daily",
            hour=8,
            minute=0,
            start_immediately=False,
        )
        
        now_at_8am = datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(job.is_due(now_at_8am))
        
        later_same_day = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        self.assertFalse(job.is_due(later_same_day))
        
        next_day_at_8am = datetime(2024, 1, 2, 8, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(job.is_due(next_day_at_8am))

    def test_scheduled_job_run(self) -> None:
        call_count = [0]
        
        def callback() -> None:
            call_count[0] += 1
        
        job = ScheduledJob(
            job_id="test",
            callback=callback,
            frequency="interval",
            interval_minutes=1,
        )
        
        old_last_run = job.last_run
        job.run()
        
        self.assertEqual(call_count[0], 1)
        self.assertGreater(job.last_run, old_last_run)

    def test_simple_scheduler_add_interval_job(self) -> None:
        scheduler = SimpleScheduler()
        call_count = [0]
        
        def callback() -> None:
            call_count[0] += 1
        
        scheduler.add_interval_job("test-job", callback, interval_minutes=5)
        jobs = scheduler.list_jobs()
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].job_id, "test-job")

    def test_simple_scheduler_run_once(self) -> None:
        scheduler = SimpleScheduler()
        call_count = [0]
        
        def callback() -> None:
            call_count[0] += 1
        
        scheduler.add_interval_job(
            "test-job", callback, interval_minutes=5, start_immediately=True
        )
        
        executed = scheduler.run_once()
        self.assertEqual(executed, 1)
        self.assertEqual(call_count[0], 1)

    def test_simple_scheduler_remove_job(self) -> None:
        scheduler = SimpleScheduler()
        scheduler.add_interval_job("test-job", lambda: None)
        
        self.assertTrue(scheduler.remove_job("test-job"))
        self.assertIsNone(scheduler.get_job("test-job"))
        self.assertFalse(scheduler.remove_job("nonexistent"))

    def test_simple_scheduler_add_daily_job(self) -> None:
        scheduler = SimpleScheduler()
        scheduler.add_daily_job("daily", lambda: None, hour=8, minute=30)
        
        job = scheduler.get_job("daily")
        self.assertIsNotNone(job)
        self.assertEqual(job.frequency, "daily")
        self.assertEqual(job.hour, 8)
        self.assertEqual(job.minute, 30)

    def test_simple_scheduler_add_hourly_job(self) -> None:
        scheduler = SimpleScheduler()
        scheduler.add_hourly_job("hourly", lambda: None, minute=15)
        
        job = scheduler.get_job("hourly")
        self.assertIsNotNone(job)
        self.assertEqual(job.frequency, "hourly")
        self.assertEqual(job.minute, 15)


if __name__ == "__main__":
    unittest.main()
