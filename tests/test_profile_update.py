import pytest
import time
from utils.database import get_conn, register_user

def test_update_profile(client):
    username = f"testprofile_{int(time.time())}"
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "pwd"
    })

    uid = res.get_json()["data"]["id"]
    pid = res.get_json()["data"]["passenger_id"]

    new_email = f"new_{username}@test.com"
    new_name = "New Name"

    res = client.put(f"/api/passengers/{pid}/profile", headers={"X-User-Id": uid}, json={
        "name": new_name,
        "email": new_email
    })

    assert res.status_code == 200

    # Verify in DB
    with get_conn() as conn:
        pax = conn.execute("SELECT name, email FROM passengers WHERE id=?", (pid,)).fetchone()
        assert pax["name"] == new_name
        assert pax["email"] == new_email

        user = conn.execute("SELECT email FROM users WHERE id=?", (uid,)).fetchone()
        assert user["email"] == new_email

def test_update_profile_email_taken(client):
    u1 = f"u1_{int(time.time())}"
    client.post("/api/auth/register", json={"username": u1, "email": f"{u1}@test.com", "password": "pwd"})

    u2 = f"u2_{int(time.time())}"
    res = client.post("/api/auth/register", json={"username": u2, "email": f"{u2}@test.com", "password": "pwd"})
    u2_id = res.get_json()["data"]["id"]
    u2_pid = res.get_json()["data"]["passenger_id"]

    # Try to change u2's email to u1's email
    res = client.put(f"/api/passengers/{u2_pid}/profile", headers={"X-User-Id": u2_id}, json={
        "name": "Another Name",
        "email": f"{u1}@test.com"
    })

    assert res.status_code == 400
    assert "Email already in use." in res.get_json()["error"]

def test_update_profile_no_user_id(client):
    import time
    from utils.database import register_user, update_passenger_profile, get_conn
    ts = int(time.time() * 1000)
    u1 = register_user(f"user_{ts}", f"user_{ts}@test.com", "pass")

    import uuid
    import datetime
    import pytest
    p_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO passengers (id, name, email, tier, created_at) VALUES (?, ?, ?, ?, ?)",
            (p_id, "Pax No User", f"unique_{ts}@test.com", "Regular", datetime.datetime.now().isoformat())
        )

    try:
        update_passenger_profile(p_id, "Pax No User", f"user_{ts}@test.com")
        pytest.fail("Should not allow updating to an existing user's email")
    except ValueError as e:
        assert "Email already in use" in str(e)

def test_update_profile_no_user_id_pax_conflict(client):
    import time
    from utils.database import register_user, update_passenger_profile, get_conn
    ts = int(time.time() * 1000)

    import uuid
    import datetime
    import pytest
    p_id_1 = str(uuid.uuid4())
    p_id_2 = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO passengers (id, name, email, tier, created_at) VALUES (?, ?, ?, ?, ?)",
            (p_id_1, "Pax No User 1", f"unique1_{ts}@test.com", "Regular", datetime.datetime.now().isoformat())
        )
        conn.execute(
            "INSERT INTO passengers (id, name, email, tier, created_at) VALUES (?, ?, ?, ?, ?)",
            (p_id_2, "Pax No User 2", f"unique2_{ts}@test.com", "Regular", datetime.datetime.now().isoformat())
        )

    try:
        update_passenger_profile(p_id_1, "Pax No User", f"unique2_{ts}@test.com")
        pytest.fail("Should not allow updating to an existing passenger's email")
    except ValueError as e:
        assert "Email already in use" in str(e)
