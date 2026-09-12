import pytest
from server import app
from utils.database import get_conn

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_admin_book_invalid_pax(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_id = res.get_json()["data"]["id"]

    # Add flight
    res = client.post("/api/admin/flights", headers={"X-User-Id": admin_id}, json={
        "flight_id": "TESTINVALIDPAX",
        "origin": "JFK",
        "origin_full": "New York",
        "destination": "LHR",
        "dest_full": "London",
        "departure_time": "2024-12-01T10:00:00",
        "arrival_time": "2024-12-01T22:00:00",
        "aircraft_model": "Boeing 737"
    })

    # Try booking
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": "nonexistent",
        "flight_id": "TESTINVALIDPAX",
        "seat_id": "TESTINVALIDPAX_1A"
    })
    assert res.status_code == 400
    assert "Passenger not found" in res.get_json()["error"]

    # Try multi booking
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": "nonexistent",
        "flight_id": "TESTINVALIDPAX",
        "seat_ids": ["TESTINVALIDPAX_1A", "TESTINVALIDPAX_1B"]
    })
    assert res.status_code == 400
    assert "Passenger not found" in res.get_json()["error"]
