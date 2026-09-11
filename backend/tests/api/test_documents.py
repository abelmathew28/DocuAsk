from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def _pdf_bytes(text: str = "Hello from DocuAsk") -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def test_upload_list_and_isolation(client, auth_headers):
    upload = client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("handbook.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["id"]

    listed = client.get("/api/documents", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    other = client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "other@example.com", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    forbidden = client.get(f"/api/documents/{document_id}", headers=other_headers)
    assert forbidden.status_code == 404

    deleted = client.delete(f"/api/documents/{document_id}", headers=auth_headers)
    assert deleted.status_code == 200
    missing = client.get(f"/api/documents/{document_id}", headers=auth_headers)
    assert missing.status_code == 404


def test_rejects_unsupported_type(client, auth_headers):
    response = client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("photo.png", b"\x89PNG", "image/png")},
    )
    assert response.status_code == 422


def test_upload_txt(client, auth_headers):
    response = client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("notes.txt", b"Vacation policy: 15 days per year.\n", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["document_type"] == "txt"
