from __future__ import annotations

import re
from typing import List, Literal, Optional, Sequence, Tuple

from app.ai.hybrid_search import tokenize
from app.ai.prompts import is_insufficient_answer
from app.ai.types import RetrievedChunk

SupportStatus = Literal["supported", "partially_supported", "not_found"]


def compute_support_status(answer: str, sources: Sequence[object] | None = None) -> SupportStatus:
    if is_insufficient_answer(answer) or not answer:
        return "not_found"
    count = len(sources or [])
    if count == 0:
        return "partially_supported"
    return "supported"

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
_WHEN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4}\s*[-–—]\s*"
    r"(?:Present|Current|Now|\w+\.?\s+\d{4}|\d{4})",
    re.I,
)
_FIELD = re.compile(r"^(Company|Skills|Email|Employer|Location)\s*:", re.I)
_COVER = ("dear hiring", "dear sir", "to whom it may concern", "i am writing", "i am excited to apply")
_SECTION_LABELS = {"professional experience", "education", "projects", "skills", "references"}


def verify_answer(
    answer: str,
    chunks: Sequence[RetrievedChunk],
    fallback: str,
) -> Tuple[str, List[RetrievedChunk]]:
    if not answer or is_insufficient_answer(answer):
        return fallback, []
    if not chunks:
        return fallback, []

    supported: List[RetrievedChunk] = []
    for chunk in chunks:
        if _supports(answer, chunk.text):
            supported.append(chunk)
    if not supported:
        return fallback, []
    return answer.strip(), list(supported)


def rank_citation_chunks(answer: str, chunks: Sequence[RetrievedChunk], limit: int = 6) -> List[RetrievedChunk]:
    """Pick citations that contain the answer's job titles, dates, or emails."""
    titles, details = _answer_anchors(answer)
    scored: List[tuple[float, RetrievedChunk]] = []
    for chunk in chunks:
        score = _citation_score(titles, details, chunk)
        if score < 5.0:
            continue
        blob = f"{chunk.heading or ''}\n{chunk.text or ''}".lower()
        if titles and not any(_anchor_in_text(title, blob) for title in titles):
            continue
        scored.append((score, chunk))
    if not scored:
        return []
    scored.sort(key=lambda item: (-item[0], item[1].page_number, getattr(item[1], "chunk_index", 0)))

    picked: List[RetrievedChunk] = []
    seen_ids = set()
    seen_titles = set()
    for _, chunk in scored:
        if chunk.id in seen_ids:
            continue
        blob = f"{chunk.heading or ''}\n{chunk.text or ''}".lower()
        matched_title = next((title for title in titles if _anchor_in_text(title, blob)), None)
        if matched_title:
            title_key = matched_title.lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
        seen_ids.add(chunk.id)
        picked.append(chunk)
        if len(picked) >= limit:
            break
    return picked


def citation_excerpt(answer: str, chunk: RetrievedChunk, limit: int = 280) -> str:
    """Return the passage from the chunk that best matches the answer."""
    text = (chunk.text or "").strip()
    heading = (chunk.heading or "").strip()
    blob = f"{heading}\n{text}" if heading and heading not in text[: max(len(heading), 1) + 8] else text
    blob = re.sub(r"\s+", " ", blob).strip()
    if not blob:
        return ""

    titles, details = _answer_anchors(answer)
    anchors = [*titles, *details]
    best = ""
    best_len = 0
    lowered = blob.lower()
    for anchor in anchors:
        idx = _anchor_index(anchor, lowered)
        if idx < 0:
            continue
        start = max(0, idx - 30)
        end = min(len(blob), idx + len(anchor) + 140)
        snippet = blob[start:end].strip(" -|")
        if len(snippet) > best_len:
            best = snippet
            best_len = len(snippet)

    for email in _EMAIL.findall(answer):
        idx = lowered.find(email.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(blob), idx + len(email) + 80)
            snippet = blob[start:end].strip()
            if len(snippet) > best_len:
                best = snippet
                best_len = len(snippet)

    if best:
        return _trim(best, limit)
    if _is_header_only(blob):
        return _trim(heading or blob, limit)
    return _trim(blob, limit)


def _answer_anchors(answer: str) -> tuple[List[str], List[str]]:
    titles: List[str] = []
    details: List[str] = []
    for match in _BOLD.finditer(answer):
        title = match.group(1).strip()
        if title.lower() not in _SECTION_LABELS:
            titles.append(title)
    for line in answer.splitlines():
        clean = line.strip().lstrip("-").strip()
        if not clean or clean.startswith("**"):
            continue
        if _FIELD.match(clean) or _WHEN.search(clean) or _EMAIL.search(clean):
            details.append(clean)
    return _dedupe_anchors(titles), _dedupe_anchors(details)


def _dedupe_anchors(anchors: List[str]) -> List[str]:
    deduped: List[str] = []
    seen = set()
    for anchor in anchors:
        key = anchor.lower()
        if key in seen or len(anchor) < 4:
            continue
        seen.add(key)
        deduped.append(anchor)
    return deduped


def _citation_score(titles: Sequence[str], details: Sequence[str], chunk: RetrievedChunk) -> float:
    text = f"{chunk.heading or ''}\n{chunk.text or ''}"
    compact = re.sub(r"\s+", " ", text).strip()
    lowered = compact.lower()
    if any(marker in lowered[:220] for marker in _COVER):
        return -10.0
    if _is_header_only(compact):
        return -4.0

    title_hit = any(_anchor_in_text(title, lowered) for title in titles)
    detail_hits = sum(1 for detail in details if _anchor_in_text(detail, lowered))
    if not title_hit and detail_hits < 2:
        return 0.0

    score = chunk.score * 0.15
    if title_hit:
        score += 16.0
    score += detail_hits * 4.0
    for email in _EMAIL.findall(" ".join(details)):
        if email.lower() in lowered:
            score += 18.0
    if _WHEN.search(compact):
        score += 2.0
    return score


def _anchor_in_text(anchor: str, lowered: str) -> bool:
    return _anchor_index(anchor, lowered) >= 0


def _anchor_index(anchor: str, lowered: str) -> int:
    anchor_l = anchor.lower()
    if len(anchor_l) < 4:
        return -1
    idx = lowered.find(anchor_l)
    if idx >= 0:
        return idx
    if len(anchor_l) > 12:
        return lowered.find(anchor_l[:28])
    return -1


def _supports(answer: str, evidence: str) -> bool:
    compact_answer = re.sub(r"\s+", " ", answer.lower())
    compact_evidence = re.sub(r"\s+", " ", evidence.lower()).strip(" .")
    if len(compact_evidence) >= 32 and compact_evidence[:120] in compact_answer:
        return True
    answer_tokens = set(tokenize(answer))
    evidence_tokens = set(tokenize(evidence))
    if not answer_tokens or not evidence_tokens:
        return False
    shared = len(answer_tokens & evidence_tokens)
    overlap = shared / max(len(answer_tokens), 1)
    if overlap >= 0.12:
        return True
    if shared / max(len(evidence_tokens), 1) >= 0.18:
        return True
    for sentence in _SENTENCE.split(answer.strip()):
        phrase = re.sub(r"\s+", " ", sentence.lower()).strip(" .")
        if len(phrase) > 24 and phrase in compact_evidence:
            return True
        numbers = re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", sentence)
        dates = re.findall(
            r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
            sentence.lower(),
        )
        if any(num in compact_evidence for num in numbers if len(num) > 1) and overlap >= 0.06:
            return True
        if any(date in compact_evidence for date in dates):
            return True
    return overlap >= 0.08


def _is_header_only(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact or len(compact) > 64:
        return False
    letters = re.sub(r"[^A-Za-z]", "", compact)
    return bool(letters) and letters.isupper() and len(compact.split()) <= 6


def _trim(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rsplit(" ", 1)[0] + "…"
