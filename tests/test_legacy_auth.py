import pytest
import time
import uuid
import hashlib
from datetime import datetime
from utils.database import get_conn

def test_legacy_auth_upgrade(client):
    username = f"legacyuser_{int(time.time())}"
    email = f"{username}@example.com"
    password = "legacypassword123"
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()

    with get_conn() as conn:
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id,username,email,password,role,created_at) VALUES (?,?,?,?,?,?)",
            (uid, username, email, legacy_hash, "user", datetime.now().isoformat())
        )
        pid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO passengers (id,user_id,name,email,tier,created_at) VALUES (?,?,?,?,?,?)",
            (pid, uid, username, email, "Regular", datetime.now().isoformat())
        )
        conn.commit()

    # First login, should succeed and upgrade hash
    res = client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    assert res.status_code == 200

    with get_conn() as conn:
        row = conn.execute("SELECT password FROM users WHERE id=?", (uid,)).fetchone()
        assert row["password"] != legacy_hash
        assert row["password"].startswith("scrypt:")

    # Second login, should succeed with the new hash
    res = client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    assert res.status_code == 200
