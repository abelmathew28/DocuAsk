from __future__ import annotations


def test_register_login_and_me(client):
    register = client.post(
        "/api/auth/register",
        json={"name": "Abel", "email": "abel@example.com", "password": "password123"},
    )
    assert register.status_code == 200
    body = register.json()
    assert body["user"]["email"] == "abel@example.com"
    assert "access_token" in body

    duplicate = client.post(
        "/api/auth/register",
        json={"name": "Abel", "email": "abel@example.com", "password": "password123"},
    )
    assert duplicate.status_code == 409

    login = client.post(
        "/api/auth/login",
        json={"email": "abel@example.com", "password": "password123"},
    )
    assert login.status_code == 200

    bad = client.post(
        "/api/auth/login",
        json={"email": "abel@example.com", "password": "wrongpass"},
    )
    assert bad.status_code == 401

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["name"] == "Abel"


def test_protected_route_requires_auth(client):
    response = client.get("/api/documents")
    assert response.status_code == 401
