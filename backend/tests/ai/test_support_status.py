from __future__ import annotations

from app.ai.citation_service import compute_support_status


def test_support_status_not_found_for_abstention():
    assert (
        compute_support_status(
            "I could not find enough information in the selected documents to answer this."
        )
        == "not_found"
    )


def test_support_status_supported_with_sources():
    assert compute_support_status("Withdraw by November 6, 2026.", [{"page": 2}]) == "supported"


def test_support_status_partial_without_sources():
    assert compute_support_status("Some grounded-looking text without citations.") == "partially_supported"
