import pytest
import uuid
import time
from server import app
from utils.database import get_conn, register_user, add_flight, book_multiple_seats, join_waitlist, hash_password

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def data():
    ts = int(time.time() * 1000)

    # 1. Normal user with a passenger profile
    u1_data = register_user(f"u1_{ts}", f"u1_{ts}@test.com", "pass")
    u1_id = u1_data["id"]
    p1_id = u1_data["passenger_id"]

    # 2. Normal user 2
    u2_data = register_user(f"u2_{ts}", f"u2_{ts}@test.com", "pass")
    u2_id = u2_data["id"]
    p2_id = u2_data["passenger_id"]

    # 3. User WITHOUT a passenger profile (insert directly)
    u3_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (id,username,email,password,role,created_at) VALUES (?,?,?,?,?,?)",
            (u3_id, f"u3_{ts}", f"u3_{ts}@test.com", hash_password("pass"), "user", "2023-01-01T00:00:00")
        )

    # 4. Admin user
    u4_data = register_user(f"admin_{ts}", f"admin_{ts}@test.com", "pass")
    u4_id = u4_data["id"]
    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (u4_id,))
        # Remove admin's passenger profile to trigger line 267
        conn.execute("DELETE FROM passengers WHERE user_id=?", (u4_id,))

    # Add flights
    f1 = f"F1_{ts}"
    f2 = f"F2_{ts}"
    add_flight(f1, "JFK", "John F", "LAX", "Los Angeles", "2025-12-01T10:00", "2025-12-01T14:00", "Boeing 737")
    add_flight(f2, "JFK", "John F", "LAX", "Los Angeles", "2025-12-01T10:00", "2025-12-01T14:00", "Boeing 737")

    # Book a seat for user 2 on f1
    with get_conn() as conn:
        seat1 = conn.execute("SELECT id FROM seats WHERE flight_id=? LIMIT 1", (f1,)).fetchone()["id"]
        seat2 = conn.execute("SELECT id FROM seats WHERE flight_id=? LIMIT 1 OFFSET 1", (f1,)).fetchone()["id"]

    b2 = book_multiple_seats(p2_id, f1, [seat1])
    b2_id = b2["bookings"][0]["id"]

    # Put user 2 on waitlist for f2
    join_waitlist(p2_id, f2, "Economy")
    with get_conn() as conn:
        w2_id = conn.execute("SELECT id FROM waitlist WHERE passenger_id=? AND flight_id=?", (p2_id,f2)).fetchone()["id"]

    return {
        "u1": u1_id, "p1": p1_id,
        "u2": u2_id, "p2": p2_id,
        "u3": u3_id,
        "u4_admin": u4_id,
        "fid1": f1,
        "fid2": f2,
        "b2_id": b2_id,
        "w2_id": w2_id,
        "seat2": seat2
    }

def test_api_bookings_no_pax_profile(client, data):
    res = client.get("/api/bookings", headers={"X-User-Id": data["u3"]})
    assert res.status_code == 403
    assert "Passenger profile not found" in res.json["error"]

def test_api_bookings_unauthorized(client, data):
    res = client.get(f"/api/bookings?passenger_id={data['p2']}", headers={"X-User-Id": data["u1"]})
    assert res.status_code == 403
    assert "Not authorized to view bookings for this passenger" in res.json["error"]

def test_api_bookings_admin_no_pax_id(client, data):
    res = client.get("/api/bookings", headers={"X-User-Id": data["u4_admin"]})
    assert res.status_code == 400
    assert "Passenger ID is required for admins to view passenger bookings" in res.json["error"]

def test_api_book_unauthorized(client, data):
    res = client.post("/api/bookings", json={
        "flight_id": data["fid1"],
        "passenger_id": data["p2"],
        "seat_id": data["seat2"]
    }, headers={"X-User-Id": data["u1"]})
    assert res.status_code == 403
    assert "Not authorized to book for this passenger" in res.json["error"]

def test_api_cancel_no_pax_profile(client, data):
    res = client.post(f"/api/bookings/{data['b2_id']}/cancel", headers={"X-User-Id": data["u3"]})
    assert res.status_code == 403
    assert "Passenger profile not found" in res.json["error"]

def test_api_cancel_unauthorized(client, data):
    res = client.post(f"/api/bookings/{data['b2_id']}/cancel", headers={"X-User-Id": data["u1"]})
    assert res.status_code == 403
    assert "Not authorized to cancel this booking" in res.json["error"]

def test_api_upgrade_no_pax_profile(client, data):
    res = client.post(f"/api/bookings/{data['b2_id']}/upgrade", json={"new_seat_id": data["seat2"]}, headers={"X-User-Id": data["u3"]})
    assert res.status_code == 403
    assert "Passenger profile not found" in res.json["error"]

def test_api_upgrade_unauthorized(client, data):
    res = client.post(f"/api/bookings/{data['b2_id']}/upgrade", json={"new_seat_id": data["seat2"]}, headers={"X-User-Id": data["u1"]})
    assert res.status_code == 403
    assert "Not authorized to upgrade this booking" in res.json["error"]

def test_api_waitlist_get_no_pax_profile(client, data):
    res = client.get("/api/waitlist", headers={"X-User-Id": data["u3"]})
    assert res.status_code == 403
    assert "Passenger profile not found" in res.json["error"]

def test_api_join_waitlist_unauthorized(client, data):
    res = client.post("/api/waitlist", json={
        "flight_id": data["fid2"],
        "passenger_id": data["p2"]
    }, headers={"X-User-Id": data["u1"]})
    assert res.status_code == 403
    assert "Not authorized to join waitlist for this passenger" in res.json["error"]

def test_api_remove_waitlist_no_pax_profile(client, data):
    res = client.delete(f"/api/waitlist/{data['w2_id']}", headers={"X-User-Id": data["u3"]})
    assert res.status_code == 403
    assert "Passenger profile not found" in res.json["error"]

def test_api_remove_waitlist_unauthorized(client, data):
    res = client.delete(f"/api/waitlist/{data['w2_id']}", headers={"X-User-Id": data["u1"]})
    assert res.status_code == 403
    assert "Not authorized to remove this waitlist entry" in res.json["error"]
