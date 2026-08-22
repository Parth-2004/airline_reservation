import pytest
from utils.database import get_seats, get_all_flights, add_flight, get_conn

def test_admin_cancel_other_user_booking(client):
    # Register user
    client.post("/api/auth/register", json={"username": "testuser_cancelact", "email": "testca@test.com", "password": "password"})
    res = client.post("/api/auth/login", json={"username": "testuser_cancelact", "password": "password"})
    user_id = res.get_json()["data"]["id"]
    pax_id = res.get_json()["data"]["passenger_id"]

    # Admin add flight
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    try:
        add_flight("TESTFLIGHT4", "AAA", "A", "BBB", "B", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")
    except ValueError:
        pass

    with get_conn() as conn:
        res_seats = conn.execute("SELECT * FROM seats WHERE flight_id='TESTFLIGHT4'").fetchall()
        available_seat = next((s["id"] for s in res_seats if s["status"] == "available"), None)

    # Book a seat as user
    res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
        "passenger_id": pax_id,
        "flight_id": "TESTFLIGHT4",
        "seat_ids": [available_seat]
    })
    assert res.status_code == 201
    booking_id = res.get_json()["data"]["bookings"][0]["id"]

    # Cancel as admin
    res = client.post(f"/api/bookings/{booking_id}/cancel", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True

def test_admin_book_other_user(client):
    # Register user
    client.post("/api/auth/register", json={"username": "testuser_bookact", "email": "testba@test.com", "password": "password"})
    res = client.post("/api/auth/login", json={"username": "testuser_bookact", "password": "password"})
    pax_id = res.get_json()["data"]["passenger_id"]

    # Login as admin
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    try:
        add_flight("TESTFLIGHT5", "AAA", "A", "BBB", "B", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")
    except ValueError:
        pass

    with get_conn() as conn:
        res_seats = conn.execute("SELECT * FROM seats WHERE flight_id='TESTFLIGHT5'").fetchall()
        available_seat = next((s["id"] for s in res_seats if s["status"] == "available"), None)

    # Book as admin for user
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": pax_id,
        "flight_id": "TESTFLIGHT5",
        "seat_ids": [available_seat]
    })
    assert res.status_code == 201
    assert res.get_json()["ok"] is True

def test_admin_get_bookings_other_user(client):
    # Register user
    client.post("/api/auth/register", json={"username": "testuser_getact", "email": "testga@test.com", "password": "password"})
    res = client.post("/api/auth/login", json={"username": "testuser_getact", "password": "password"})
    pax_id = res.get_json()["data"]["passenger_id"]

    # Login as admin
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    # Get bookings as admin for user
    res = client.get(f"/api/bookings?passenger_id={pax_id}", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True
