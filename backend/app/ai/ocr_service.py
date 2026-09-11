from __future__ import annotations

from typing import List

from app.ai.types import PageText
from app.core.logging import get_logger

logger = get_logger("ai.ocr")


def ocr_page_image(image_bytes: bytes) -> str:
    """OCR a rendered page. Uses RapidOCR when installed; otherwise empty."""
    if not image_bytes:
        return ""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return ""
    try:
        engine = RapidOCR()
        result, _ = engine(image_bytes)
        if not result:
            return ""
        lines = [item[1] for item in result if len(item) > 1 and item[1]]
        return "\n".join(lines).strip()
    except Exception as exc:
        logger.warning("ocr_failed", error=str(exc))
        return ""


def page_needs_ocr(text: str, min_chars: int = 40) -> bool:
    compact = "".join(ch for ch in (text or "") if ch.isalnum())
    return len(compact) < min_chars
