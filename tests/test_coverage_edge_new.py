import pytest
import time

def test_api_flight_coverage(client):
    # Test valid flight (this covers `get_flight_stats` indirectly)
    res = client.get("/api/flights/AI101")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["id"] == "AI101"
    assert "stats" in data
    assert "Economy" in data["stats"]
    assert "waitlist" in data["stats"]

def test_cancel_already_cancelled(client):
    # Setup - Register, Login, Book, Cancel, then Cancel again
    username = f"cancel_user_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "pwd"
    })
    res = client.post("/api/auth/login", json={"username": username, "password": "pwd"})
    uid = res.get_json()["data"]["id"]
    pid = res.get_json()["data"]["passenger_id"]

    res = client.get("/api/flights")
    fid = res.get_json()["data"][0]["id"]

    res = client.get(f"/api/flights/{fid}/seats")
    seats = [s for s in res.get_json()["data"] if s["status"] == "available"]
    seat_id = seats[0]["id"]

    # Book
    res = client.post("/api/bookings", headers={"X-User-Id": uid}, json={
        "passenger_id": pid,
        "flight_id": fid,
        "seat_id": seat_id
    })
    bid = res.get_json()["data"]["id"]

    # Cancel once
    res = client.post(f"/api/bookings/{bid}/cancel", headers={"X-User-Id": uid})
    assert res.status_code == 200

    # Cancel again
    res = client.post(f"/api/bookings/{bid}/cancel", headers={"X-User-Id": uid})
    assert res.status_code == 400
    assert "already cancelled" in res.get_json()["error"]

def test_upgrade_invalid_payload(client):
    # Setup - Register, Login, Book, then Upgrade with bad payload
    username = f"upg_user_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "pwd"
    })
    res = client.post("/api/auth/login", json={"username": username, "password": "pwd"})
    uid = res.get_json()["data"]["id"]
    pid = res.get_json()["data"]["passenger_id"]

    res = client.get("/api/flights")
    fid = res.get_json()["data"][0]["id"]

    res = client.get(f"/api/flights/{fid}/seats")
    seats = [s for s in res.get_json()["data"] if s["status"] == "available"]
    seat_id = seats[0]["id"]

    # Book
    res = client.post("/api/bookings", headers={"X-User-Id": uid}, json={
        "passenger_id": pid,
        "flight_id": fid,
        "seat_id": seat_id
    })
    bid = res.get_json()["data"]["id"]

    # Upgrade missing seat_id
    res = client.post(f"/api/bookings/{bid}/upgrade", headers={"X-User-Id": uid}, json={})
    assert res.status_code == 400
    assert "Missing required field" in res.get_json()["error"]

    # Upgrade invalid seat_id
    res = client.post(f"/api/bookings/{bid}/upgrade", headers={"X-User-Id": uid}, json={"seat_id": "NONEXISTENT"})
    assert res.status_code == 400
    assert "Upgrade seat not available" in res.get_json()["error"]

def test_join_waitlist_missing_fields(client):
    username = f"wl_user_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "pwd"
    })
    res = client.post("/api/auth/login", json={"username": username, "password": "pwd"})
    uid = res.get_json()["data"]["id"]
    pid = res.get_json()["data"]["passenger_id"]

    res = client.get("/api/flights")
    fid = res.get_json()["data"][0]["id"]

    # Missing flight_id
    res = client.post("/api/waitlist", headers={"X-User-Id": uid}, json={
        "passenger_id": pid,
        "pref_class": "Economy"
    })
    assert res.status_code == 400
    assert "Missing required field" in res.get_json()["error"]
