from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None = None


class ImageryDateOcrReader:
    """Placeholder for the later OpenCV/Tesseract bottom-right date reader."""

    def read_bottom_right_date(self, screenshot_path: str) -> OcrResult:
        raise NotImplementedError("OCR screenshot reading is not implemented in this MVP.")
