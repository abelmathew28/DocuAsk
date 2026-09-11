from __future__ import annotations

from app.ai.chat import title_from_question
from app.ai.chunking_service import chunk_pages
from app.ai.citation_service import verify_answer
from app.ai.hybrid_search import keyword_score, reciprocal_rank_fusion
from app.ai.processor import PageText
from app.ai.types import RetrievedChunk, TextBlock


def test_chunking_preserves_page_numbers():
    pages = [
        PageText(page_number=1, text="Vacation policy: employees receive 15 days. " * 20),
        PageText(page_number=2, text="Sick leave is 10 days per calendar year."),
    ]
    chunks = chunk_pages(pages, chunk_size=80, overlap=10)
    assert chunks
    assert {chunk.page_number for chunk in chunks} <= {1, 2}
    assert any(chunk.page_number == 2 for chunk in chunks)


def test_semantic_chunking_keeps_headings_and_tables():
    page = PageText(
        page_number=3,
        text="Leave\nEmployees receive 15 days.\nCategory | Days\nVacation | 15",
        heading="Leave",
        blocks=[
            TextBlock(text="Leave", kind="heading"),
            TextBlock(text="Employees receive 15 days.", kind="paragraph", heading="Leave"),
            TextBlock(text="Category | Days\nVacation | 15", kind="table", heading="Leave"),
        ],
    )
    chunks = chunk_pages([page], chunk_size=400, overlap=40)
    assert any(chunk.chunk_type == "table" for chunk in chunks)
    assert any(chunk.heading == "Leave" for chunk in chunks)
    assert not any(chunk.chunk_type == "heading" and len(chunk.text) < 20 for chunk in chunks)
    assert any("Employees receive 15 days" in chunk.text for chunk in chunks)


def test_chunking_keeps_section_heading_with_body():
    page = PageText(
        page_number=1,
        text="PROFESSIONAL EXPERIENCE\nFull Stack Developer\nDesigned Invoice Gen.",
        heading="PROFESSIONAL EXPERIENCE",
        blocks=[
            TextBlock(text="PROFESSIONAL EXPERIENCE", kind="heading"),
            TextBlock(text="Full Stack Developer | UI/UX Designer", kind="heading"),
            TextBlock(text="Designed and developed Invoice Gen.", kind="paragraph"),
        ],
    )
    chunks = chunk_pages([page], chunk_size=400, overlap=40)
    joined = " ".join(chunk.text for chunk in chunks)
    assert "Invoice Gen" in joined
    assert any("PROFESSIONAL EXPERIENCE" in chunk.text and "Invoice Gen" in chunk.text for chunk in chunks)


def test_keyword_score_prefers_exact_terms():
    query = "graduation deadline November 1"
    high = keyword_score(query, "The graduation deadline is November 1.")
    low = keyword_score(query, "The cafeteria serves lunch at noon.")
    assert high > low


def test_rrf_merges_lists():
    a = RetrievedChunk(id="1", document_id="d", document_name="A", page_number=1, text="one", score=0.9)
    b = RetrievedChunk(id="2", document_id="d", document_name="A", page_number=2, text="two", score=0.4)
    fused = reciprocal_rank_fusion([[a, b], [b, a]])
    assert {item.id for item in fused} == {"1", "2"}


def test_evidence_rejects_unsupported_claim():
    chunk = RetrievedChunk(
        id="1",
        document_id="d",
        document_name="Policy",
        page_number=1,
        text="Employees receive 15 paid vacation days each year.",
        score=0.8,
    )
    answer, supported = verify_answer("The moon is made of cheese.", [chunk], "fallback")
    assert answer == "fallback"
    assert supported == []
    kept, sources = verify_answer("Employees receive 15 paid vacation days each year.", [chunk], "fallback")
    assert "15" in kept


def test_title_from_question():
    assert "Vacation" in title_from_question("What is the vacation policy?")


def test_experience_question_expands_search_terms():
    from app.ai.query_service import expand_search_query, expanded_terms, term_overlap

    query = expand_search_query("What experience is listed?")
    assert "experience" in query.lower()
    terms = expanded_terms("What experience is listed?")
    assert term_overlap(terms, "PROFESSIONAL EXPERIENCE internships and roles") >= 1
    assert term_overlap(terms, "The cafeteria serves lunch at noon.") == 0


def test_resume_questions_are_document_specific():
    from app.utils.insights import extractive_summary, suggested_questions

    pages = [
        PageText(
            page_number=1,
            text="ABEL REJI MATHEW\n(732)-890-1441 | mathewabel28@gmail.com | linkedin.com/in/abel\nEXPERIENCE\nSoftware intern at Acme.\nEDUCATION\nB.S. Computer Science\nSKILLS\nPython, TypeScript",
            heading="ABEL REJI MATHEW",
            blocks=[
                TextBlock(text="ABEL REJI MATHEW", kind="heading"),
                TextBlock(text="EXPERIENCE", kind="heading"),
                TextBlock(text="Software intern at Acme.", kind="paragraph"),
                TextBlock(text="EDUCATION", kind="heading"),
                TextBlock(text="SKILLS", kind="heading"),
            ],
        )
    ]
    questions = suggested_questions(pages)
    assert any("experience" in item.lower() for item in questions)
    assert not any("vacation" in item.lower() for item in questions)
    brief = extractive_summary(pages)
    assert "@" not in brief
    assert "gmail" not in brief.lower()
