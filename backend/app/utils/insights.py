from __future__ import annotations

import json
import re
from typing import Iterable, List

from app.ai.processor import PageText

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\d{3}[-.\s)]\s*\d{3}")
_NAME_HEADING = re.compile(r"^[A-Z][A-Z\s.'-]{4,60}$")


def extractive_summary(pages: Iterable[PageText], limit: int = 280) -> str:
    pages = list(pages)
    headings = _headings(pages)
    useful = [item for item in headings if not _is_name_or_contact(item)]
    if useful:
        return " · ".join(useful[:8])

    for page in pages:
        for paragraph in re.split(r"\n+", page.text or ""):
            compact = re.sub(r"\s+", " ", paragraph).strip()
            if _is_contact_line(compact) or len(compact) < 40:
                continue
            if len(compact) <= limit:
                return compact
            return compact[:limit].rsplit(" ", 1)[0] + "…"
    return ""


def suggested_questions(pages: Iterable[PageText]) -> List[str]:
    pages = list(pages)
    blob = " ".join(page.text for page in pages)
    lower = blob.lower()
    headings = [item for item in _headings(pages) if not _is_name_or_contact(item)]
    questions: List[str] = []

    if _looks_like_resume(lower, headings):
        catalog = [
            ("experience", "What experience is listed?"),
            ("skill", "What skills are listed?"),
            ("educat", "What education is listed?"),
            ("project", "What projects are described?"),
            ("intern", "What internships or roles are mentioned?"),
            ("certif", "What certifications are listed?"),
        ]
        for needle, question in catalog:
            if needle in lower:
                questions.append(question)
        if not questions:
            questions = [
                "What experience is listed?",
                "What skills are listed?",
                "What education is listed?",
            ]
        return _unique(questions, 6)

    for heading in headings[:6]:
        questions.append(f"What does this document say about {heading}?")

    topical = [
        ("vacation", "What is the vacation policy?"),
        ("sick", "How many sick days are available?"),
        ("remote", "What is the remote work policy?"),
        ("deadline", "What deadlines are mentioned?"),
        ("eligib", "What are the eligibility requirements?"),
        ("tuition", "What does this say about tuition or financial aid?"),
        ("salary", "What compensation is mentioned?"),
        ("requirement", "What requirements are listed?"),
    ]
    for needle, question in topical:
        if needle in lower:
            questions.append(question)

    return _unique(questions, 6)


def dump_questions(questions: List[str]) -> str:
    return json.dumps(questions)


def _headings(pages: Iterable[PageText]) -> List[str]:
    found: List[str] = []
    for page in pages:
        if page.heading:
            found.append(page.heading.strip())
        for block in page.blocks or []:
            if block.kind == "heading" and block.text:
                found.append(block.text.strip())
    return _unique(found, 16)


def _looks_like_resume(lower: str, headings: List[str]) -> bool:
    heading_blob = " ".join(headings).lower()
    resume_heads = any(word in heading_blob for word in ("experience", "education", "skills", "projects"))
    contact = bool(_EMAIL.search(lower)) and bool(_PHONE.search(lower))
    return resume_heads or "linkedin" in lower or ("resume" in lower and contact) or contact and "experience" in lower


def _is_contact_line(text: str) -> bool:
    if not text:
        return True
    if _EMAIL.search(text) or "linkedin." in text.lower() or "github.com" in text.lower():
        return True
    return bool(_PHONE.search(text)) and len(text) < 180


def _is_name_or_contact(text: str) -> bool:
    value = (text or "").strip()
    if not value or _is_contact_line(value):
        return True
    if _NAME_HEADING.match(value) and len(value.split()) <= 5:
        return True
    return False


def _unique(values: List[str], limit: int) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        key = re.sub(r"\s+", " ", value).strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        out.append(key)
        if len(out) >= limit:
            break
    return out
