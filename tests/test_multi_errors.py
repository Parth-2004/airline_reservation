import pytest

def test_multi_book_errors(client):
    username = "test_multi_err"
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "pwd"
    })
    res = client.post("/api/auth/login", json={"username": username, "password": "pwd"})
    admin_id = res.get_json()["data"]["id"]
    passenger_id = res.get_json()["data"].get("passenger_id") or "123"

    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    # Book with empty list
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_ids": []
    })
    assert res.status_code == 400

    # Book with more than 9 seats
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_ids": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"]
    })
    assert res.status_code == 400

    # Book with invalid seat
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_ids": ["INVALID_SEAT_ID"]
    })
    assert res.status_code == 400

    # Book already booked seat
    res = client.get(f"/api/flights/{flight_id}/seats")
    available_seats = [s for s in res.get_json()["data"] if s["status"] == "available"]
    seat_id = available_seats[0]["id"]

    # First booking works
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_id": seat_id
    })
    assert res.status_code == 201

    # Second booking fails
    res = client.post("/api/bookings", headers={"X-User-Id": admin_id}, json={
        "passenger_id": passenger_id,
        "flight_id": flight_id,
        "seat_ids": [seat_id]
    })
    assert res.status_code == 400
