import pytest

def test_waitlist_invalid_class(client):
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    admin_id = res.get_json()["data"]["id"]
    pax_id = res.get_json()["data"]["passenger_id"]

    res = client.get("/api/flights")
    flight_id = res.get_json()["data"][0]["id"]

    res = client.post("/api/waitlist", headers={"X-User-Id": admin_id}, json={
        "passenger_id": pax_id,
        "flight_id": flight_id,
        "pref_class": "SuperClass"
    })
    assert res.status_code == 400
    assert "Invalid preferred class" in res.get_json()["error"]
