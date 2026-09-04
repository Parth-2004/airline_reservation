import pytest
from utils.database import add_flight

def test_admin_flights(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/admin/aircraft-models", headers={"X-User-Id": admin_id})
    assert res.status_code == 200

    # Add flight
    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TEST1234",
        "origin": "JFK",
        "origin_full": "New York",
        "destination": "LHR",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 201

    # Delete flight
    res = client.delete("/api/admin/flights/TEST1234", headers={"X-User-Id": admin_id})
    assert res.status_code == 200

def test_admin_update_tier(client):
    # Register a user to ensure there's at least one passenger
    client.post("/api/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "password"})

    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/passengers", headers={"X-User-Id": admin_id})
    passengers = res.get_json()["data"]
    passenger_id = passengers[0]["id"]

    res = client.put(f"/api/passengers/{passenger_id}/tier", headers={"X-User-Id": admin_id}, json={
        "tier": "Gold"
    })
    assert res.status_code == 200

def test_admin_bookings(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/admin/bookings", headers={"X-User-Id": admin_id})
    assert res.status_code == 200

def test_add_flight_invalid_dates():
    with pytest.raises(ValueError, match="Invalid date format."):
        add_flight("TF_INV1", "A", "A", "B", "B", "invalid_date", "invalid_date")

    with pytest.raises(ValueError, match="Arrival time must be after departure time."):
        add_flight("TF_INV2", "A", "A", "B", "B", "2024-12-01T22:00:00", "2024-12-01T10:00:00")

    with pytest.raises(ValueError, match="Arrival time must be after departure time."):
        add_flight("TF_INV3", "A", "A", "B", "B", "2024-12-01T10:00:00", "2024-12-01T10:00:00")


def test_add_flight_empty_fields(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "",
        "origin": "JFK",
        "origin_full": "New York",
        "destination": "LHR",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 400
    assert "Flight ID cannot be empty" in res.get_json()["error"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TEST",
        "origin": "  ",
        "origin_full": "New York",
        "destination": "LHR",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 400
    assert "Origin cannot be empty" in res.get_json()["error"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TEST",
        "origin": "JFK",
        "origin_full": "",
        "destination": "LHR",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 400
    assert "Origin full name cannot be empty" in res.get_json()["error"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TEST",
        "origin": "JFK",
        "origin_full": "New York",
        "destination": "  ",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 400
    assert "Destination cannot be empty" in res.get_json()["error"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TEST",
        "origin": "JFK",
        "origin_full": "New York",
        "destination": "LHR",
        "dest_full": "",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 400
    assert "Destination full name cannot be empty" in res.get_json()["error"]
