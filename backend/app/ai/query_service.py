from __future__ import annotations

import re
from typing import List, Sequence, Set

from app.ai.hybrid_search import tokenize

_PRONOUN = re.compile(
    r"\b(it|this|that|they|them|those|these|the deadline|the policy|the requirement|the date)\b",
    re.I,
)

# Extra retrieval terms for questions whose wording rarely appears in passages.
_TOPIC_EXPANSIONS = (
    (
        ("deadline", "due date", "due on"),
        "deadline due date due by submit by",
    ),
    (
        ("require", "eligib", "must"),
        "requirements eligibility must shall",
    ),
    (
        ("fee", "cost", "amount", "salary", "tuition"),
        "amount cost fee salary tuition",
    ),
)

_STEM_SUFFIXES = ("ing", "ers", "ies", "ied", "ed", "er", "ment", "tion", "s")


def expand_search_query(question: str) -> str:
    text = (question or "").strip()
    if not text:
        return text
    lowered = text.lower()
    extras: List[str] = []
    listed = re.search(r"\bwhat ([a-z0-9][a-z0-9 \-/]{1,40}?) (is|are) listed\b", lowered)
    if listed:
        extras.append(listed.group(1).strip())
    for needles, expansion in _TOPIC_EXPANSIONS:
        if any(needle in lowered for needle in needles):
            extras.append(expansion)
    if not extras:
        return text
    return f"{text} {' '.join(extras)}"


def expanded_terms(question: str) -> Set[str]:
    tokens = set(tokenize(expand_search_query(question)))
    stemmed: Set[str] = set()
    for token in tokens:
        stemmed.update(_stems(token))
    return stemmed


def term_overlap(terms: Set[str], text: str) -> int:
    if not terms or not text:
        return 0
    passage = set()
    for token in tokenize(text):
        passage.update(_stems(token))
    return len(terms & passage)


def _stems(token: str) -> Set[str]:
    stems = {token}
    for suffix in _STEM_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            stems.add(token[: -len(suffix)])
    if token.endswith("ies") and len(token) > 5:
        stems.add(token[:-3] + "y")
    return stems


def rewrite_question(question: str, history: Sequence[dict]) -> str:
    text = (question or "").strip()
    if not text:
        return text
    if len(text.split()) >= 8 and not _PRONOUN.search(text):
        return text
    prior = _last_user_and_answer(history)
    if not prior:
        return text
    last_q, last_a = prior
    if last_q.lower() in text.lower():
        return text
    return f"{text}\n\n(Regarding the previous question: {last_q} Previous answer: {last_a[:240]})"


def search_queries(question: str) -> List[str]:
    queries = [question.strip()]
    expanded = expand_search_query(question)
    if expanded not in queries:
        queries.append(expanded)
    lowered = question.lower()
    if any(word in lowered for word in ("compare", "difference", "across", "versus", "vs")):
        queries.append(question.replace("compare", "requirements").strip())
    if any(word in lowered for word in ("deadline", "date", "when", "due")):
        queries.append(f"deadline due date {question}")
    if any(word in lowered for word in ("require", "must", "eligib", "need")):
        queries.append(f"requirements {question}")
    if any(word in lowered for word in ("how much", "cost", "fee", "amount", "salary", "revenue")):
        queries.append(f"amount cost {question}")
    unique: List[str] = []
    for item in queries:
        if item and item not in unique:
            unique.append(item)
    return unique[:4]


def _last_user_and_answer(history: Sequence[dict]) -> tuple[str, str] | None:
    user = None
    assistant = None
    for message in history:
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if role == "user":
            user = content.split("\n\nQuestion:")[-1].strip() if "Question:" in content else content
        elif role == "assistant":
            assistant = content
    if user and assistant:
        return user[:240], assistant[:320]
    return None
