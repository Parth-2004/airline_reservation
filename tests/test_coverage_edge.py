import pytest
import time

def test_book_errors(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    # Book with no seats
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": "test",
        "flight_id": "test"
    })
    assert res.status_code == 400

    # Book non-existent seat
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": "test",
        "flight_id": "test",
        "seat_id": "NONEXISTENT"
    })
    assert res.status_code == 400

def test_delete_missing_flight(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.delete("/api/admin/flights/NONEXISTENT", headers={"X-User-Id": admin_id})
    assert res.status_code == 400

def test_upgrade_errors(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.post("/api/bookings/NONEXISTENT/upgrade", headers={"X-User-Id": admin_id}, json={
        "seat_id": "newseat"
    })
    assert res.status_code == 400

def test_cancel_missing(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    res = client.post("/api/bookings/NONEXISTENT/cancel", headers={"X-User-Id": admin_id})
    assert res.status_code == 400

def test_waitlist_errors(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"]["passenger_id"]

    res = client.post("/api/waitlist", headers={"X-User-Id": admin_id}, json={
        "passenger_id": passenger_id,
        "flight_id": "NONEXISTENT",
        "pref_class": "Economy"
    })
    assert res.status_code == 400
