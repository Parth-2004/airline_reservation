import pytest
import time

def test_waitlist_double_booking(client):
    # Register user1 and join waitlist
    u1 = f"u1_{int(time.time())}"
    res = client.post("/api/auth/register", json={"username": u1, "email": f"{u1}@test.com", "password": "pw"})
    u1_id = res.get_json()["data"]["id"]
    u1_pax = res.get_json()["data"]["passenger_id"]

    # Register user2 and book a seat
    u2 = f"u2_{int(time.time())}"
    res = client.post("/api/auth/register", json={"username": u2, "email": f"{u2}@test.com", "password": "pw"})
    u2_id = res.get_json()["data"]["id"]
    u2_pax = res.get_json()["data"]["passenger_id"]

    # Get flight
    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    # Get seats
    res = client.get(f"/api/flights/{flight_id}/seats")
    seats = res.get_json()["data"]
    avail_seats = [s for s in seats if s["status"] == "available"]

    seat_1 = avail_seats[0]["id"]
    seat_2 = avail_seats[1]["id"]

    # User 1 joins waitlist (allowed because they have no booking)
    res = client.post("/api/waitlist", headers={"X-User-Id": u1_id}, json={
        "passenger_id": u1_pax,
        "flight_id": flight_id,
        "pref_class": "Economy"
    })
    assert res.status_code == 201

    # User 1 manually books seat_1 (allowed because book_seat doesn't check if already booked or on waitlist)
    res = client.post("/api/bookings", headers={"X-User-Id": u1_id}, json={
        "passenger_id": u1_pax,
        "flight_id": flight_id,
        "seat_id": seat_1
    })
    assert res.status_code == 201

    # User 2 books seat_2
    res = client.post("/api/bookings", headers={"X-User-Id": u2_id}, json={
        "passenger_id": u2_pax,
        "flight_id": flight_id,
        "seat_id": seat_2
    })
    assert res.status_code == 201
    u2_booking = res.get_json()["data"]["id"]

    # Check User 1 bookings count
    res = client.get(f"/api/bookings", headers={"X-User-Id": u1_id})
    assert len(res.get_json()["data"]) == 1

    # User 2 cancels their booking, triggering waitlist processing
    res = client.post(f"/api/bookings/{u2_booking}/cancel", headers={"X-User-Id": u2_id})
    assert res.status_code == 200

    # Check User 1 bookings count again
    res = client.get(f"/api/bookings", headers={"X-User-Id": u1_id})
    print("User 1 Bookings:", res.get_json()["data"])
    assert len(res.get_json()["data"]) == 1, "User 1 should not have two bookings on the same flight!"
