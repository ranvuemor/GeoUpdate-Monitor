from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    region_id: str
    region_name: str
    sample_id: str
    latitude: float
    longitude: float
    normal_imagery_date: str | None
    historical_latest_date: str | None
    effective_latest_date: str | None
    zoom_range_m: int
    checked_at: str
    normal_raw_text: str | None = None
    historical_raw_text: str | None = None
    normal_confidence: float | None = None
    historical_confidence: float | None = None
    status: str = "ok"


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with closing(self.connect()) as connection:
            with connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        region_id TEXT NOT NULL,
                        region_name TEXT NOT NULL,
                        sample_id TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        normal_imagery_date TEXT,
                        historical_latest_date TEXT,
                        effective_latest_date TEXT,
                        normal_raw_text TEXT,
                        historical_raw_text TEXT,
                        normal_confidence REAL,
                        historical_confidence REAL,
                        status TEXT NOT NULL,
                        zoom_range_m INTEGER NOT NULL,
                        checked_at TEXT NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS idx_checks_sample_checked
                    ON checks(sample_id, checked_at);

                    CREATE INDEX IF NOT EXISTS idx_checks_region_effective
                    ON checks(region_id, effective_latest_date);
                    """
                )
                self._ensure_columns(connection)

    def latest_for_sample(self, sample_id: str, region_id: str | None = None) -> CheckResult | None:
        where = "sample_id = ?"
        params: tuple[str, ...] = (sample_id,)
        if region_id is not None:
            where = "sample_id = ? AND region_id = ?"
            params = (sample_id, region_id)

        with closing(self.connect()) as connection:
            row = connection.execute(
                f"""
                SELECT * FROM checks
                WHERE {where}
                ORDER BY checked_at DESC, id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()

        return _row_to_check_result(row) if row else None

    def save_check(self, result: CheckResult) -> None:
        with closing(self.connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO checks (
                        region_id,
                        region_name,
                        sample_id,
                        latitude,
                        longitude,
                        normal_imagery_date,
                        historical_latest_date,
                        effective_latest_date,
                        normal_raw_text,
                        historical_raw_text,
                        normal_confidence,
                        historical_confidence,
                        status,
                        zoom_range_m,
                        checked_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.region_id,
                        result.region_name,
                        result.sample_id,
                        result.latitude,
                        result.longitude,
                        result.normal_imagery_date,
                        result.historical_latest_date,
                        result.effective_latest_date,
                        result.normal_raw_text,
                        result.historical_raw_text,
                        result.normal_confidence,
                        result.historical_confidence,
                        result.status,
                        result.zoom_range_m,
                        result.checked_at,
                    ),
                )

    def _ensure_columns(self, connection: sqlite3.Connection) -> None:
        existing = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(checks)").fetchall()
        }
        migrations = {
            "region_name": "ALTER TABLE checks ADD COLUMN region_name TEXT NOT NULL DEFAULT ''",
            "normal_imagery_date": "ALTER TABLE checks ADD COLUMN normal_imagery_date TEXT",
            "normal_raw_text": "ALTER TABLE checks ADD COLUMN normal_raw_text TEXT",
            "historical_raw_text": "ALTER TABLE checks ADD COLUMN historical_raw_text TEXT",
            "normal_confidence": "ALTER TABLE checks ADD COLUMN normal_confidence REAL",
            "historical_confidence": "ALTER TABLE checks ADD COLUMN historical_confidence REAL",
            "status": "ALTER TABLE checks ADD COLUMN status TEXT NOT NULL DEFAULT 'ok'",
            "zoom_range_m": "ALTER TABLE checks ADD COLUMN zoom_range_m INTEGER NOT NULL DEFAULT 100000",
        }
        for column, statement in migrations.items():
            if column not in existing:
                connection.execute(statement)
        if "normal_date" in existing:
            connection.execute(
                """
                UPDATE checks
                SET normal_imagery_date = COALESCE(normal_imagery_date, normal_date)
                WHERE normal_imagery_date IS NULL
                """
            )
        if "ocr_confidence" in existing:
            connection.execute(
                """
                UPDATE checks
                SET normal_confidence = COALESCE(normal_confidence, ocr_confidence)
                WHERE normal_confidence IS NULL
                """
            )
        if "zoom_range_meters" in existing:
            connection.execute(
                """
                UPDATE checks
                SET zoom_range_m = zoom_range_meters
                WHERE zoom_range_m = 100000
                """
            )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_check_result(row: sqlite3.Row) -> CheckResult:
    return CheckResult(
        region_id=row["region_id"],
        region_name=row["region_name"],
        sample_id=row["sample_id"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        normal_imagery_date=row["normal_imagery_date"],
        historical_latest_date=row["historical_latest_date"],
        effective_latest_date=row["effective_latest_date"],
        normal_raw_text=row["normal_raw_text"],
        historical_raw_text=row["historical_raw_text"],
        normal_confidence=row["normal_confidence"],
        historical_confidence=row["historical_confidence"],
        status=row["status"],
        zoom_range_m=row["zoom_range_m"],
        checked_at=row["checked_at"],
    )
