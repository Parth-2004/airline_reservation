import pytest
import time
from utils.database import get_conn, join_waitlist, get_waitlist, update_passenger_tier

def test_waitlist_priority_update(client):
    username = f"testprio_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "password"
    })
    user_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"]["passenger_id"]

    # Get a flight
    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    # Join waitlist
    res = client.post("/api/waitlist", headers={"X-User-Id": user_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "pref_class": "Economy"
    })
    assert res.status_code == 201

    # Initial priority should be 0
    with get_conn() as conn:
        prio = conn.execute("SELECT priority FROM waitlist WHERE passenger_id=?", (passenger_id,)).fetchone()[0]
    assert prio == 0

    # Admin updates tier to Platinum
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    client.put(f"/api/passengers/{passenger_id}/tier", headers={"X-User-Id": admin_id}, json={"tier": "Platinum"})

    # Check waitlist priority, it should be 2, but currently it remains 0
    with get_conn() as conn:
        new_prio = conn.execute("SELECT priority FROM waitlist WHERE passenger_id=?", (passenger_id,)).fetchone()[0]

    assert new_prio == 2, f"Expected 2, got {new_prio}"

    # Cleanup: remove from waitlist to not affect other tests
    res = client.delete(f"/api/waitlist/{flight_id}", headers={"X-User-Id": user_id})
    # Wait, the endpoint needs the waitlist entry ID, let's fetch it or just use db
    with get_conn() as conn:
        conn.execute("DELETE FROM waitlist WHERE passenger_id=?", (passenger_id,))
