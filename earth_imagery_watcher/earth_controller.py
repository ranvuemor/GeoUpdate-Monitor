from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ImageryDateReading:
    normal_date_text: str | None
    historical_latest_date_text: str | None
    normal_confidence: float | None = None
    historical_confidence: float | None = None


class EarthController(Protocol):
    def open_kml(self, kml_path: Path) -> None:
        """Open a KML file in Google Earth Pro."""

    def read_imagery_dates(self) -> ImageryDateReading:
        """Read normal and latest historical imagery dates from the UI."""


class NotImplementedEarthController:
    def open_kml(self, kml_path: Path) -> None:
        raise NotImplementedError("Google Earth Pro automation is not implemented in this MVP.")

    def read_imagery_dates(self) -> ImageryDateReading:
        raise NotImplementedError("Google Earth Pro OCR automation is not implemented in this MVP.")
