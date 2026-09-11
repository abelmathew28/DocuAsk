from __future__ import annotations

import re
from io import BytesIO
from typing import List, Optional

from app.ai.ocr_service import ocr_page_image, page_needs_ocr
from app.ai.types import PageText, TextBlock
from app.core.exceptions import ValidationAppError
from app.core.logging import get_logger

logger = get_logger("ai.pdf")

_HEADING_RE = re.compile(r"^(\d+(\.\d+){0,3}|[A-Z][A-Z0-9 /&-]{8,}|[A-Z][a-z].{0,80})$")


def extract_pdf_pages(data: bytes) -> List[PageText]:
    pages = _extract_pymupdf(data)
    if pages is None:
        pages = _extract_pypdf(data)
    if not pages:
        raise ValidationAppError("This PDF could not be read. It may be damaged.")
    if not any(page.text.strip() for page in pages):
        raise ValidationAppError(
            "No readable text was found in this PDF. If it is a scanned file, enable OCR (RapidOCR) and retry."
        )
    return pages


def _extract_pymupdf(data: bytes) -> Optional[List[PageText]]:
    try:
        import fitz
    except ImportError:
        return None
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception:
        return None
    if document.is_encrypted:
        try:
            if not document.authenticate(""):
                raise ValidationAppError("This PDF is password-protected and cannot be processed.")
        except ValidationAppError:
            raise
        except Exception as exc:
            raise ValidationAppError("This PDF is password-protected and cannot be processed.") from exc

    pages: List[PageText] = []
    for index, page in enumerate(document, start=1):
        pages.append(_page_from_pymupdf(page, index))
    document.close()
    return pages


def _page_from_pymupdf(page, page_number: int) -> PageText:
    text = (page.get_text("text") or "").strip()
    used_ocr = False
    if page_needs_ocr(text):
        try:
            pixmap = page.get_pixmap(matrix=__import__("fitz").Matrix(2, 2), alpha=False)
            ocr_text = ocr_page_image(pixmap.tobytes("png"))
            if ocr_text:
                text = ocr_text
                used_ocr = True
        except Exception as exc:
            logger.warning("ocr_page_skipped", page=page_number, error=str(exc))

    blocks: List[TextBlock] = []
    heading = None
    try:
        dict_page = page.get_text("dict")
        sizes = []
        for block in dict_page.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if not line_text:
                    continue
                size = max((span.get("size", 0) for span in line.get("spans", [])), default=0)
                sizes.append(size)
        median = sorted(sizes)[len(sizes) // 2] if sizes else 11
        for block in dict_page.get("blocks", []):
            if block.get("type") != 0:
                continue
            parts = []
            size = 0
            bbox = block.get("bbox")
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if line_text:
                    parts.append(line_text)
                    size = max(size, max((span.get("size", 0) for span in line.get("spans", [])), default=0))
            block_text = " ".join(parts).strip()
            if not block_text:
                continue
            kind = "paragraph"
            if size >= median * 1.18 or _looks_like_heading(block_text):
                kind = "heading"
                if heading is None:
                    heading = block_text[:180]
            elif re.match(r"^\s*([•\-\*]|\d+[\.)])\s+", block_text):
                kind = "list"
            blocks.append(TextBlock(text=block_text, kind=kind, heading=heading, bbox=list(bbox) if bbox else None))
    except Exception:
        blocks = [TextBlock(text=line.strip(), kind="paragraph") for line in text.split("\n") if line.strip()]

    tables: List[str] = []
    try:
        finder = page.find_tables()
        for table in finder.tables:
            rows = table.extract()
            rendered = _render_table(rows)
            if rendered:
                tables.append(rendered)
                blocks.append(TextBlock(text=rendered, kind="table", heading=heading))
    except Exception:
        pass

    cleaned = _clean_text(text)
    if not cleaned and tables:
        cleaned = "\n\n".join(tables)
    return PageText(
        page_number=page_number,
        text=cleaned,
        heading=heading,
        blocks=blocks or [TextBlock(text=cleaned, kind="paragraph")] if cleaned else [],
        tables=tables,
        used_ocr=used_ocr,
    )


def _extract_pypdf(data: bytes) -> List[PageText]:
    from pypdf import PdfReader
    from pypdf.errors import FileNotDecryptedError, PdfReadError

    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError as exc:
        raise ValidationAppError("This PDF could not be read. It may be damaged.") from exc
    if reader.is_encrypted:
        try:
            if reader.decrypt("") == 0:
                raise ValidationAppError("This PDF is password-protected and cannot be processed.")
        except (FileNotDecryptedError, NotImplementedError) as exc:
            raise ValidationAppError("This PDF is password-protected and cannot be processed.") from exc

    pages: List[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        cleaned = _clean_text(raw)
        pages.append(
            PageText(
                page_number=index,
                text=cleaned,
                blocks=[TextBlock(text=cleaned, kind="paragraph")] if cleaned else [],
            )
        )
    return pages


def _render_table(rows: List[List]) -> str:
    cleaned_rows = []
    for row in rows or []:
        cells = [re.sub(r"\s+", " ", str(cell or "")).strip() for cell in row]
        if any(cells):
            cleaned_rows.append(" | ".join(cells))
    return "\n".join(cleaned_rows)


def _looks_like_heading(text: str) -> bool:
    value = text.strip()
    if len(value) > 90 or len(value) < 3:
        return False
    if value.endswith("."):
        return False
    return bool(_HEADING_RE.match(value)) or value.isupper()


def _clean_text(value: str) -> str:
    value = (value or "").replace("\x00", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()
