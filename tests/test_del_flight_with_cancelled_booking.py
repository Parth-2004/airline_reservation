import pytest
import time

def test_del_flight_with_cancelled_booking(client):
    username = f"delcancelltest{time.time_ns()}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    user_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"]["passenger_id"]

    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "DELTEST02",
        "origin": "DEL",
        "origin_full": "Delhi",
        "destination": "BOM",
        "dest_full": "Mumbai",
        "departure_time": "2035-10-10T10:00:00",
        "arrival_time": "2035-10-10T12:00:00",
        "aircraft_model": "Boeing 737",
        "status": "Scheduled"
    })

    flight_id = "DELTEST02"

    res = client.get(f"/api/flights/{flight_id}/seats")
    seat_id = [s["id"] for s in res.get_json()["data"] if s["status"] == "available"][0]

    res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_ids": [seat_id]
    })
    booking_id = res.get_json()["data"]["bookings"][0]["id"]

    res = client.post(f"/api/bookings/{booking_id}/cancel", headers={"X-User-Id": user_id})
    assert res.status_code == 200

    # delete flight as admin
    res = client.delete(f"/api/admin/flights/{flight_id}", headers={"X-User-Id": admin_id})
    assert res.status_code == 200
