def test_non_api_error(client):
    res = client.post("/nonexistent")
    assert res.status_code == 404
    assert not res.is_json
