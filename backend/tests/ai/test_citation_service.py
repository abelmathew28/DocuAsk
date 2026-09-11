from __future__ import annotations

from app.ai.citation_service import citation_excerpt, rank_citation_chunks
from app.ai.types import RetrievedChunk


def _chunk(
    chunk_id: str,
    page: int,
    heading: str,
    text: str,
    index: int = 0,
    score: float = 0.8,
) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        document_id="doc",
        document_name="Resume.pdf",
        page_number=page,
        text=text,
        score=score,
        heading=heading,
        chunk_index=index,
    )


def test_rank_citation_chunks_prefers_answer_items_over_section_headers():
    answer = (
        "**Professional Experience**\n\n"
        "- **Full Stack Developer | UI/UX Designer**\n"
        "  August 2024 - Present\n"
        "  Company: RDAlabs\n"
        "  Skills: Angular | TypeScript\n"
    )
    chunks = [
        _chunk("1", 1, "PROFESSIONAL EXPERIENCE", "PROFESSIONAL EXPERIENCE", index=3),
        _chunk(
            "2",
            1,
            "Full Stack Developer | UI/UX Designer August 2024 - Present",
            "Full Stack Developer | UI/UX Designer August 2024 - Present",
            index=9,
        ),
        _chunk("3", 2, "Dear Hiring Team,", "Dear Hiring Team, I am writing to express my interest.", index=25),
    ]
    picked = rank_citation_chunks(answer, chunks)
    assert picked
    assert picked[0].id == "2"
    assert "professional experience" not in citation_excerpt(answer, picked[0]).lower() or "full stack" in citation_excerpt(answer, picked[0]).lower()


def test_rank_citation_chunks_points_to_reference_emails():
    answer = (
        "**Queen College**\n\n"
        "- **Jomy George**\n"
        "  Email: jomy.george@qc.cuny.edu\n"
    )
    chunks = [
        _chunk("1", 1, "PROFESSIONAL EXPERIENCE", "PROFESSIONAL EXPERIENCE"),
        _chunk(
            "2",
            3,
            "Jomy George Registrar Administrator Email: jomy.george@qc.cuny.edu",
            "Jomy George Registrar Administrator Email: jomy.george@qc.cuny.edu",
            index=31,
        ),
        _chunk("3", 2, "Dear Hiring Team,", "Dear Hiring Team, I am writing to express my interest.", index=25),
    ]
    picked = rank_citation_chunks(answer, chunks)
    assert picked
    assert picked[0].page_number == 3
    excerpt = citation_excerpt(answer, picked[0]).lower()
    assert "jomy.george@qc.cuny.edu" in excerpt


def test_citation_excerpt_surfaces_matching_passage():
    answer = "- **Data Engineer**\n  May 2018 - August 2018\n  Company: RDAlabs"
    chunk = _chunk(
        "1",
        1,
        "Data Engineer May 2018 - August 2018",
        "Data Engineer May 2018 - August 2018",
    )
    excerpt = citation_excerpt(answer, chunk)
    assert "data engineer" in excerpt.lower()
    assert "2018" in excerpt
