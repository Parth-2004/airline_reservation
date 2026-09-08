import pytest
import time

def test_missing_flight(client):
    res = client.get("/api/flights/NONEXISTENT")
    assert res.status_code == 404

def test_unauthenticated(client):
    res = client.get("/api/bookings")
    assert res.status_code == 401

    res = client.get("/api/admin/users")
    assert res.status_code == 401

def test_invalid_login(client):
    res = client.post("/api/auth/login", json={"username": "wrong", "password": "wrong"})
    assert res.status_code == 401

def test_invalid_register(client):
    username = f"testuser_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    # Register again
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    assert res.status_code == 400

def test_missing_flight_seatmap(client):
    res = client.get("/api/flights/NONEXISTENT/seatmap")
    assert res.status_code == 404

def test_missing_flight_seats(client):
    res = client.get("/api/flights/NONEXISTENT/seats")
    assert res.status_code == 404

def test_booking_key_error(client):
    username = f"testbooker_keyerr_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    res = client.post("/api/auth/login", json={"username": username, "password": "testpassword123"})
    uid = res.get_json()["data"]["id"]

    # Missing passenger_id
    res = client.post("/api/bookings", headers={"X-User-Id": uid}, json={
        "flight_id": "F1",
        "seat_id": "S1"
    })

    assert res.status_code == 400
    assert "Missing required field" in res.get_json()["error"]
    assert "passenger_id" in res.get_json()["error"]
