from __future__ import annotations

import json
import re
from typing import Iterable, List, Optional

from app.ai.types import PageText, TextBlock, TextChunk
from app.core.config import settings


def chunk_pages(
    pages: Iterable[PageText],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> List[TextChunk]:
    size = chunk_size or settings.CHUNK_SIZE
    overlap_size = overlap if overlap is not None else settings.CHUNK_OVERLAP
    if overlap_size >= size:
        overlap_size = max(size // 5, 0)

    chunks: List[TextChunk] = []
    index = 0
    for page in pages:
        page_chunks = _chunk_page(page, size, overlap_size)
        for chunk in page_chunks:
            chunk.chunk_index = index
            chunks.append(chunk)
            index += 1
    return chunks


def _chunk_page(page: PageText, size: int, overlap: int) -> List[TextChunk]:
    blocks = page.blocks or [TextBlock(text=page.text, kind="paragraph", heading=page.heading)]
    grouped: List[tuple[str, str, Optional[str], Optional[str]]] = []
    current_type = "text"
    current_heading = page.heading
    current_section = page.heading
    buffer: List[str] = []
    bbox = None

    def flush() -> None:
        nonlocal buffer, current_type, bbox
        text = "\n\n".join(part for part in buffer if part.strip()).strip()
        if text and not (current_type == "heading" and len(text) < 48):
            grouped.append((text, current_type, current_heading, _bbox_json(bbox)))
        buffer = []
        bbox = None

    for block in blocks:
        if not (block.text or "").strip():
            continue
        if block.kind == "heading":
            # Keep short headings with the following body instead of storing them alone.
            if buffer and current_type == "heading" and sum(len(part) for part in buffer) < 120:
                buffer.append(block.text)
                current_heading = block.text[:180]
                current_section = current_heading
                bbox = bbox or block.bbox
                continue
            flush()
            current_heading = block.text[:180]
            current_section = current_heading
            current_type = "heading"
            buffer = [block.text]
            bbox = block.bbox
            continue
        if block.kind == "table":
            if buffer and current_type == "heading":
                grouped.append(
                    (
                        "\n\n".join([*buffer, block.text.strip()]).strip(),
                        "table",
                        current_heading,
                        _bbox_json(block.bbox),
                    )
                )
                buffer = []
                bbox = None
                current_type = "text"
                continue
            flush()
            grouped.append((block.text.strip(), "table", current_heading, _bbox_json(block.bbox)))
            continue
        if block.kind == "list":
            if current_type == "heading":
                current_type = "list"
            elif current_type not in {"list", "text"} or (buffer and current_type == "table"):
                flush()
            current_type = "list"
            buffer.append(block.text)
            bbox = bbox or block.bbox
            continue
        if current_type == "heading":
            current_type = "text"
        if sum(len(part) for part in buffer) + len(block.text) > size and buffer:
            flush()
            current_type = "text"
        current_type = "text"
        buffer.append(block.text)
        bbox = bbox or block.bbox
    flush()

    chunks: List[TextChunk] = []
    for text, chunk_type, heading, box in grouped:
        if len(text) <= size or chunk_type == "table":
            chunks.append(
                TextChunk(
                    page_number=page.page_number,
                    chunk_index=0,
                    text=text,
                    heading=heading,
                    section=heading or current_section,
                    chunk_type=chunk_type,
                    bbox=box,
                )
            )
            continue
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                breakpoint = max(text.rfind("\n\n", start, end), text.rfind(". ", start, end), text.rfind(" ", start, end))
                if breakpoint > start + size // 3:
                    end = breakpoint + (1 if text[breakpoint] == "." else 0)
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    TextChunk(
                        page_number=page.page_number,
                        chunk_index=0,
                        text=piece,
                        heading=heading,
                        section=heading or current_section,
                        chunk_type=chunk_type,
                        bbox=box,
                    )
                )
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    if chunks:
        return chunks
    text = (page.text or "").strip()
    if not text:
        return []
    return [
        TextChunk(
            page_number=page.page_number,
            chunk_index=0,
            text=text[:size],
            heading=page.heading,
            section=page.heading,
            chunk_type="text",
        )
    ]


def _bbox_json(bbox: Optional[list]) -> Optional[str]:
    if not bbox:
        return None
    try:
        return json.dumps([float(value) for value in bbox[:4]])
    except (TypeError, ValueError):
        return None
