from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


CropBox = tuple[int, int, int, int]


def bottom_right_crop_box(
    image_width: int,
    image_height: int,
    crop_width: int,
    crop_height: int,
) -> CropBox:
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image dimensions must be positive.")
    if crop_width <= 0 or crop_height <= 0:
        raise ValueError("Crop dimensions must be positive.")

    right = image_width
    lower = image_height
    left = max(0, image_width - crop_width)
    upper = max(0, image_height - crop_height)
    return left, upper, right, lower


def capture_bottom_right_crop(
    output_dir: str | Path,
    region_name: str,
    sample_id: str,
    crop_width: int = 500,
    crop_height: int = 120,
) -> Path:
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError(
            "Screenshot capture requires Pillow. Install with: pip install 'earth-imagery-watcher[screenshot]'"
        ) from exc

    screenshot = ImageGrab.grab()
    crop_box = bottom_right_crop_box(screenshot.width, screenshot.height, crop_width, crop_height)
    crop = screenshot.crop(crop_box)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / _crop_filename(region_name, sample_id)
    crop.save(output_path, format="PNG")
    return output_path


def _crop_filename(region_name: str, sample_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    region = _safe_filename_part(region_name)
    sample = _safe_filename_part(sample_id)
    return f"{region}_{sample}_{timestamp}_date_crop.png"


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "unnamed"
