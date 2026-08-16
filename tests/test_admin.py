import pytest

def test_admin_stats(client):
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    admin_id = data["id"]

    res = client.get("/api/admin/stats", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
    stats = res.get_json()["data"]
    assert "total_flights" in stats
    assert "total_passengers" in stats

def test_admin_revenue(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/admin/revenue", headers={"X-User-Id": admin_id})
    assert res.status_code == 200

def test_admin_occupancy(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/admin/occupancy", headers={"X-User-Id": admin_id})
    assert res.status_code == 200

def test_admin_users_and_passengers(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/admin/users", headers={"X-User-Id": admin_id})
    assert res.status_code == 200

    res = client.get("/api/passengers", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
