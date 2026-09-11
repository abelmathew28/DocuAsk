from __future__ import annotations


def test_intelligence_endpoints_require_auth(client):
    assert client.post("/api/research", json={"question": "x", "document_ids": []}).status_code in {401, 403, 422}
    assert client.post("/api/compare", json={"document_a_id": "a", "document_b_id": "b", "question": "x"}).status_code in {
        401,
        403,
        422,
    }
    assert client.post("/api/extract", json={"question": "x", "document_ids": []}).status_code in {401, 403, 422}
