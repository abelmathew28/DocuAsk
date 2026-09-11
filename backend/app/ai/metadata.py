from __future__ import annotations

import json
import re
from typing import Iterable, List

from app.ai.types import PageText

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_MONEY = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*\s?(?:USD|dollars)\b", re.I)
_DATE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b",
    re.I,
)
_DEADLINE = re.compile(r"\b(deadline|due by|due on|no later than|must be submitted by|submit by)\b.{0,80}", re.I)


def extract_intelligence(pages: Iterable[PageText], filename: str = "") -> dict:
    pages = list(pages)
    blob = "\n".join(page.text for page in pages)
    headings = []
    for page in pages:
        if page.heading:
            headings.append(page.heading)
        for block in page.blocks:
            if block.kind == "heading" and block.text not in headings:
                headings.append(block.text[:180])
    emails = _unique(_EMAIL.findall(blob), 12)
    phones = _unique(_PHONE.findall(blob), 8)
    dates = _unique(_DATE.findall(blob), 16)
    money = _unique(_MONEY.findall(blob), 12)
    deadlines = _unique([match.group(0).strip() for match in _DEADLINE.finditer(blob)], 10)
    requirements = _unique(_requirement_lines(blob), 12)
    contacts = emails[:6] + phones[:4]
    title = headings[0] if headings else (filename.rsplit(".", 1)[0] if filename else None)
    return {
        "title": title,
        "sections": headings[:24],
        "topics": headings[:12],
        "dates": dates,
        "deadlines": deadlines,
        "amounts": money,
        "contacts": contacts,
        "people": [],
        "organizations": [],
        "locations": [],
        "requirements": requirements,
        "action_items": deadlines[:6],
        "key_terms": headings[:8],
    }


def dump_intelligence(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _requirement_lines(blob: str) -> List[str]:
    found: List[str] = []
    for line in blob.splitlines():
        compact = line.strip()
        if len(compact) < 12 or len(compact) > 220:
            continue
        if re.search(r"\b(must|required|shall|need to|at least)\b", compact, re.I):
            found.append(compact)
    return found


def _unique(values: List[str], limit: int) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        key = value.strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        out.append(key)
        if len(out) >= limit:
            break
    return out
