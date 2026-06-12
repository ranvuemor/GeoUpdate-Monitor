from __future__ import annotations

import os
import platform
import subprocess
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


class DefaultFileAssociationEarthController:
    def __init__(self):
        self._earth_automation = None

    def open_kml(self, kml_path: Path) -> None:
        path = Path(kml_path)
        system = platform.system()
        command = build_open_command(path, system=system)
        if command is None:
            os.startfile(path)  # type: ignore[attr-defined]
            return
        subprocess.run(command, check=True)

    def read_imagery_dates(self) -> ImageryDateReading:
        raise NotImplementedError("Google Earth Pro OCR automation is not implemented in this MVP.")

    def toggle_historical_imagery(self, enable: bool = True) -> None:
        """Toggle the Historical Imagery view in Google Earth Pro.
        
        Requires PyAutoGUI and the automation mode to be available.
        """
        try:
            from .earth_automation import EarthAutomation
        except ImportError as exc:
            raise RuntimeError(
                "Historical Imagery automation requires PyAutoGUI. Install with: pip install 'earth-imagery-watcher[automation]'"
            ) from exc

        if not self._earth_automation:
            self._earth_automation = EarthAutomation()
        
        self._earth_automation.toggle_historical_imagery(enable)


class NotImplementedEarthController:
    def open_kml(self, kml_path: Path) -> None:
        raise NotImplementedError("Google Earth Pro KML opening is not configured.")

    def read_imagery_dates(self) -> ImageryDateReading:
        raise NotImplementedError("Google Earth Pro OCR automation is not implemented in this MVP.")


def build_open_command(kml_path: Path, system: str | None = None) -> list[str] | None:
    operating_system = system or platform.system()
    path = str(kml_path)
    if operating_system == "Windows":
        return None
    if operating_system == "Darwin":
        return ["open", path]
    if operating_system == "Linux":
        return ["xdg-open", path]
    raise RuntimeError(f"Unsupported operating system for opening KML files: {operating_system}")
