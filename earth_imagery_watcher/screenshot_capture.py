from __future__ import annotations

import re
import platform
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CropBox = tuple[int, int, int, int]
EARTH_WINDOW_TITLE_PARTS = ("Google Earth Pro", "Google Earth", "Earth Pro")


@dataclass(frozen=True)
class WindowBounds:
    left: int
    top: int
    width: int
    height: int
    title: str | None = None


@dataclass(frozen=True)
class CaptureResult:
    path: Path
    crop_box: CropBox
    used_window_crop: bool
    window: WindowBounds | None = None


def bottom_right_crop_box(
    image_width: int,
    image_height: int,
    crop_width: int,
    crop_height: int,
    crop_bottom_offset: int = 0,
    window_bounds: WindowBounds | None = None,
) -> CropBox:
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image dimensions must be positive.")
    if crop_width <= 0 or crop_height <= 0:
        raise ValueError("Crop dimensions must be positive.")
    if crop_bottom_offset < 0:
        raise ValueError("Crop bottom offset cannot be negative.")

    if window_bounds:
        target_left = max(0, window_bounds.left)
        target_top = max(0, window_bounds.top)
        target_right = min(image_width, window_bounds.left + window_bounds.width)
        target_bottom = min(image_height, window_bounds.top + window_bounds.height)
    else:
        target_left = 0
        target_top = 0
        target_right = image_width
        target_bottom = image_height

    target_bottom -= crop_bottom_offset
    if target_right <= target_left or target_bottom <= target_top:
        raise ValueError("Crop bottom offset leaves no visible crop area.")

    left = max(target_left, target_right - crop_width)
    top = max(target_top, target_bottom - crop_height)
    return left, top, target_right, target_bottom


def find_google_earth_window() -> WindowBounds | None:
    if platform.system() != "Windows":
        return None

    try:
        import pygetwindow
    except ImportError:
        print("Warning: Google Earth window detection requires pygetwindow; using full-screen crop fallback.")
        return None

    windows = [
        window
        for window in pygetwindow.getAllWindows()
        if window.title and any(part.lower() in window.title.lower() for part in EARTH_WINDOW_TITLE_PARTS)
    ]
    if not windows:
        return None

    try:
        active = pygetwindow.getActiveWindow()
    except Exception:
        active = None

    if active and active.title:
        for window in windows:
            if window.title == active.title:
                return _window_to_bounds(window)

    return _window_to_bounds(windows[0])


def prepare_for_screenshot(window: WindowBounds | None, delay_seconds: float = 1.0) -> None:
    try:
        import pyautogui
    except ImportError:
        print("Warning: pyautogui is unavailable; cannot move mouse away from the screen edge.")
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        return

    if window:
        x = window.left + window.width // 2
        y = window.top + window.height // 2
    else:
        screen_width, screen_height = pyautogui.size()
        x = screen_width // 2
        y = screen_height // 2

    pyautogui.moveTo(x, y)
    if delay_seconds > 0:
        time.sleep(delay_seconds)


def capture_bottom_right_crop(
    output_dir: str | Path,
    region_name: str,
    sample_id: str,
    crop_width: int = 500,
    crop_height: int = 120,
    crop_bottom_offset: int = 0,
    window_bounds: WindowBounds | None = None,
    attempt: int | None = None,
) -> CaptureResult:
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError(
            "Screenshot capture requires Pillow. Install with: pip install 'earth-imagery-watcher[screenshot]'"
        ) from exc

    screenshot = ImageGrab.grab()
    crop_box = bottom_right_crop_box(
        screenshot.width,
        screenshot.height,
        crop_width,
        crop_height,
        crop_bottom_offset=crop_bottom_offset,
        window_bounds=window_bounds,
    )
    crop = screenshot.crop(crop_box)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / _crop_filename(region_name, sample_id, attempt=attempt)
    crop.save(output_path, format="PNG")
    return CaptureResult(
        path=output_path,
        crop_box=crop_box,
        used_window_crop=window_bounds is not None,
        window=window_bounds,
    )


def _window_to_bounds(window: object) -> WindowBounds:
    return WindowBounds(
        left=int(getattr(window, "left")),
        top=int(getattr(window, "top")),
        width=int(getattr(window, "width")),
        height=int(getattr(window, "height")),
        title=str(getattr(window, "title", "") or ""),
    )


def _crop_filename(region_name: str, sample_id: str, attempt: int | None = None) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    region = _safe_filename_part(region_name)
    sample = _safe_filename_part(sample_id)
    attempt_part = f"-attempt-{attempt}" if attempt is not None else ""
    return f"{region}_{sample}{attempt_part}_{timestamp}_date_crop.png"


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "unnamed"
