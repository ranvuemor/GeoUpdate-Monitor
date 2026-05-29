from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    region_id: str
    sample_id: str
    latitude: float
    longitude: float
    normal_date: str | None
    historical_latest_date: str | None
    effective_latest_date: str | None
    ocr_confidence: float | None
    zoom_range_meters: int
    checked_at: str


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region_id TEXT NOT NULL,
                    sample_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    normal_date TEXT,
                    historical_latest_date TEXT,
                    effective_latest_date TEXT,
                    ocr_confidence REAL,
                    zoom_range_meters INTEGER NOT NULL,
                    checked_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_checks_sample_checked
                ON checks(sample_id, checked_at);

                CREATE INDEX IF NOT EXISTS idx_checks_region_effective
                ON checks(region_id, effective_latest_date);
                """
            )

    def latest_for_sample(self, sample_id: str) -> CheckResult | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM checks
                WHERE sample_id = ?
                ORDER BY checked_at DESC, id DESC
                LIMIT 1
                """,
                (sample_id,),
            ).fetchone()

        return _row_to_check_result(row) if row else None

    def save_check(self, result: CheckResult) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO checks (
                    region_id,
                    sample_id,
                    latitude,
                    longitude,
                    normal_date,
                    historical_latest_date,
                    effective_latest_date,
                    ocr_confidence,
                    zoom_range_meters,
                    checked_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.region_id,
                    result.sample_id,
                    result.latitude,
                    result.longitude,
                    result.normal_date,
                    result.historical_latest_date,
                    result.effective_latest_date,
                    result.ocr_confidence,
                    result.zoom_range_meters,
                    result.checked_at,
                ),
            )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_check_result(row: sqlite3.Row) -> CheckResult:
    return CheckResult(
        region_id=row["region_id"],
        sample_id=row["sample_id"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        normal_date=row["normal_date"],
        historical_latest_date=row["historical_latest_date"],
        effective_latest_date=row["effective_latest_date"],
        ocr_confidence=row["ocr_confidence"],
        zoom_range_meters=row["zoom_range_meters"],
        checked_at=row["checked_at"],
    )
