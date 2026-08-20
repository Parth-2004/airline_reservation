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

def test_admin_aircraft_models(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/admin/aircraft-models", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
    models = res.get_json()["data"]
    assert "Boeing 737" in models

def test_admin_update_tier(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"]["passenger_id"]

    res = client.put(f"/api/passengers/{passenger_id}/tier", headers={"X-User-Id": admin_id}, json={"tier": "Gold"})
    assert res.status_code == 200

    res = client.get("/api/passengers", headers={"X-User-Id": admin_id})
    passengers = res.get_json()["data"]
    updated_pax = next(p for p in passengers if p["id"] == passenger_id)
    assert updated_pax["tier"] == "Gold"
