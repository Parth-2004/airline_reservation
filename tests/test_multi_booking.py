import pytest
import time

def test_book_multiple_seats(client):
    username = f"testmultibook_{int(time.time())}"
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

    if len(available_seats) >= 2:
        seat_ids = [available_seats[0]["id"], available_seats[1]["id"]]

        res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "seat_ids": seat_ids
        })
        assert res.status_code == 201

        # Verify bookings
        res = client.get(f"/api/bookings?passenger_id={passenger_id}", headers={"X-User-Id": user_id})
        assert res.status_code == 200
        bookings = res.get_json()["data"]
        assert len(bookings) == 2

        booking_ids = [b["id"] for b in bookings]

        # Cancel one of them to get coverage for cancel waitlist
        res = client.post(f"/api/bookings/{booking_ids[0]}/cancel", headers={"X-User-Id": user_id})
        assert res.status_code == 200
