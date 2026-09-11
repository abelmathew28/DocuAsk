from __future__ import annotations

import re
from typing import Iterable, List, Optional

from app.ai.query_service import expanded_terms, term_overlap
from app.ai.types import RetrievedChunk

_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
_WHEN = re.compile(
    rf"{_MONTH}\.?\s+\d{{4}}\s*[-–—to]+\s*(?:Present|Current|Now|{_MONTH}\.?\s+\d{{4}}|\d{{4}})",
    re.I,
)
_KV = re.compile(r"^[A-Za-z][A-Za-z0-9/&-]*(?: [A-Za-z][A-Za-z0-9/&-]*)?:\s+\S")
_COVER = ("dear hiring", "dear sir", "to whom it may concern", "i am writing", "i am excited to apply")
_KV_IN_TITLE = re.compile(r"\b([A-Z][A-Za-z]{1,24}):\s+(\S.+)$")
_FIELD_LABEL = re.compile(
    r"^(Company|Skills|Location|Tech Stack|Department|School|Organization|Employer)\s*:",
    re.I,
)


def format_list_answer(question: str, chunks: Iterable[RetrievedChunk], fallback: str) -> str:
    """Turn retrieved chunks into a scannable markdown list, grouped by section."""
    items_by_section = _collect_items(list(chunks))
    if not items_by_section:
        return fallback
    terms = expanded_terms(question)
    chosen = _pick_sections(items_by_section, terms)
    if not chosen:
        return fallback

    lines: List[str] = []
    for section, items in chosen:
        if section:
            label = section.title() if section.isupper() else section
            lines.append(f"**{label}**")
            lines.append("")
        for item in _sort_items_by_date(items):
            title = item["title"]
            when = item["when"]
            fields = _display_fields(item["kv"])
            block = [f"- **{title}**"]
            if when:
                block.append(f"  {when}")
            block.extend(f"  {field}" for field in fields)
            lines.append("\n".join(block))
            lines.append("")
    return "\n".join(lines).strip()


def _display_fields(kv: List[str]) -> List[str]:
    """Keep only labeled document fields (company, skills, etc.), not narrative text."""
    merged: dict[str, str] = {}
    order: List[str] = []
    for raw in kv:
        for piece in _split_kv_line(raw):
            piece = _compact(piece)
            if not piece or not _FIELD_LABEL.match(piece):
                continue
            label, _, value = piece.partition(":")
            key = label.strip().lower()
            value = value.strip()
            if not value or len(value) < 2:
                continue
            if key not in merged or len(value) > len(merged[key]):
                if key not in merged:
                    order.append(key)
                merged[key] = value
    preferred = ("company", "employer", "skills", "location", "tech stack", "department", "school", "organization")
    keys = [key for key in preferred if key in merged] + [key for key in order if key not in preferred]
    return [f"{key.title()}: {merged[key]}" for key in keys]


def _split_kv_line(raw: str) -> List[str]:
    parts: List[str] = []
    current: List[str] = []
    for segment in re.split(r"\s*\|\s*", _compact(raw)):
        if _FIELD_LABEL.match(segment):
            if current:
                parts.append(_compact(" | ".join(current)))
            current = [segment]
        elif current:
            current.append(segment)
        else:
            parts.append(segment)
    if current:
        parts.append(_compact(" | ".join(current)))
    return parts


def _sort_items_by_date(items: List[dict]) -> List[dict]:
    """Newest roles first when dates are available (resume-style order)."""
    if len(items) < 2 or sum(1 for item in items if item.get("when")) < 2:
        return items
    return sorted(items, key=_item_sort_key, reverse=True)


def _item_sort_key(item: dict) -> tuple[int, int, int, int]:
    start_year, start_month, end_year, end_month = _parse_when(item.get("when") or "")
    return (start_year, start_month, end_year, end_month)


def _parse_when(when: str) -> tuple[int, int, int, int]:
    compact = _compact(when)
    if not compact:
        return (0, 0, 0, 0)
    parts = re.split(r"\s*[-–—]\s*|\s+to\s+", compact, maxsplit=1)
    start = _parse_date_part(parts[0])
    end = _parse_date_part(parts[1]) if len(parts) > 1 else start
    return (*start, *end)


def _parse_date_part(text: str) -> tuple[int, int]:
    lowered = text.strip().lower()
    if lowered in {"present", "current", "now"}:
        return (9999, 12)
    month_match = re.search(_MONTH, text, re.I)
    year_match = re.search(r"\b(\d{4})\b", text)
    month = _month_number(month_match.group(0)) if month_match else 1
    year = int(year_match.group(1)) if year_match else 0
    return (year, month)


def _month_number(token: str) -> int:
    key = token.strip().lower().rstrip(".")
    lookup = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
        "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
    }
    return lookup.get(key, 1)


def _pick_sections(items_by_section: List[tuple[str, List[dict]]], terms: set[str]) -> List[tuple[str, List[dict]]]:
    if not terms:
        return items_by_section

    matching_pages = {
        item["page"]
        for section, items in items_by_section
        if section and term_overlap(terms, section) >= 1
        for item in items
    }
    if not matching_pages:
        matching_pages = {
            chunk_page
            for section, items in items_by_section
            if term_overlap(terms, section) >= 1
            for chunk_page in {item["page"] for item in items}
        }

    chosen: List[tuple[str, List[dict]]] = []
    for section, items in items_by_section:
        hay = f"{section} " + " ".join(item["title"] for item in items)
        keep = items
        if matching_pages:
            keep = [item for item in items if item["page"] in matching_pages]
        if term_overlap(terms, hay) >= 1:
            chosen.append((section, keep or items))
            continue
        dated = [item for item in keep if item["when"]]
        if dated and matching_pages:
            # Two-column pages often park later roles after unrelated headers.
            chosen.append((section, dated))
    if chosen:
        chosen = _merge_dated_into_matching_section(chosen, terms)
    if chosen:
        return chosen

    leftover = []
    for section, items in items_by_section:
        kept = [
            item
            for item in items
            if item["when"] or term_overlap(terms, f"{item['title']} {item['summary']}") >= 1
        ]
        if kept:
            leftover.append((section, kept))
    return leftover


def _merge_dated_into_matching_section(
    chosen: List[tuple[str, List[dict]]],
    terms: set[str],
) -> List[tuple[str, List[dict]]]:
    """Keep one scannable list when dated items leaked into later page headers."""
    matching = [(section, items) for section, items in chosen if term_overlap(terms, section) >= 1]
    if not matching:
        return chosen
    extras = []
    seen = {item["title"].lower() for _, items in matching for item in items}
    for section, items in chosen:
        if term_overlap(terms, section) >= 1:
            continue
        for item in items:
            key = item["title"].lower()
            if item["when"] and key not in seen:
                extras.append(item)
                seen.add(key)
    if not extras:
        return matching
    primary_section, primary_items = matching[0]
    return [(primary_section, primary_items + extras)]


def _collect_items(chunks: List[RetrievedChunk]) -> List[tuple[str, List[dict]]]:
    ordered = sorted(chunks, key=lambda chunk: (chunk.page_number, getattr(chunk, "chunk_index", 0)))
    section = ""
    groups: List[tuple[str, List[dict]]] = []
    titles: List[dict] = []
    pending: List[dict] = []
    seen = set()

    def flush_section() -> None:
        nonlocal titles
        _assign_pending(titles, pending)
        pending.clear()
        if titles:
            groups.append((section, titles))
        titles = []

    for chunk in ordered:
        heading = _compact(chunk.heading or "")
        body = (chunk.text or "").strip()
        if heading and heading in body:
            body = body.replace(heading, "", 1).strip()
        blob = f"{heading} {body}".lower()
        if any(marker in blob[:180] for marker in _COVER):
            continue

        lead = _section_name(heading) or _section_name(_first_line(body))
        if lead:
            flush_section()
            section = lead
            if heading == lead:
                heading = ""
            elif heading.startswith(lead):
                heading = _compact(heading[len(lead) :].lstrip(" -|"))
            if _compact(_first_line(body)) == lead:
                body = "\n".join(body.splitlines()[1:]).strip()
            if not heading and not body:
                continue

        dated_source = heading if _is_dated_title(heading) else (_first_line(body) if _is_dated_title(_first_line(body)) else "")
        if dated_source:
            leftover = _body_without_title(body, dated_source)
            item = _item_from(dated_source, leftover, chunk.page_number)
            if item:
                _, peeled = _peel_kv(_compact(body))
                for extra in peeled:
                    _merge_kv(item["kv"], extra)
                item["source"] = _compact(heading or dated_source)
                key = item["title"].lower()
                if key in seen:
                    extra = leftover or (body if not _same_opening(body, dated_source) else "")
                    if extra and titles and titles[-1]["title"].lower() == key:
                        _apply_details(
                            titles[-1],
                            {
                                "title": "",
                                "kv": item["kv"],
                                "summary": _first_sentence(_compact(extra), 200),
                                "page": chunk.page_number,
                            },
                        )
                    continue
                seen.add(key)
                titles.append(item)
            continue

        details = _details_from_chunk(heading, body, chunk.page_number)
        if not details or not _is_useful_details(details):
            continue
        if titles:
            if pending:
                continue
            if _same_record(titles[-1], heading, details):
                _apply_details(titles[-1], details)
            continue
        _buffer_details(pending, details, heading)

    flush_section()
    cleaned: List[tuple[str, List[dict]]] = []
    for name, items in groups:
        dated = [item for item in items if item["when"]]
        keep = dated if len(dated) >= 2 else items
        if keep:
            cleaned.append((name, keep[:12]))
    return cleaned


def _body_without_title(body: str, title: str) -> str:
    compact_title = _compact(title)
    lines = [(chunk_line, _compact(chunk_line)) for chunk_line in (body or "").splitlines() if chunk_line.strip()]
    if not lines:
        return ""
    first = lines[0][1]
    if first == compact_title or _same_opening(first, compact_title):
        return "\n".join(line for line, _ in lines[1:]).strip()
    if compact_title and compact_title in _compact(body):
        return _compact(body).replace(compact_title, "", 1).strip(" |-")
    return (body or "").strip()


def _same_opening(left: str, right: str) -> bool:
    a = _compact(left).split()
    b = _compact(right).split()
    return bool(a and b) and a[:3] == b[:3]


def _same_record(item: dict, heading: str, details: dict) -> bool:
    if details.get("page") != item.get("page"):
        return False
    source = item.get("source") or item.get("title") or ""
    head = _compact(heading)
    return bool(head) and _same_opening(head, source)


def _assign_pending(items: List[dict], pending: List[dict]) -> None:
    if not pending:
        return
    if not items:
        pending.clear()
        return
    for index, item in enumerate(items):
        if index < len(pending):
            _apply_details(item, pending[index])
    pending.clear()


def _buffer_details(pending: List[dict], details: dict, heading: str) -> None:
    heading_key = _compact(heading).lower()
    details["heading_key"] = heading_key or details.get("heading_key", "")
    if not pending:
        pending.append(details)
        return
    last = pending[-1]
    last_key = last.get("heading_key") or ""
    is_kv = _is_kv_heading(heading)
    if is_kv and last_key and heading_key and last_key != heading_key:
        pending.append(details)
        return
    if last["summary"] and details["summary"]:
        if details.get("heading_key") and details.get("heading_key") == last.get("heading_key"):
            details = {**details, "kv": [], "title": ""}
        pending.append(details)
        return
    _apply_details(last, details)


def _apply_details(item: dict, details: dict) -> None:
    for extra in details.get("kv") or []:
        _merge_kv(item["kv"], extra)
    summary = details.get("summary") or ""
    if summary and not item["summary"] and not _same_opening(summary, item["title"]):
        item["summary"] = summary
    if details.get("title") and _is_kv_heading(details["title"]):
        _merge_kv(item["kv"], details["title"])


def _merge_kv(existing: List[str], extra: str) -> None:
    extra = _compact(extra)
    if not extra or ":" not in extra:
        return
    label, _, value = extra.partition(":")
    label_key = label.lower().strip()
    value = value.strip()
    for index, line in enumerate(existing):
        if line.split(":", 1)[0].lower().strip() != label_key:
            continue
        current = line.split(":", 1)[-1].strip()
        if label_key == "company" and "|" not in value and len(value) > len(current):
            existing[index] = _compact(f"{label.strip()}: {value}")
        return
    existing.append(_compact(f"{label.strip()}: {value}") if value else extra)


def _is_useful_details(details: dict) -> bool:
    if details.get("kv") or details.get("when"):
        return True
    summary = details.get("summary") or ""
    return len(summary) >= 40


def _details_from_chunk(heading: str, body: str, page: int) -> Optional[dict]:
    item = _item_from(heading, body, page)
    if not item:
        if body:
            return {"title": "", "when": "", "kv": [], "summary": _first_sentence(_compact(body), 200), "page": page}
        return None
    return item


def _item_from(heading: str, body: str, page: int) -> Optional[dict]:
    title = heading or _first_line(body)
    if not title or len(title) < 4:
        return None
    when_match = _WHEN.search(f"{title} {body[:160]}")
    when = _compact(when_match.group(0)) if when_match else ""
    if when:
        title = _compact(_WHEN.sub(" ", title)).strip(" |-")
    kv: List[str] = []
    rest: List[str] = []
    title, peeled = _peel_kv(title)
    kv.extend(peeled)
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if _KV.match(line) and len(kv) < 4:
            _, extra_from_line = _split_labeled_heading(line)
            for piece in extra_from_line or [_compact(line)]:
                _merge_kv(kv, piece)
        else:
            rest.append(line)
    summary = _first_sentence(_compact(" ".join(rest)), 200)
    pretty, extra_kv = _split_labeled_heading(title)
    if extra_kv:
        title = pretty
        kv = extra_kv + kv
    if not title:
        return None
    if summary and _same_opening(summary, title):
        summary = ""
    return {"title": title, "when": when, "kv": kv[:3], "summary": summary, "page": page}


def _peel_kv(title: str) -> tuple[str, List[str]]:
    compact = _compact(title)
    extras: List[str] = []
    match = _KV_IN_TITLE.search(compact)
    if match and compact.lower().find(match.group(1).lower() + ":") > 0:
        extras.append(_compact(f"{match.group(1)}: {match.group(2)}"))
        compact = _compact(compact[: match.start()]).strip(" |-")
    return compact, extras


def _is_dated_title(text: str) -> bool:
    compact = _compact(text)
    if not compact or len(compact) > 160 or compact.count(" ") > 18:
        return False
    return bool(_WHEN.search(compact))


def _is_section_header(text: str) -> bool:
    compact = _compact(text)
    if not compact or len(compact) > 48 or _WHEN.search(compact) or "|" in compact or ":" in compact:
        return False
    letters = re.sub(r"[^A-Za-z]", "", compact)
    return bool(letters) and letters.isupper() and len(compact.split()) <= 6


def _section_name(text: str) -> str:
    compact = _compact(text)
    if _is_section_header(compact):
        return compact
    match = re.match(r"^([A-Z][A-Z0-9 &/]{2,32})(?:\s+[A-Z][a-z]|\s*$)", compact)
    if match and not _WHEN.search(compact) and "|" not in compact[:24]:
        name = match.group(1).strip()
        if name not in {"AWS"} and len(name) >= 4:
            return name
    return ""


def _is_kv_heading(text: str) -> bool:
    return bool(_KV.match(_compact(text)))


def _split_labeled_heading(title: str) -> tuple[str, List[str]]:
    compact = _compact(title)
    if ":" not in compact:
        return compact, []
    head, sep, rest = compact.partition("|")
    if ":" not in head:
        return compact, []
    key, value = head.split(":", 1)
    if len(key.split()) != 1 or len(key) > 24:
        return compact, []
    extras = [_compact(f"{key}: {value}")]
    if rest.strip():
        extras.append(rest.strip())
    return value.strip() or compact, extras


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        compact = _compact(line)
        if compact:
            return compact[:180]
    return _compact(text)[:180]


def _first_sentence(text: str, limit: int) -> str:
    if not text:
        return ""
    match = re.search(r"(.+?[.!?])(\s|$)", text)
    snippet = _compact(match.group(1) if match else text)
    if len(snippet) <= limit:
        return snippet
    return snippet[: limit - 1].rsplit(" ", 1)[0] + "…"


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()
