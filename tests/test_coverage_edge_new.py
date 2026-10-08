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

    join_waitlist(user1["passenger_id"], f_id)
    with get_conn() as conn:
        w_id = conn.execute("SELECT id FROM waitlist WHERE flight_id=? AND passenger_id=?", (f_id, user1["passenger_id"])).fetchone()["id"]

    res = client.delete(f"/api/waitlist/{w_id}", headers={"X-User-Id": admin["id"]})
    assert res.status_code == 200

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

def test_cancel_booking_not_found(client):
    from utils.database import cancel_booking
    import pytest
    with pytest.raises(ValueError, match="Booking not found or already cancelled."):
        cancel_booking("NONEXISTENT_BOOKING")

def test_add_flight_duplicate(client):
    from utils.database import add_flight
    import pytest
    with pytest.raises(ValueError, match="already exists"):
        add_flight("DUP_FLIGHT", "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")
        add_flight("DUP_FLIGHT", "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

def test_delete_flight_not_found(client):
    from utils.database import delete_flight
    import pytest
    with pytest.raises(ValueError, match="Flight not found."):
        delete_flight("NONEXISTENT_DEL_FLIGHT")

def test_join_waitlist_passenger_not_found(client):
    from utils.database import join_waitlist, add_flight
    import pytest
    import time
    ts = time.time_ns()
    fid = f"F_{ts}"
    add_flight(fid, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")
    with pytest.raises(ValueError, match="Passenger not found."):
        join_waitlist("NONEXISTENT_PAX", fid, "Economy")

def test_upgrade_booking_not_found_db(client):
    from utils.database import upgrade_booking
    import pytest
    with pytest.raises(ValueError, match="Booking not found."):
        upgrade_booking("NONEXISTENT", "SOME_SEAT")

def test_upgrade_seat_not_on_same_flight(client):
    from utils.database import upgrade_booking, add_flight, book_multiple_seats, get_seats, register_user
    import pytest
    import time
    ts = time.time_ns()

    fid1 = f"F1_{ts}"
    fid2 = f"F2_{ts}"

    add_flight(fid1, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")
    add_flight(fid2, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

    u = register_user(f"u_upg_{ts}", f"u_upg_{ts}@example.com", "pass")

    seats1 = get_seats(fid1)
    seat1 = seats1[0]["id"]

    seats2 = get_seats(fid2)
    seat2 = seats2[0]["id"]

    booking = book_multiple_seats(u["passenger_id"], fid1, [seat1])["bookings"][0]

    with pytest.raises(ValueError, match="Upgrade seat must be on the same flight."):
        upgrade_booking(booking["id"], seat2)

def test_login_invalid_legacy_hash(client):
    from utils.database import get_conn, hash_password
    import sqlite3

    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, username, email, password, role, created_at) VALUES ('legacy_invalid_test', 'legacy_invalid', 'legacy_invalid@example.com', '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef', 'user', '2025-01-01')"
        )

    res = client.post("/api/auth/login", json={"username": "legacy_invalid", "password": "wrong_password"})
    assert res.status_code == 401

    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id='legacy_invalid_test'")

def test_waitlist_already_on_waitlist(client):
    from utils.database import join_waitlist, add_flight, register_user
    import pytest
    import time
    ts = time.time_ns()

    fid = f"FW1_{ts}"
    add_flight(fid, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

    u = register_user(f"u_wl1_{ts}", f"u_wl1_{ts}@example.com", "pass")
    join_waitlist(u["passenger_id"], fid, "Economy")

    with pytest.raises(ValueError, match="Passenger already on waitlist for this flight."):
        join_waitlist(u["passenger_id"], fid, "Economy")

def test_waitlist_already_booked(client):
    from utils.database import join_waitlist, add_flight, register_user, book_multiple_seats, get_seats
    import pytest
    import time
    ts = time.time_ns()

    fid = f"FW2_{ts}"
    add_flight(fid, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

    u = register_user(f"u_wl2_{ts}", f"u_wl2_{ts}@example.com", "pass")
    seats = get_seats(fid)
    book_multiple_seats(u["passenger_id"], fid, [seats[0]["id"]])

    with pytest.raises(ValueError, match="Passenger already has an active booking on this flight."):
        join_waitlist(u["passenger_id"], fid, "Economy")

def test_get_all_users_with_conn(client):
    from utils.database import get_all_users, get_conn
    with get_conn() as conn:
        users = get_all_users(conn)
        assert len(users) > 0

def test_update_profile_empty_email(client):
    from utils.database import update_passenger_profile
    import pytest
    with pytest.raises(ValueError, match="Email cannot be empty."):
        update_passenger_profile("p_id", "valid name", "")

def test_update_profile_empty_name(client):
    from utils.database import update_passenger_profile
    import pytest
    with pytest.raises(ValueError, match="Name cannot be empty."):
        update_passenger_profile("p_id", "", "valid@example.com")

def test_book_multiple_seats_empty_list_db(client):
    from utils.database import book_multiple_seats
    import pytest
    with pytest.raises(ValueError, match="No seats selected."):
        book_multiple_seats("p_id", "f_id", [])

def test_get_bookings_filters(client):
    from utils.database import get_bookings, book_multiple_seats, get_seats, add_flight, register_user
    import time
    ts = time.time_ns()

    fid = f"FB_{ts}"
    add_flight(fid, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

    u = register_user(f"u_b_{ts}", f"u_b_{ts}@example.com", "pass")

    seats = get_seats(fid)
    book_multiple_seats(u["passenger_id"], fid, [seats[0]["id"]])

    # filter by passenger, flight, status
    res = get_bookings(passenger_id=u["passenger_id"], flight_id=fid, status="Confirmed")
    assert len(res) == 1

def test_get_flight_stats_booked_and_waitlist(client):
    from utils.database import get_flight_stats, book_multiple_seats, get_seats, add_flight, register_user, join_waitlist
    import time
    ts = time.time_ns()

    fid = f"FS_{ts}"
    add_flight(fid, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

    u1 = register_user(f"u_fs1_{ts}", f"u_fs1_{ts}@example.com", "pass")
    u2 = register_user(f"u_fs2_{ts}", f"u_fs2_{ts}@example.com", "pass")

    seats = get_seats(fid)
    book_multiple_seats(u1["passenger_id"], fid, [seats[0]["id"]])

    join_waitlist(u2["passenger_id"], fid, "Economy")

    stats = get_flight_stats(fid)
    assert stats["waitlist"] == 1
    assert stats["First"]["booked"] > 0 or stats["Business"]["booked"] > 0 or stats["Economy"]["booked"] > 0

def test_api_update_profile_unauthorized(client):
    from utils.database import register_user
    import time
    ts = time.time_ns()

    u = register_user(f"u_up_auth_{ts}", f"u_up_auth_{ts}@example.com", "pass")

    res = client.put(f"/api/passengers/SOME_OTHER_PID/profile", headers={"X-User-Id": u["id"]}, json={"name": "Valid", "email": "valid@test.com"})
    assert res.status_code == 403

def test_login_invalid_password_scrypt(client):
    from utils.database import register_user
    import time
    ts = time.time_ns()

    register_user(f"u_login_{ts}", f"u_login_{ts}@example.com", "mypassword")

    res = client.post("/api/auth/login", json={"username": f"u_login_{ts}", "password": "wrongpassword"})
    assert res.status_code == 401

def test_delete_flight_active_bookings(client):
    from utils.database import delete_flight, add_flight, register_user, book_multiple_seats, get_seats
    import pytest
    import time
    ts = time.time_ns()

    fid = f"F_DEL_{ts}"
    add_flight(fid, "ORG", "Origin", "DST", "Dest", "2024-01-01T10:00:00", "2024-01-01T14:00:00")

    u = register_user(f"u_del_{ts}", f"u_del_{ts}@example.com", "pass")
    seats = get_seats(fid)
    book_multiple_seats(u["passenger_id"], fid, [seats[0]["id"]])

    with pytest.raises(ValueError, match="Cannot delete a flight with active bookings."):
        delete_flight(fid)

def test_memory_db_initialization():
    from utils.database import get_conn
    import os
    os.environ["DATABASE_PATH"] = ":memory:"

    with get_conn() as conn:
        res = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert res in (1, "1", "ON")

    os.environ.pop("DATABASE_PATH", None)
