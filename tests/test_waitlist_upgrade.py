import pytest
import time

def test_waitlist(client):
    username = f"testwaitlist_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    user_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"]["passenger_id"]

    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    # Join waitlist
    res = client.post("/api/waitlist", headers={"X-User-Id": user_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "pref_class": "Economy"
    })
    assert res.status_code == 201

    # Get waitlist
    res = client.get(f"/api/waitlist?flight_id={flight_id}", headers={"X-User-Id": user_id})
    assert res.status_code == 200
    waitlist = res.get_json()["data"]
    assert len(waitlist) > 0
    waitlist_id = waitlist[0]["id"]

    # Remove waitlist
    res = client.delete(f"/api/waitlist/{waitlist_id}", headers={"X-User-Id": user_id})
    assert res.status_code == 200

def test_upgrade(client):
    username = f"testupgrade_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    user_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"]["passenger_id"]

    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    res = client.get(f"/api/flights/{flight_id}/seats")
    available_seats = [s for s in res.get_json()["data"] if s["status"] == "available"]

    if len(available_seats) >= 2:
        seat_id = available_seats[0]["id"]
        upgrade_seat_id = available_seats[1]["id"]

        # Book seat
        res = client.post("/api/bookings", headers={"X-User-Id": user_id}, json={
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "seat_id": seat_id
        })
        booking_id = res.get_json()["data"]["id"]

        # Upgrade seat
        res = client.post(f"/api/bookings/{booking_id}/upgrade", headers={"X-User-Id": user_id}, json={
            "seat_id": upgrade_seat_id
        })
        assert res.status_code == 200
