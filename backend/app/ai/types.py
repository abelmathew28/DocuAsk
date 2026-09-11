from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TextBlock:
    text: str
    kind: str = "paragraph"  # heading, paragraph, list, table
    heading: Optional[str] = None
    bbox: Optional[List[float]] = None


@dataclass
class PageText:
    page_number: int
    text: str
    heading: Optional[str] = None
    blocks: List[TextBlock] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    used_ocr: bool = False


@dataclass
class TextChunk:
    page_number: int
    chunk_index: int
    text: str
    heading: Optional[str] = None
    section: Optional[str] = None
    chunk_type: str = "text"
    bbox: Optional[str] = None


@dataclass
class RetrievedChunk:
    id: str
    document_id: str
    document_name: str
    page_number: int
    text: str
    score: float
    heading: Optional[str] = None
    chunk_type: str = "text"
    bbox: Optional[str] = None
    chunk_index: int = 0

