from __future__ import annotations

from app.ai.list_answer import format_list_answer
from app.ai.types import RetrievedChunk


def _chunk(index: int, heading: str, text: str, page: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        id=str(index),
        document_id="doc",
        document_name="Resume.pdf",
        page_number=page,
        text=text,
        score=0.8,
        heading=heading,
        chunk_index=index,
    )


def test_list_answer_organizes_multiple_roles():
    chunks = [
        _chunk(0, "PROFESSIONAL EXPERIENCE", "PROFESSIONAL EXPERIENCE"),
        _chunk(
            1,
            "Full Stack Developer | UI/UX Designer August 2024 - Present",
            "Full Stack Developer | UI/UX Designer August 2024 - Present\nDesigned and developed Invoice Gen.",
        ),
        _chunk(2, "Company: RDAlabs | Skills: Angular | TypeScript", "Company: RDAlabs | Skills: Angular | TypeScript"),
        _chunk(3, "Backend Developer May 2019 - August 2019", "Backend Developer May 2019 - August 2019\nBuilt REST APIs."),
        _chunk(4, "Data Engineer May 2018 - August 2018", "Data Engineer May 2018 - August 2018\nWorked with pipelines."),
        _chunk(5, "Software Intern May 2017 - August 2017", "Software Intern May 2017 - August 2017\nLearned Java and OOP."),
        _chunk(6, "EDUCATION", "EDUCATION"),
        _chunk(7, "B.S. Computer Science", "B.S. Computer Science\nMay 2020 - May 2024"),
    ]
    answer = format_list_answer("What experience is listed?", chunks, "fallback")
    assert answer != "fallback"
    assert answer.count("- **") >= 4
    assert "full stack" in answer.lower()
    assert "backend developer" in answer.lower()
    assert "data engineer" in answer.lower()
    assert "software intern" in answer.lower()
    assert "education" not in answer.lower()
    assert "designed and developed" not in answer.lower()
    assert "built rest" not in answer.lower()


def test_list_answer_pairs_two_column_details_with_later_titles():
    """PDF column order often emits company/skills before the job titles."""
    chunks = [
        _chunk(0, "EDUCATION", "EDUCATION"),
        _chunk(1, "PROFESSIONAL EXPERIENCE", "PROFESSIONAL EXPERIENCE"),
        _chunk(2, "Company: Northwind | Skills: Angular | TypeScript", "Company: Northwind | Skills: Angular | TypeScript"),
        _chunk(3, "Company: Northwind | Skills: Angular | TypeScript", "Designed and developed Invoice Gen for small businesses."),
        _chunk(4, "Company: Northwind | Skills: Angular | TypeScript", "Applied object-oriented programming in an agile environment."),
        _chunk(5, "Company: Northwind | Skills: Python | Java", "Company: Northwind | Skills: Python | Java"),
        _chunk(6, "Company: Northwind | Skills: Python | Java", "Built a messaging platform using socket programming."),
        _chunk(
            7,
            "Full Stack Developer | UI/UX Designer                                                                                              August 2024 - Present",
            "Full Stack Developer | UI/UX Designer                                                                                              August 2024 - Present",
        ),
        _chunk(
            8,
            "Backend Developer                                                                                                                               May 2019 - August 2019",
            "Backend Developer                                                                                                                               May 2019 - August 2019",
        ),
        _chunk(
            9,
            "Data Engineer                                                                                                                                        May 2018 - August 2018",
            "Data Engineer                                                                                                                                        May 2018 - August 2018",
        ),
        _chunk(10, "PROJECTS Portal App Tech Stack: React", "PROJECTS Portal App Tech Stack: React"),
        _chunk(11, "AI & AUTOMATION", "AI & AUTOMATION"),
        _chunk(
            12,
            "Front Desk Assistant                                                                                                                 October 2025 - Present Company: City College",
            "Front Desk Assistant                                                                                                                 October 2025 - Present Company: City College",
        ),
        _chunk(
            13,
            "Front Desk Assistant                                                                                                                 October 2025 - Present Company: City College",
            "Assisted students at the front desk with registration questions.",
        ),
    ]
    answer = format_list_answer("What experience is listed?", chunks, "fallback")
    assert answer != "fallback"
    lowered = answer.lower()
    assert lowered.count("- **") >= 4
    assert "full stack developer" in lowered
    assert "backend developer" in lowered
    assert "data engineer" in lowered
    assert "front desk assistant" in lowered
    assert "northwind" in lowered
    assert "city college" in lowered
    assert "professional experience" in lowered
    assert "designed and developed" not in lowered
    assert "object-oriented" not in lowered
    assert "messaging platform" not in lowered
    assert "assisted students" not in lowered
    assert not lowered.strip().startswith("company:")
    assert lowered.index("front desk assistant") < lowered.index("full stack developer")
    assert lowered.index("full stack developer") < lowered.index("backend developer")
    assert lowered.index("backend developer") < lowered.index("data engineer")


def test_list_answer_sorts_experience_newest_first():
    chunks = [
        _chunk(0, "PROFESSIONAL EXPERIENCE", "PROFESSIONAL EXPERIENCE"),
        _chunk(1, "Data Engineer May 2018 - August 2018", "Data Engineer May 2018 - August 2018"),
        _chunk(2, "Backend Developer May 2019 - August 2019", "Backend Developer May 2019 - August 2019"),
        _chunk(3, "Full Stack Developer August 2024 - Present", "Full Stack Developer August 2024 - Present"),
        _chunk(4, "Registrar Assistant October 2025 - Present", "Registrar Assistant October 2025 - Present"),
    ]
    answer = format_list_answer("What experience is listed?", chunks, "fallback").lower()
    assert answer.index("registrar assistant") < answer.index("full stack developer")
    assert answer.index("full stack developer") < answer.index("backend developer")
    assert answer.index("backend developer") < answer.index("data engineer")


def test_list_answer_skips_cover_letter():
    chunks = [
        _chunk(0, "Dear Hiring Team,", "Dear Hiring Team, I am writing to express my interest in the developer role."),
        _chunk(1, "Backend Developer May 2019 - August 2019", "Backend Developer May 2019 - August 2019"),
    ]
    answer = format_list_answer("What experience is listed?", chunks, "fallback")
    assert "hiring team" not in answer.lower()
    assert "backend developer" in answer.lower()


def test_list_answer_lists_policy_deadlines():
    chunks = [
        _chunk(0, "COMPLIANCE DEADLINES", "COMPLIANCE DEADLINES"),
        _chunk(1, "Safety audit January 2024 - March 2024", "Safety audit January 2024 - March 2024\nSubmit the plant safety report."),
        _chunk(2, "License renewal April 2024 - June 2024", "License renewal April 2024 - June 2024\nFile with the county clerk."),
    ]
    answer = format_list_answer("What deadlines are listed?", chunks, "fallback")
    assert "safety audit" in answer.lower()
    assert "license renewal" in answer.lower()
    assert "compliance deadlines" in answer.lower()
    assert "submit the plant" not in answer.lower()
    assert "file with the county" not in answer.lower()
    assert answer.lower().index("license renewal") < answer.lower().index("safety audit")
