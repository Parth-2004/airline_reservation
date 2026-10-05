import pytest
import time

def test_waitlist_class_logic(client):
    from utils.database import get_conn
    with get_conn() as conn:
        conn.execute("UPDATE seats SET status='available' WHERE status='booked'")
        conn.execute("DELETE FROM waitlist")
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

    # Book all First class seats so they are forced into the waitlist
    res = client.get(f"/api/flights/{flight_id}/seats")
    available_seats = [s for s in res.get_json()["data"] if s["status"] == "available"]

    from utils.database import get_conn
    with get_conn() as conn:
        conn.execute("UPDATE seats SET status='booked' WHERE flight_id=? AND seat_class='First'", (flight_id,))

    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]
    admin_pax = res.get_json()["data"]["passenger_id"]

    # User joins waitlist for First class
    res = client.post("/api/waitlist", headers={"X-User-Id": user_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "pref_class": "First"
    })
    assert res.status_code == 201

    # We book an Economy seat and then cancel it. The user should NOT get auto-assigned to Economy.
    econ_seat = next(s for s in available_seats if s["seat_class"] == "Economy")

    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": admin_pax,
        "flight_id": flight_id,
        "seat_id": econ_seat["id"]
    })
    booking_id = res.get_json()["data"]["id"]

    # Cancel the Economy booking
    res = client.post(f"/api/bookings/{booking_id}/cancel", headers={"X-User-Id": admin_id})
    cancel_data = res.get_json()["data"]

    # It should not have auto-assigned the First-class waitlist user to the Economy seat.
    try:
        if "auto_assigned" in cancel_data and cancel_data["auto_assigned"] is not None:
            assert cancel_data["auto_assigned"]["passenger"] != username
    finally:
        with get_conn() as conn:
            conn.execute("UPDATE seats SET status='available' WHERE flight_id=? AND seat_class='First'", (flight_id,))
