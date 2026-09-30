import pytest
from utils.database import init_db, _seed_flights, _seed_admin, get_conn, SCHEMA

def test_db_init_seeds():
    # Force empty tables to test seed functions
    with get_conn() as conn:
        conn.execute("DELETE FROM bookings")
        conn.execute("DELETE FROM waitlist")
        conn.execute("DELETE FROM seats")
        conn.execute("DELETE FROM flights")
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM passengers")

    # Running init_db again should call _seed_flights and _seed_admin
    init_db()

    with get_conn() as conn:
        f_count = conn.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
        assert f_count > 0
        u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert u_count > 0
