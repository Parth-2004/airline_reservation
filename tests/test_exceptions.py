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
