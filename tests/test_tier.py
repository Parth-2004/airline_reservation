import pytest

def test_update_tier_invalid(client):
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    admin_id = res.get_json()["data"]["id"]

    res = client.get("/api/passengers", headers={"X-User-Id": admin_id})
    pax_id = res.get_json()["data"][0]["id"]

    res = client.put(f"/api/passengers/{pax_id}/tier", headers={"X-User-Id": admin_id}, json={"tier": "SuperPlatinum"})
    assert res.status_code == 400
    assert res.get_json()["ok"] is False
    assert "Invalid tier" in res.get_json()["error"]
