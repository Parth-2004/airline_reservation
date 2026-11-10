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
    username = f"testuser_{time.time_ns()}"
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

def test_api_json_errors(client):
    res = client.get("/api/nonexistent")
    assert res.status_code == 404
    assert res.is_json

    res = client.post("/api/flights", json={})
    assert res.status_code == 405
    assert res.is_json

    res = client.post("/api/auth/login", data="invalid json", headers={"Content-Type": "application/json"})
    assert res.status_code == 400
    assert res.is_json

def test_api_other_http_error(client):
    res = client.post("/api/flights") # Method Not Allowed
    assert res.status_code == 405
    assert res.is_json

def test_cors_preflight_undefined_route(client):
    res = client.options("/api/nonexistent")
    assert res.status_code == 200
    assert res.is_json
