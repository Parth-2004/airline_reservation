import pytest
import time

def test_missing_flight(client):
    res = client.get("/api/flights/NONEXISTENT")
    assert res.status_code == 404

def test_unauthenticated(client):
    res = client.get("/api/bookings")
    assert res.status_code == 401

    res = client.get("/api/admin/users")
    assert res.status_code == 401

def test_invalid_login(client):
    res = client.post("/api/auth/login", json={"username": "wrong", "password": "wrong"})
    assert res.status_code == 401

def test_invalid_login_none(client):
    res = client.post("/api/auth/login", json={"username": "wrong", "password": None})
    assert res.status_code == 401

def test_invalid_login_missing(client):
    res = client.post("/api/auth/login", json={"username": "wrong"})
    assert res.status_code == 401

def test_invalid_register(client):
    username = f"testuser_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    # Register again
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    assert res.status_code == 400

def test_missing_flight_seatmap(client):
    res = client.get("/api/flights/NONEXISTENT/seatmap")
    assert res.status_code == 404

def test_missing_flight_seats(client):
    res = client.get("/api/flights/NONEXISTENT/seats")
    assert res.status_code == 404

def test_booking_key_error(client):
    username = f"testbooker_keyerr_{int(time.time())}"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    res = client.post("/api/auth/login", json={"username": username, "password": "testpassword123"})
    uid = res.get_json()["data"]["id"]

    # Missing passenger_id
    res = client.post("/api/bookings", headers={"X-User-Id": uid}, json={
        "flight_id": "F1",
        "seat_id": "S1"
    })

    assert res.status_code == 400
    assert "Missing required field" in res.get_json()["error"]
    assert "passenger_id" in res.get_json()["error"]

def test_invalid_register_trailing_spaces(client):
    username = f"testuser_spaces_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": f" {username} ",
        "email": f" {username}@example.com ",
        "password": " testpassword123 "
    })
    assert res.status_code == 201

    res2 = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword123"
    })
    # This should fail because the username was stripped
    assert res2.status_code == 400

def test_add_flight_int_input(client):
    from utils.database import get_conn, hash_password
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id, username, email, password, role, created_at) VALUES ('testadmin', 'testadmin', 'testadmin@test.com', ?, 'admin', '2025-01-01')", (hash_password('admin123'),))

    import time
    resp = client.post("/api/admin/flights", json={
        "_uid": "testadmin",
        "flight_id": int(time.time()),
        "origin": 456,
        "origin_full": 789,
        "destination": 101,
        "dest_full": 112,
        "departure_time": "2025-05-01T10:00:00",
        "arrival_time": "2025-05-01T14:00:00"
    })
    # Assuming valid dates are provided, the strings should be stripped normally
    assert resp.status_code == 201

def test_register_int_input(client):
    import time
    username = int(time.time())
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": 789101112
    })
    assert resp.status_code == 201

def test_login_int_input(client):
    import time
    username = int(time.time())
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test2.com",
        "password": 789101112
    })

    # Try logging in with the user created above
    resp = client.post("/api/auth/login", json={
        "username": username,
        "password": 789101112
    })
    assert resp.status_code == 200
