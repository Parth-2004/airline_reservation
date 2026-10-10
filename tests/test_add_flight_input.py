import pytest
from utils.database import add_flight, get_flight
import time

def test_add_flight_strips(client):
    ts = int(time.time_ns())
    fid = f"FL_{ts}"
    add_flight(f" {fid} ", " ny ", "New York ", " la ", " Los Angeles ", "2025-01-01T10:00:00", "2025-01-01T14:00:00")
    f = get_flight(fid)
    assert f is not None
    assert f["origin"] == "NY"
    assert f["origin_full"] == "New York"
    assert f["destination"] == "LA"
    assert f["dest_full"] == "Los Angeles"
