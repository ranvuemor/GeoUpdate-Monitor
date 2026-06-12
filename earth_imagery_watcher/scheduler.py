"""Scheduling system for recurring imagery checks."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Callable


class SimpleScheduler:
    """Simple in-process scheduler for running checks on intervals."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self._jobs: dict[str, ScheduledJob] = {}
        self._running = False
    
    def add_hourly_job(
        self,
        job_id: str,
        callback: Callable[[], None],
        minute: int = 0,
        start_immediately: bool = False,
    ) -> None:
        """Schedule a job to run hourly at a specific minute.
        
        Args:
            job_id: Unique identifier for this job.
            callback: Function to call when job is due.
            minute: Minute of the hour to run (0-59).
            start_immediately: If True, run now before scheduling.
        """
        job = ScheduledJob(
            job_id=job_id,
            callback=callback,
            frequency="hourly",
            hour=None,
            minute=minute,
            start_immediately=start_immediately,
        )
        self._jobs[job_id] = job
    
    def add_daily_job(
        self,
        job_id: str,
        callback: Callable[[], None],
        hour: int = 0,
        minute: int = 0,
        start_immediately: bool = False,
    ) -> None:
        """Schedule a job to run daily at a specific time.
        
        Args:
            job_id: Unique identifier for this job.
            callback: Function to call when job is due.
            hour: Hour of the day to run (0-23).
            minute: Minute of the hour to run (0-59).
            start_immediately: If True, run now before scheduling.
        """
        job = ScheduledJob(
            job_id=job_id,
            callback=callback,
            frequency="daily",
            hour=hour,
            minute=minute,
            start_immediately=start_immediately,
        )
        self._jobs[job_id] = job
    
    def add_interval_job(
        self,
        job_id: str,
        callback: Callable[[], None],
        interval_minutes: int = 60,
        start_immediately: bool = False,
    ) -> None:
        """Schedule a job to run at regular intervals.
        
        Args:
            job_id: Unique identifier for this job.
            callback: Function to call when job is due.
            interval_minutes: How often to run (in minutes).
            start_immediately: If True, run now before scheduling.
        """
        job = ScheduledJob(
            job_id=job_id,
            callback=callback,
            frequency="interval",
            interval_minutes=interval_minutes,
            start_immediately=start_immediately,
        )
        self._jobs[job_id] = job
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.
        
        Args:
            job_id: ID of the job to remove.
            
        Returns:
            True if job was removed, False if not found.
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    def get_job(self, job_id: str) -> ScheduledJob | None:
        """Get a scheduled job by ID."""
        return self._jobs.get(job_id)
    
    def list_jobs(self) -> list[ScheduledJob]:
        """List all scheduled jobs."""
        return list(self._jobs.values())
    
    def run_once(self, blocking: bool = False) -> int:
        """Run all due jobs once.
        
        Args:
            blocking: If True, run until no jobs are available.
            
        Returns:
            Number of jobs executed.
        """
        executed = 0
        now = datetime.now(timezone.utc)
        
        for job in self._jobs.values():
            if job.is_due(now):
                try:
                    job.run()
                    executed += 1
                except Exception as exc:
                    print(f"Error running job {job.job_id}: {exc}")
        
        return executed
    
    def run_forever(self, check_interval_seconds: float = 60) -> None:
        """Run scheduler indefinitely, checking jobs at intervals.
        
        Args:
            check_interval_seconds: How often to check for due jobs.
        """
        self._running = True
        try:
            while self._running:
                self.run_once()
                time.sleep(check_interval_seconds)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
        finally:
            self._running = False
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False


class ScheduledJob:
    """Represents a single scheduled job."""
    
    def __init__(
        self,
        job_id: str,
        callback: Callable[[], None],
        frequency: str = "interval",
        hour: int | None = None,
        minute: int | None = None,
        interval_minutes: int | None = None,
        start_immediately: bool = False,
    ):
        """Initialize a scheduled job.
        
        Args:
            job_id: Unique identifier.
            callback: Function to call when due.
            frequency: "hourly", "daily", or "interval".
            hour: Hour (0-23) for daily jobs.
            minute: Minute (0-59) for hourly/daily jobs.
            interval_minutes: Interval in minutes for interval jobs.
            start_immediately: If True, run immediately.
        """
        self.job_id = job_id
        self.callback = callback
        self.frequency = frequency
        self.hour = hour
        self.minute = minute or 0
        self.interval_minutes = interval_minutes or 60
        
        if start_immediately:
            self.last_run = datetime.min.replace(tzinfo=timezone.utc)
        else:
            self.last_run = datetime.now(timezone.utc)
    
    def is_due(self, now: datetime | None = None) -> bool:
        """Check if this job is due to run.
        
        Args:
            now: Current time. If None, uses current time.
            
        Returns:
            True if job is due.
        """
        now = now or datetime.now(timezone.utc)
        
        if self.frequency == "interval":
            elapsed = (now - self.last_run).total_seconds() / 60
            return elapsed >= self.interval_minutes
        
        elif self.frequency == "hourly":
            if self.last_run.minute == now.minute and self.last_run.hour == now.hour:
                return False
            return now.minute == self.minute
        
        elif self.frequency == "daily":
            if self.last_run.date() == now.date():
                return False
            return now.hour == self.hour and now.minute == self.minute
        
        return False
    
    def run(self) -> None:
        """Execute this job."""
        self.callback()
        self.last_run = datetime.now(timezone.utc)
    
    def reset(self) -> None:
        """Reset the last run time."""
        self.last_run = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        """String representation of the job."""
        if self.frequency == "interval":
            return f"<ScheduledJob {self.job_id} every {self.interval_minutes} minutes>"
        elif self.frequency == "hourly":
            return f"<ScheduledJob {self.job_id} hourly at :{self.minute:02d}>"
        elif self.frequency == "daily":
            return f"<ScheduledJob {self.job_id} daily at {self.hour:02d}:{self.minute:02d}>"
        return f"<ScheduledJob {self.job_id}>"
