import pytest
import sqlite3

def test_delete_flight_with_bookings(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TEST6666",
        "origin": "JFK",
        "origin_full": "New York",
        "destination": "LHR",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })
    assert res.status_code == 201

    client.post("/api/auth/register", json={"username": "user2", "email": "u2@test.com", "password": "pw"})
    res = client.post("/api/auth/login", json={"username": "user2", "password": "pw"})
    user_id = res.get_json()["data"]["id"]
    pax_id = res.get_json()["data"]["passenger_id"]

    # Book a seat
    res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
        "passenger_id": pax_id,
        "flight_id": "TEST6666",
        "seat_id": "TEST6666_1A"
    })
    assert res.status_code == 201
    booking_id = res.get_json()["data"]["id"]

    # Cancel booking
    res = client.post(f"/api/bookings/{booking_id}/cancel", headers={"X-User-Id": user_id})
    assert res.status_code == 200

    # Try to delete flight
    res = client.delete("/api/admin/flights/TEST6666", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
