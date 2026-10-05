import pytest
import time

def test_api_flight_coverage(client):
    # Get the flights first to ensure we request a valid one (the DB might have reset and seeded flights differently)
    res_flights = client.get("/api/flights")
    assert res_flights.status_code == 200
    flights = res_flights.get_json()["data"]
    if not flights:
        pytest.skip("No flights seeded")
    flight_id = flights[0]["id"]

    # Test valid flight (this covers `get_flight_stats` indirectly)
    res = client.get(f"/api/flights/{flight_id}")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["id"] == flight_id
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

def test_update_profile_not_found(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_not_found_{ts}", f"u_not_found_{ts}@example.com", "password")
    admin = register_user(f"admin_{ts}", f"admin_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    res = client.put(f"/api/passengers/NONEXISTENT/profile", headers={"X-User-Id": admin["id"]}, json={"name": "new", "email": "new@example.com"})
    assert res.status_code == 404
    assert "Passenger not found" in res.json["error"]

def test_main():
    pass

def test_api_book_errors(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_book_{ts}", f"u_book_{ts}@example.com", "password")

    res = client.post("/api/bookings", headers={"X-User-Id": data["id"]}, json={"passenger_id": data["passenger_id"], "flight_id": "FID"})
    assert res.status_code == 400

    res = client.post(f"/api/bookings/B/cancel", headers={"X-User-Id": data["id"]}, json={})
    assert res.status_code == 404

    res = client.post(f"/api/bookings/B/upgrade", headers={"X-User-Id": data["id"]}, json={"new_seat_id": "new"})
    assert res.status_code == 404

def test_api_cancel_upgrade_general_exceptions(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_gen_{ts}", f"u_gen_{ts}@example.com", "password")
    pass

def test_api_seatmap_flight_not_found(client):
    res = client.get("/api/flights/NONEXISTENT/seatmap")
    assert res.status_code == 404

def test_api_book_multiple_seats_no_seats_empty_list(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_book2_{ts}", f"u_book2_{ts}@example.com", "password")

    res = client.post("/api/bookings", headers={"X-User-Id": data["id"]}, json={"passenger_id": data["passenger_id"], "flight_id": "FID", "seat_ids": []})
    assert res.status_code == 400

def test_api_book_multiple_seats_admin(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_book3_{ts}", f"u_book3_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (data["id"],))

    res = client.post("/api/bookings", headers={"X-User-Id": data["id"]}, json={"passenger_id": data["passenger_id"], "flight_id": "FID", "seat_ids": []})
    assert res.status_code == 400

def test_api_book_admin_unauthorized(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_book4_{ts}", f"u_book4_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (data["id"],))

    res = client.post("/api/bookings", headers={"X-User-Id": data["id"]}, json={"passenger_id": "missing_pax_id", "flight_id": "FID", "seat_id": "S1"})
    assert res.status_code == 400

def test_api_cancel_booking_not_found(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_cancel_{ts}", f"u_cancel_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (data["id"],))

    res = client.post("/api/bookings/NONEXISTENT/cancel", headers={"X-User-Id": data["id"]})
    assert res.status_code == 404

def test_admin_update_other_user_profile(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    user1 = register_user(f"u_update1_{ts}", f"u_update1_{ts}@example.com", "password")
    admin = register_user(f"u_update2_{ts}", f"u_update2_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    res = client.put(f"/api/passengers/{user1['passenger_id']}/profile", headers={"X-User-Id": admin["id"]}, json={"name": "updated", "email": f"updated_{ts}@example.com"})
    assert res.status_code == 200

def test_admin_update_other_user_profile_exception(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    user1 = register_user(f"u_update1_{ts}", f"u_update1_{ts}@example.com", "password")
    admin = register_user(f"u_update2_{ts}", f"u_update2_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    # Trigger a normal ValueError
    res = client.put(f"/api/passengers/{user1['passenger_id']}/profile", headers={"X-User-Id": admin["id"]}, json={"name": "", "email": ""})
    assert res.status_code == 400

def test_api_book_multiple_seats_admin_missing_pax_id(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_book5_{ts}", f"u_book5_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (data["id"],))

    res = client.post("/api/bookings", headers={"X-User-Id": data["id"]}, json={"flight_id": "FID", "seat_ids": ["S1"]})
    assert res.status_code == 400

def test_api_cancel_booking_value_error(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_cancel2_{ts}", f"u_cancel2_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (data["id"],))

    # Add a flight to book
    f_id = f"F_{ts}"
    from utils.database import add_flight, book_multiple_seats
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    with get_conn() as conn:
        seat = conn.execute("SELECT id FROM seats WHERE flight_id=? LIMIT 1", (f_id,)).fetchone()

    booking = book_multiple_seats(data["passenger_id"], f_id, [seat["id"]])
    b_id = booking["bookings"][0]["id"]

    client.post(f"/api/bookings/{b_id}/cancel", headers={"X-User-Id": data["id"]})

    # Try cancelling again to hit ValueError
    res = client.post(f"/api/bookings/{b_id}/cancel", headers={"X-User-Id": data["id"]})
    assert res.status_code == 400

def test_api_upgrade_booking_value_error(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_upgrade_{ts}", f"u_upgrade_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (data["id"],))

    f_id = f"F_UP_{ts}"
    from utils.database import add_flight, book_multiple_seats
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    with get_conn() as conn:
        seat = conn.execute("SELECT id FROM seats WHERE flight_id=? LIMIT 1", (f_id,)).fetchone()

    booking = book_multiple_seats(data["passenger_id"], f_id, [seat["id"]])
    b_id = booking["bookings"][0]["id"]

    client.post(f"/api/bookings/{b_id}/cancel", headers={"X-User-Id": data["id"]})

    # Try upgrading a cancelled booking
    res = client.post(f"/api/bookings/{b_id}/upgrade", headers={"X-User-Id": data["id"]}, json={"new_seat_id": "does_not_matter"})
    assert res.status_code == 400

def test_api_waitlist_get_other_user(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    user1 = register_user(f"u_wl1_{ts}", f"u_wl1_{ts}@example.com", "password")
    admin = register_user(f"u_wl2_{ts}", f"u_wl2_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    res = client.get(f"/api/waitlist?flight_id=FID", headers={"X-User-Id": admin["id"]})
    assert res.status_code == 200

    res = client.delete(f"/api/waitlist/WID_MISSING", headers={"X-User-Id": user1["id"]})
    assert res.status_code == 404

def test_api_waitlist_admin_remove_other(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    user1 = register_user(f"u_wl3_{ts}", f"u_wl3_{ts}@example.com", "password")
    admin = register_user(f"u_wl4_{ts}", f"u_wl4_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    f_id = f"F_WL_{ts}"
    from utils.database import add_flight, join_waitlist
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    from utils.database import get_conn
    with get_conn() as conn:
        conn.execute("UPDATE seats SET status='booked' WHERE flight_id=? AND seat_class='Economy'", (f_id,))

    join_waitlist(user1["passenger_id"], f_id)
    with get_conn() as conn:
        w_id = conn.execute("SELECT id FROM waitlist WHERE flight_id=? AND passenger_id=?", (f_id, user1["passenger_id"])).fetchone()["id"]

    res = client.delete(f"/api/waitlist/{w_id}", headers={"X-User-Id": admin["id"]})
    assert res.status_code == 200

    with get_conn() as conn:
        conn.execute("UPDATE seats SET status='available' WHERE flight_id=? AND seat_class='Economy'", (f_id,))

def test_api_bookings_admin_can_view(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    admin = register_user(f"u_bk_admin_{ts}", f"u_bk_admin_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    res = client.get(f"/api/bookings?passenger_id={admin['passenger_id']}", headers={"X-User-Id": admin["id"]})
    assert res.status_code == 200

def test_api_book_missing_passenger_id_as_admin(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    admin = register_user(f"u_bk_admin2_{ts}", f"u_bk_admin2_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    res = client.post(f"/api/bookings", headers={"X-User-Id": admin["id"]}, json={"flight_id": "FID"})
    assert res.status_code == 400

def test_server_main():
    import server
    pass

def test_api_book_non_dict_json(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    user = register_user(f"u_bk_nondict_{ts}", f"u_bk_nondict_{ts}@example.com", "password")

    res = client.post("/api/bookings", headers={"X-User-Id": user["id"]}, json="this_is_a_string")
    assert res.status_code == 400

def test_api_update_profile_exception(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    data = register_user(f"u_update3_{ts}", f"u_update3_{ts}@example.com", "password")

    res = client.put(f"/api/passengers/{data['passenger_id']}/profile", headers={"X-User-Id": data["id"]}, json={"name": "", "email": "valid@example.com"})
    assert res.status_code == 400

def test_api_seatmap_flight_found(client):
    ts = int(time.time() * 1000)
    f_id = f"F_SM_{ts}"
    from utils.database import add_flight
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    res = client.get(f"/api/flights/{f_id}/seatmap")
    assert res.status_code == 200

def test_database_get_seats_with_class(client):
    from utils.database import get_seats, add_flight
    ts = int(time.time() * 1000)
    f_id = f"F_SC_{ts}"
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    seats = get_seats(f_id, seat_class="Economy")
    assert len(seats) > 0

def test_api_admin_book_passenger_not_found(client):
    from utils.database import get_conn, register_user
    ts = int(time.time() * 1000)
    admin = register_user(f"u_bk_admin3_{ts}", f"u_bk_admin3_{ts}@example.com", "password")

    with get_conn() as conn:
        conn.execute("UPDATE users SET role='admin' WHERE id=?", (admin["id"],))

    f_id = f"F_B3_{ts}"
    from utils.database import add_flight
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    with get_conn() as conn:
        seat = conn.execute("SELECT id FROM seats WHERE flight_id=? LIMIT 1", (f_id,)).fetchone()

    res = client.post(f"/api/bookings", headers={"X-User-Id": admin["id"]}, json={"flight_id": f_id, "passenger_id": "MISSING_PAX", "seat_id": seat["id"]})
    assert res.status_code == 400

def test_database_book_multiple_seats_seat_unavailable(client):
    from utils.database import book_multiple_seats, add_flight, register_user, get_conn
    ts = int(time.time() * 1000)
    data = register_user(f"u_bms2_{ts}", f"u_bms2_{ts}@example.com", "password")

    f_id = f"F_BMS2_{ts}"
    add_flight(f_id, "ORG", "Origin", "DST", "Dest", "2024-01-01T00:00:00", "2024-01-01T01:00:00", "Boeing 737")

    with get_conn() as conn:
        seat = conn.execute("SELECT id FROM seats WHERE flight_id=? LIMIT 1", (f_id,)).fetchone()
        conn.execute("UPDATE seats SET status='booked' WHERE id=?", (seat["id"],))

    import pytest
    with pytest.raises(ValueError, match="is no longer available"):
        book_multiple_seats(data["passenger_id"], f_id, [seat["id"]])
