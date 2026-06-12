from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .date_parser import parse_imagery_date


@dataclass(frozen=True)
class OcrTextBlock:
    text: str
    confidence: float | None = None
    box: Any | None = None


@dataclass(frozen=True)
class OcrResult:
    raw_text: str
    text_blocks: list[OcrTextBlock]
    confidence: float | None = None
    parsed_imagery_date: date | None = None


class PaddleImageryDateOcrReader:
    def __init__(self, engine: Any | None = None):
        self._engine = engine

    def read_image(self, image_path: str | Path) -> OcrResult:
        engine = self._engine or _create_paddle_engine()
        raw_output = _run_paddle_ocr(engine, Path(image_path))
        return parse_paddleocr_output(raw_output)


def parse_paddleocr_output(raw_output: Any) -> OcrResult:
    blocks = list(_iter_text_blocks(raw_output))
    raw_text = "\n".join(block.text for block in blocks)
    confidences = [block.confidence for block in blocks if block.confidence is not None]
    confidence = sum(confidences) / len(confidences) if confidences else None
    return OcrResult(
        raw_text=raw_text,
        text_blocks=blocks,
        confidence=confidence,
        parsed_imagery_date=parse_imagery_date(raw_text),
    )


def _create_paddle_engine() -> Any:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            "OCR requires PaddleOCR. Install with: pip install 'earth-imagery-watcher[ocr]'"
        ) from exc

    try:
        return PaddleOCR(use_angle_cls=True, lang="en")
    except TypeError:
        return PaddleOCR(lang="en")


def _run_paddle_ocr(engine: Any, image_path: Path) -> Any:
    if hasattr(engine, "ocr"):
        try:
            return engine.ocr(str(image_path), cls=True)
        except TypeError:
            return engine.ocr(str(image_path))
    if hasattr(engine, "predict"):
        return engine.predict(str(image_path))
    raise RuntimeError("PaddleOCR engine does not expose an ocr() or predict() method.")


def _iter_text_blocks(value: Any) -> Iterable[OcrTextBlock]:
    if value is None:
        return

    if hasattr(value, "to_dict"):
        yield from _iter_text_blocks(value.to_dict())
        return

    if isinstance(value, dict):
        yield from _iter_dict_text_blocks(value)
        return

    if isinstance(value, (str, bytes)):
        return

    if isinstance(value, (list, tuple)):
        legacy_block = _legacy_text_block(value)
        if legacy_block:
            yield legacy_block
            return
        for item in value:
            yield from _iter_text_blocks(item)


def _iter_dict_text_blocks(value: dict[str, Any]) -> Iterable[OcrTextBlock]:
    rec_texts = value.get("rec_texts")
    if isinstance(rec_texts, list):
        rec_scores = value.get("rec_scores") or []
        rec_boxes = value.get("rec_boxes") or value.get("dt_polys") or []
        for index, text in enumerate(rec_texts):
            if not text:
                continue
            confidence = _float_or_none(_get_index(rec_scores, index))
            box = _get_index(rec_boxes, index)
            yield OcrTextBlock(text=str(text), confidence=confidence, box=box)
        return

    text = value.get("text") or value.get("transcription")
    if text:
        confidence = _float_or_none(value.get("confidence") or value.get("score"))
        yield OcrTextBlock(text=str(text), confidence=confidence, box=value.get("box"))
        return

    for item in value.values():
        yield from _iter_text_blocks(item)


def _legacy_text_block(value: list[Any] | tuple[Any, ...]) -> OcrTextBlock | None:
    if len(value) < 2:
        return None

    maybe_text_score = value[1]
    if (
        isinstance(maybe_text_score, (list, tuple))
        and len(maybe_text_score) >= 2
        and isinstance(maybe_text_score[0], str)
    ):
        return OcrTextBlock(
            text=maybe_text_score[0],
            confidence=_float_or_none(maybe_text_score[1]),
            box=value[0],
        )

    return None


def _get_index(values: Any, index: int) -> Any | None:
    if isinstance(values, (list, tuple)) and index < len(values):
        return values[index]
    return None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
