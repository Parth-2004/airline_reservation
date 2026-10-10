import pytest
def test_login_strips(client):
    res = client.post("/api/auth/login", json={"username": " admin ", "password": "admin123"})
    assert res.status_code == 200
