def test_update_tier_404(client):
    # Login as admin to get auth
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    admin_id = res.get_json()["data"]["id"]

    res = client.put(
        "/api/passengers/INVALID_PID/tier",
        headers={"X-User-Id": admin_id},
        json={"tier": "Gold"}
    )
    assert res.status_code == 404
    assert res.get_json()["ok"] is False
    assert "Passenger not found." in res.get_json()["error"]
