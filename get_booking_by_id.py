def get_booking(booking_id: str):
    from utils.database import get_conn
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        return dict(row) if row else None
