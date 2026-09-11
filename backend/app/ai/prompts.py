INSUFFICIENT_DOCUMENT = "I could not find enough information in the selected documents to answer this."
INSUFFICIENT_SELECTED = "I could not find enough information in the selected documents to answer this."
INSUFFICIENT_LIBRARY = "I could not find enough information in the selected documents to answer this."

SYSTEM_PROMPT = """You are DocuAsk, a document Q&A assistant.

Answer using ONLY the document excerpts in the user message.
Do not use outside knowledge, training data, or guesswork.
Do not invent policies, numbers, names, or page numbers.

If the excerpts do not contain the answer, reply with exactly:
{fallback}

When the excerpts do contain the answer:
- Be accurate and concise.
- Keep numbers, dates, and policy names exactly as written.
- Cite sources inline like [1] using the Source numbers provided.
- You may mention page numbers only when they appear in the source metadata.
- Do not invent citations or source numbers that were not provided.
"""


def insufficient_message(scope: str) -> str:
    if scope == "selected":
        return INSUFFICIENT_SELECTED
    if scope == "library":
        return INSUFFICIENT_LIBRARY
    return INSUFFICIENT_DOCUMENT


def system_prompt(scope: str) -> str:
    return SYSTEM_PROMPT.format(fallback=insufficient_message(scope))


def build_context_block(chunks: list[dict]) -> str:
    if not chunks:
        return "No document context was retrieved."

    parts = []
    for index, chunk in enumerate(chunks, start=1):
        heading = chunk.get("heading")
        head = f" | Section: {heading}" if heading else ""
        body = chunk["text"]
        if heading and heading not in body:
            body = f"{heading}\n{body}"
        parts.append(
            f"[Source {index}] Document: {chunk['document_name']} | Page: {chunk['page_number']}{head}\n{body}"
        )
    return "\n\n".join(parts)


def build_user_prompt(question: str, context: str, fallback: str) -> str:
    return (
        "Use only the following document excerpts to answer the question.\n\n"
        f"{context}\n\n"
        f"Question: {question}\n\n"
        f"If the excerpts do not contain the answer, reply with: {fallback}"
    )


def is_insufficient_answer(text: str) -> bool:
    lowered = (text or "").strip().lower()
    if not lowered:
        return True
    needles = (
        "couldn't find enough information",
        "could not find enough information",
        "not enough information in this document",
        "not enough information in the selected",
        "not enough information in your library",
    )
    return any(needle in lowered for needle in needles)
