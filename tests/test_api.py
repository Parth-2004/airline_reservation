import pytest
import time

def test_get_flights(client):
    res = client.get("/api/flights")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

def test_register_and_login(client):
    username = f"testuser_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["username"] == username
    assert "password" not in data["data"]

    res = client.post("/api/auth/login", json={
        "username": username,
        "password": "testpassword123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["username"] == username
    assert "token" in data["data"] or "id" in data["data"]

def test_get_flight_seatmap(client):
    res = client.get("/api/flights")
    flights = res.get_json()["data"]
    flight_id = flights[0]["id"]

    res = client.get(f"/api/flights/{flight_id}/seatmap")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

def test_booking(client):
    username = f"testbooker_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    data = res.get_json()["data"]
    user_id = data["id"]
    passenger_id = data["passenger_id"]

    # Book a seat
    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    res = client.get(f"/api/flights/{flight_id}/seats")
    available_seats = [s for s in res.get_json()["data"] if s["status"] == "available"]
    seat_id = available_seats[0]["id"]

    res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_id": seat_id
    })
    assert res.status_code == 201

    # Get bookings
    res = client.get(f"/api/bookings?passenger_id={passenger_id}", headers={"X-User-Id": user_id})
    assert res.status_code == 200
    bookings = res.get_json()["data"]
    assert len(bookings) == 1
    assert bookings[0]["seat_id"] == seat_id

def test_booking_cancel(client):
    username = f"testcancel_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    data = res.get_json()["data"]
    user_id = data["id"]
    passenger_id = data["passenger_id"]

    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    res = client.get(f"/api/flights/{flight_id}/seats")
    available_seats = [s for s in res.get_json()["data"] if s["status"] == "available"]
    seat_id = available_seats[0]["id"]

    res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_id": seat_id
    })
    assert res.status_code == 201
    booking_id = res.get_json()["data"]["id"]

    # Cancel booking
    res = client.post(f"/api/bookings/{booking_id}/cancel", headers={"X-User-Id": user_id})
    assert res.status_code == 200

    # Verify cancellation
    res = client.get(f"/api/bookings?passenger_id={passenger_id}", headers={"X-User-Id": user_id})
    bookings = res.get_json()["data"]
    assert bookings[0]["status"] == "Cancelled"
