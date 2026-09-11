from __future__ import annotations

from app.ai.local_provider import ExtractiveProvider, HashEmbeddingProvider
from app.ai.prompts import build_context_block, build_user_prompt
from app.core.config import settings


def test_hash_embeddings_match_configured_dimensions():
    vectors = HashEmbeddingProvider().embed(["vacation policy", "safety rules"])
    assert len(vectors) == 2
    assert len(vectors[0]) == settings.embedding_dimensions
    assert abs(sum(v * v for v in vectors[0]) - 1.0) < 1e-6


def test_extractive_answers_from_retrieved_pages():
    context = build_context_block(
        [
            {
                "document_name": "Handbook",
                "page_number": 14,
                "text": "Vacation policy: full-time employees receive 15 paid vacation days each year. Unused days do not roll over.",
            }
        ]
    )
    prompt = build_user_prompt("How many vacation days do employees receive?", context, "I couldn't find enough information in this document to answer that question.")
    answer = ExtractiveProvider().complete("system", [{"role": "user", "content": prompt}], max_tokens=200)
    assert "15" in answer
    assert "vacation" in answer.lower()


def test_extractive_answers_experience_from_resume_passages():
    context = build_context_block(
        [
            {
                "document_name": "Resume.pdf",
                "page_number": 1,
                "heading": "PROFESSIONAL EXPERIENCE",
                "text": (
                    "Full Stack Developer | UI/UX Designer  August 2024 - Present\n"
                    "Company: RDAlabs\n"
                    "Designed and developed Invoice Gen, a billing platform used by operations teams."
                ),
            }
        ]
    )
    prompt = build_user_prompt(
        "What experience is listed?",
        context,
        "I couldn't find enough information in this document to answer that question.",
    )
    answer = ExtractiveProvider().complete("system", [{"role": "user", "content": prompt}], max_tokens=200)
    assert "couldn't find" not in answer.lower()
    assert "rdalabs" in answer.lower() or "invoice gen" in answer.lower() or "developer" in answer.lower()
    assert "hiring team" not in answer.lower()


def test_extractive_prefers_roles_over_cover_letter():
    context = build_context_block(
        [
            {
                "document_name": "Resume.pdf",
                "page_number": 3,
                "heading": "Dear Hiring Team,",
                "text": (
                    "Dear Hiring Team, I am writing to express my interest in the developer role. "
                    "My professional experience includes internships and I would welcome the opportunity to contribute."
                ),
            },
            {
                "document_name": "Resume.pdf",
                "page_number": 1,
                "heading": "PROFESSIONAL EXPERIENCE",
                "text": "Full Stack Developer | UI/UX Designer  August 2024 - Present\nCompany: RDAlabs",
            },
        ]
    )
    prompt = build_user_prompt(
        "What experience is listed?",
        context,
        "I couldn't find enough information in this document to answer that question.",
    )
    answer = ExtractiveProvider().complete("system", [{"role": "user", "content": prompt}], max_tokens=200)
    assert "rdalabs" in answer.lower()
    assert "full stack" in answer.lower()


def test_extractive_stays_insufficient_on_unrelated_passages():
    context = build_context_block(
        [
            {
                "document_name": "Handbook",
                "page_number": 14,
                "text": "The cafeteria serves lunch from 11:30 a.m. to 1:30 p.m. on weekdays.",
            }
        ]
    )
    prompt = build_user_prompt(
        "What experience is listed?",
        context,
        "I couldn't find enough information in this document to answer that question.",
    )
    answer = ExtractiveProvider().complete("system", [{"role": "user", "content": prompt}], max_tokens=200)
    assert "could not find enough information" in answer.lower() or "couldn't find enough information" in answer.lower()
