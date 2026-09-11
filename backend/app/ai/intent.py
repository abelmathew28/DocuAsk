from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    FACT_LOOKUP = "fact_lookup"
    LIST = "list"
    SUMMARY = "summary"
    COMPARE = "compare"
    EXTRACT = "extract"
    RESEARCH = "research"
    EXPLAIN = "explain"
    LOCATE_SOURCE = "locate_source"


_LIST = re.compile(
    r"\b(listed|list the|list all|what are the|which .+ are|all of the|every)\b",
    re.I,
)
_SUMMARY = re.compile(r"\b(summarize|summary|overview|tl;dr|key points)\b", re.I)
_COMPARE = re.compile(r"\b(compare|difference|differ|versus|\bvs\.?\b|conflict)\b", re.I)
_LOCATE = re.compile(r"\b(which page|what page|where (does|is|are)|find the (section|page))\b", re.I)
_EXPLAIN = re.compile(r"\b(explain|how does|how do|why does|walk me through)\b", re.I)


def classify_intent(question: str, mode: str = "ask") -> Intent:
    lowered = (mode or "ask").lower()
    if lowered == "research":
        return Intent.RESEARCH
    if lowered == "extract":
        return Intent.EXTRACT
    if lowered == "compare":
        return Intent.COMPARE

    text = question or ""
    if _SUMMARY.search(text):
        return Intent.SUMMARY
    if _COMPARE.search(text):
        return Intent.COMPARE
    if _LOCATE.search(text):
        return Intent.LOCATE_SOURCE
    if _LIST.search(text) or re.search(r"^what [a-z].*(is|are) listed\b", text.strip(), re.I):
        return Intent.LIST
    if _EXPLAIN.search(text):
        return Intent.EXPLAIN
    return Intent.FACT_LOOKUP
