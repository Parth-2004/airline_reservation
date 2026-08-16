import pytest
import time

def test_options(client):
    res = client.options("/api/flights")
    assert res.status_code == 200

    res = client.options("/")
    assert res.status_code == 200

def test_require_login_invalid(client):
    res = client.get("/api/bookings", headers={"X-User-Id": "INVALID_ID"})
    assert res.status_code == 401

def test_require_admin_invalid(client):
    res = client.get("/api/admin/users", headers={"X-User-Id": "INVALID_ID"})
    assert res.status_code == 403

def test_require_admin_not_admin(client):
    # Register regular user
    username = f"testuser_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    res = client.post("/api/auth/login", json={
        "username": username,
        "password": "testpassword123"
    })
    user_id = res.get_json()["data"]["id"]

    # Try accessing admin endpoint
    res = client.get("/api/admin/users", headers={"X-User-Id": user_id})
    assert res.status_code == 403

def test_static_routes(client):
    res = client.get("/")
    assert res.status_code == 200

    res = client.get("/login")
    assert res.status_code == 200

    res = client.get("/admin")
    assert res.status_code == 200
