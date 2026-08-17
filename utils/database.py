"""
SQLite database layer for AirBook.
Handles: users (auth), passengers, flights, aircraft/seats, bookings, waitlist.
"""
import sqlite3
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "airbook.db")
)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hash_password(pw: str) -> str:
    return generate_password_hash(pw)


# ─── Schema ──────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    username    TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'user',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS passengers (
    id          TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    tier        TEXT NOT NULL DEFAULT 'Regular',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flights (
    id              TEXT PRIMARY KEY,
    origin          TEXT NOT NULL,
    origin_full     TEXT NOT NULL,
    destination     TEXT NOT NULL,
    dest_full       TEXT NOT NULL,
    departure_time  TEXT NOT NULL,
    arrival_time    TEXT NOT NULL,
    aircraft_model  TEXT NOT NULL DEFAULT 'Boeing 737',
    status          TEXT NOT NULL DEFAULT 'Scheduled'
);

CREATE TABLE IF NOT EXISTS seats (
    id          TEXT PRIMARY KEY,
    flight_id   TEXT NOT NULL REFERENCES flights(id) ON DELETE CASCADE,
    row_num     INTEGER NOT NULL,
    col_num     INTEGER NOT NULL,
    seat_class  TEXT NOT NULL,
    label       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'available',
    passenger_id TEXT REFERENCES passengers(id) ON DELETE SET NULL,
    UNIQUE(flight_id, row_num, col_num)
);

CREATE TABLE IF NOT EXISTS bookings (
    id              TEXT PRIMARY KEY,
    passenger_id    TEXT NOT NULL REFERENCES passengers(id),
    flight_id       TEXT NOT NULL REFERENCES flights(id),
    seat_id         TEXT NOT NULL REFERENCES seats(id),
    seat_label      TEXT NOT NULL,
    seat_class      TEXT NOT NULL,
    price           INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Confirmed',
    booked_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS waitlist (
    id              TEXT PRIMARY KEY,
    flight_id       TEXT NOT NULL REFERENCES flights(id) ON DELETE CASCADE,
    passenger_id    TEXT NOT NULL REFERENCES passengers(id) ON DELETE CASCADE,
    pref_class      TEXT NOT NULL DEFAULT 'Economy',
    priority        INTEGER NOT NULL DEFAULT 0,
    added_at        TEXT NOT NULL,
    UNIQUE(flight_id, passenger_id)
);

CREATE INDEX IF NOT EXISTS idx_seats_flight    ON seats(flight_id);
CREATE INDEX IF NOT EXISTS idx_bookings_pax    ON bookings(passenger_id);
CREATE INDEX IF NOT EXISTS idx_bookings_flight ON bookings(flight_id);
CREATE INDEX IF NOT EXISTS idx_waitlist_flight ON waitlist(flight_id);
"""

PRICES = {"First": 30000, "Business": 15000, "Economy": 5000}
LAYOUT = [
    {"seat_class": "First",    "rows": 2,  "cols": 4},
    {"seat_class": "Business", "rows": 4,  "cols": 6},
    {"seat_class": "Economy",  "rows": 14, "cols": 6},
]

AIRCRAFT_LAYOUTS = {
    "Boeing 737":  [{"seat_class":"First","rows":2,"cols":4},{"seat_class":"Business","rows":4,"cols":6},{"seat_class":"Economy","rows":14,"cols":6}],
    "Airbus A320": [{"seat_class":"First","rows":2,"cols":4},{"seat_class":"Business","rows":3,"cols":6},{"seat_class":"Economy","rows":12,"cols":6}],
    "Boeing 777":  [{"seat_class":"First","rows":3,"cols":4},{"seat_class":"Business","rows":6,"cols":6},{"seat_class":"Economy","rows":18,"cols":9}],
    "Airbus A380": [{"seat_class":"First","rows":4,"cols":4},{"seat_class":"Business","rows":8,"cols":6},{"seat_class":"Economy","rows":20,"cols":10}],
}


def init_db():
    """Create schema and seed flights if empty."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)

        # Seed flights if none exist
        if conn.execute("SELECT COUNT(*) FROM flights").fetchone()[0] == 0:
            _seed_flights(conn)

        # Create default admin if no users
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            _seed_admin(conn)


def _seed_admin(conn):
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO users (id,username,email,password,role,created_at) VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), "admin", "admin@airbook.com", hash_password("admin123"), "admin", now)
    )


def _seat_label(row: int, col: int) -> str:
    return f"{row + 1}{chr(65 + col)}"


def _seed_flights(conn):
    base = datetime.now().replace(minute=0, second=0, microsecond=0)

    flights_data = [
        ("AI101", "DEL", "Delhi",     "BOM", "Mumbai",    3,  0,  5,  0),
        ("AI202", "BOM", "Mumbai",    "BLR", "Bangalore", 6,  0,  7, 30),
        ("AI303", "DEL", "Delhi",     "BLR", "Bangalore", 9,  0, 11, 15),
        ("AI404", "MAA", "Chennai",   "DEL", "Delhi",    12,  0, 14, 30),
        ("AI505", "HYD", "Hyderabad", "BOM", "Mumbai",   15,  0, 16, 30),
        ("AI606", "BLR", "Bangalore", "MAA", "Chennai",  18,  0, 19,  0),
    ]

    for fid, orig, orig_full, dest, dest_full, dh, dm, ah, am in flights_data:
        dep = (base + timedelta(hours=dh, minutes=dm)).isoformat()
        arr = (base + timedelta(hours=ah, minutes=am)).isoformat()
        conn.execute(
            "INSERT INTO flights (id,origin,origin_full,destination,dest_full,"
            "departure_time,arrival_time,aircraft_model,status) VALUES (?,?,?,?,?,?,?,?,?)",
            (fid, orig, orig_full, dest, dest_full, dep, arr, "Boeing 737", "Scheduled")
        )
        # Generate seats for this flight
        row_idx = 0
        for seg in LAYOUT:
            for _ in range(seg["rows"]):
                for c in range(seg["cols"]):
                    label = _seat_label(row_idx, c)
                    seat_id = f"{fid}_{label}"
                    conn.execute(
                        "INSERT INTO seats (id,flight_id,row_num,col_num,seat_class,label,status)"
                        " VALUES (?,?,?,?,?,?,?)",
                        (seat_id, fid, row_idx, c, seg["seat_class"], label, "available")
                    )
                row_idx += 1


def add_flight(flight_id: str, origin: str, origin_full: str,
               destination: str, dest_full: str,
               departure_time: str, arrival_time: str,
               aircraft_model: str = "Boeing 737") -> dict:
    """Admin: add a new flight and auto-generate its seats."""
    with get_conn() as conn:
        # Validate no duplicate
        if conn.execute("SELECT id FROM flights WHERE id=?", (flight_id,)).fetchone():
            raise ValueError(f"Flight ID '{flight_id}' already exists.")

        conn.execute(
            "INSERT INTO flights (id,origin,origin_full,destination,dest_full,"
            "departure_time,arrival_time,aircraft_model,status) VALUES (?,?,?,?,?,?,?,?,?)",
            (flight_id, origin.upper(), origin_full, destination.upper(), dest_full,
             departure_time, arrival_time, aircraft_model, "Scheduled")
        )

        layout = AIRCRAFT_LAYOUTS.get(aircraft_model, AIRCRAFT_LAYOUTS["Boeing 737"])
        row_idx = 0
        seat_count = 0
        for seg in layout:
            for _ in range(seg["rows"]):
                for c in range(seg["cols"]):
                    label = _seat_label(row_idx, c)
                    seat_id = f"{flight_id}_{label}"
                    conn.execute(
                        "INSERT INTO seats (id,flight_id,row_num,col_num,seat_class,label,status)"
                        " VALUES (?,?,?,?,?,?,?)",
                        (seat_id, flight_id, row_idx, c, seg["seat_class"], label, "available")
                    )
                    seat_count += 1
                row_idx += 1

        return {"flight_id": flight_id, "seats_created": seat_count, "aircraft": aircraft_model}


def delete_flight(flight_id: str):
    """Admin: remove a flight (cascades to seats, waitlist)."""
    with get_conn() as conn:
        flight = conn.execute("SELECT id FROM flights WHERE id=?", (flight_id,)).fetchone()
        if not flight:
            raise ValueError("Flight not found.")
        if conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE flight_id=? AND status!='Cancelled'",
            (flight_id,)
        ).fetchone()[0] > 0:
            raise ValueError("Cannot delete a flight with active bookings.")
        conn.execute("DELETE FROM flights WHERE id=?", (flight_id,))


# ─── Auth ─────────────────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str, role: str = "user") -> dict:
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username=? OR email=?", (username, email)
        ).fetchone()
        if existing:
            raise ValueError("Username or email already exists.")
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id,username,email,password,role,created_at) VALUES (?,?,?,?,?,?)",
            (uid, username, email, hash_password(password), role, datetime.now().isoformat())
        )
        # Auto-create passenger profile
        pid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO passengers (id,user_id,name,email,tier,created_at) VALUES (?,?,?,?,?,?)",
            (pid, uid, username, email, "Regular", datetime.now().isoformat())
        )
        return {"id": uid, "username": username, "email": email, "role": role, "passenger_id": pid}


def login_user(username: str, password: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE (username=? OR email=?)",
            (username, username)
        ).fetchone()
        if not row:
            raise ValueError("Invalid credentials.")

        stored_password = row["password"]

        # Check if the stored password is a legacy SHA-256 hash (64 hex characters)
        if len(stored_password) == 64 and all(c in '0123456789abcdefABCDEF' for c in stored_password):
            if hashlib.sha256(password.encode()).hexdigest() != stored_password:
                raise ValueError("Invalid credentials.")

            # Upgrade the hash to scrypt
            new_hash = generate_password_hash(password)
            conn.execute("UPDATE users SET password=? WHERE id=?", (new_hash, row["id"]))
        elif not check_password_hash(stored_password, password):
            raise ValueError("Invalid credentials.")

        # Get passenger profile
        pax = conn.execute(
            "SELECT id, tier FROM passengers WHERE user_id=?", (row["id"],)
        ).fetchone()
        return {
            "id": row["id"], "username": row["username"],
            "email": row["email"], "role": row["role"],
            "passenger_id": pax["id"] if pax else None,
            "tier": pax["tier"] if pax else "Regular",
        }


def get_all_users(conn=None):
    def _run(c):
        return [dict(r) for r in c.execute(
            "SELECT u.id,u.username,u.email,u.role,u.created_at,"
            "p.id as passenger_id, p.tier "
            "FROM users u LEFT JOIN passengers p ON p.user_id=u.id ORDER BY u.created_at DESC"
        ).fetchall()]
    if conn:
        return _run(conn)
    with get_conn() as c:
        return _run(c)


# ─── Passengers ───────────────────────────────────────────────────────────────

def get_all_passengers():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM passengers ORDER BY name"
        ).fetchall()]


def update_passenger_tier(passenger_id: str, tier: str):
    with get_conn() as conn:
        conn.execute("UPDATE passengers SET tier=? WHERE id=?", (tier, passenger_id))


# ─── Flights ──────────────────────────────────────────────────────────────────

def get_all_flights():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM flights ORDER BY departure_time").fetchall()
        return [dict(r) for r in rows]


def get_flight(flight_id: str):
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM flights WHERE id=?", (flight_id,)).fetchone()
        return dict(r) if r else None


def get_seats(flight_id: str, seat_class: str = None):
    with get_conn() as conn:
        if seat_class:
            rows = conn.execute(
                "SELECT * FROM seats WHERE flight_id=? AND seat_class=? ORDER BY row_num,col_num",
                (flight_id, seat_class)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM seats WHERE flight_id=? ORDER BY row_num,col_num",
                (flight_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def get_seat_map(flight_id: str):
    """Returns seats grouped by row for frontend rendering."""
    seats = get_seats(flight_id)
    rows = {}
    for s in seats:
        rows.setdefault(s["row_num"], []).append(s)
    return [rows[k] for k in sorted(rows)]


def get_flight_stats(flight_id: str):
    with get_conn() as conn:
        stats = {}
        for cls in ["First", "Business", "Economy"]:
            total = conn.execute(
                "SELECT COUNT(*) FROM seats WHERE flight_id=? AND seat_class=?",
                (flight_id, cls)
            ).fetchone()[0]
            booked = conn.execute(
                "SELECT COUNT(*) FROM seats WHERE flight_id=? AND seat_class=? AND status='booked'",
                (flight_id, cls)
            ).fetchone()[0]
            stats[cls] = {"total": total, "booked": booked, "available": total - booked,
                          "pct": round(booked / total * 100, 1) if total else 0}
        wl = conn.execute(
            "SELECT COUNT(*) FROM waitlist WHERE flight_id=?", (flight_id,)
        ).fetchone()[0]
        stats["waitlist"] = wl
        return stats


# ─── Bookings ─────────────────────────────────────────────────────────────────

BOOK_COUNTER = [1]


def book_seat(passenger_id: str, flight_id: str, seat_id: str) -> dict:
    with get_conn() as conn:
        seat = conn.execute(
            "SELECT * FROM seats WHERE id=? AND flight_id=?", (seat_id, flight_id)
        ).fetchone()
        if not seat or seat["status"] != "available":
            raise ValueError("Seat is not available.")

        bid = f"BK{str(uuid.uuid4())[:6].upper()}"
        price = PRICES.get(seat["seat_class"], 5000)
        now = datetime.now().isoformat()

        conn.execute("UPDATE seats SET status='booked', passenger_id=? WHERE id=?",
                     (passenger_id, seat_id))
        conn.execute(
            "INSERT INTO bookings (id,passenger_id,flight_id,seat_id,seat_label,"
            "seat_class,price,status,booked_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (bid, passenger_id, flight_id, seat_id, seat["label"],
             seat["seat_class"], price, "Confirmed", now)
        )
        return {"id": bid, "seat_label": seat["label"], "seat_class": seat["seat_class"],
                "price": price, "status": "Confirmed"}


def book_multiple_seats(passenger_id: str, flight_id: str, seat_ids: list) -> dict:
    """Book multiple seats at once for a single passenger on a single flight.
    All seats are booked atomically — if any fail, none are booked."""
    if not seat_ids:
        raise ValueError("No seats selected.")
    if len(seat_ids) > 9:
        raise ValueError("Cannot book more than 9 seats at once.")

    with get_conn() as conn:
        bookings = []
        total_price = 0
        now = datetime.now().isoformat()

        for seat_id in seat_ids:
            seat = conn.execute(
                "SELECT * FROM seats WHERE id=? AND flight_id=?", (seat_id, flight_id)
            ).fetchone()
            if not seat:
                raise ValueError(f"Seat {seat_id} not found on flight {flight_id}.")
            if seat["status"] != "available":
                raise ValueError(f"Seat {seat['label']} is no longer available.")

            bid = f"BK{str(uuid.uuid4())[:6].upper()}"
            price = PRICES.get(seat["seat_class"], 5000)
            total_price += price

            conn.execute("UPDATE seats SET status='booked', passenger_id=? WHERE id=?",
                         (passenger_id, seat_id))
            conn.execute(
                "INSERT INTO bookings (id,passenger_id,flight_id,seat_id,seat_label,"
                "seat_class,price,status,booked_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (bid, passenger_id, flight_id, seat_id, seat["label"],
                 seat["seat_class"], price, "Confirmed", now)
            )
            bookings.append({
                "id": bid, "seat_label": seat["label"],
                "seat_class": seat["seat_class"], "price": price, "status": "Confirmed"
            })

        return {"bookings": bookings, "total_seats": len(bookings), "total_price": total_price}


def get_bookings(passenger_id: str = None, flight_id: str = None, status: str = None):
    with get_conn() as conn:
        q = """SELECT b.*, p.name as passenger_name, p.tier as passenger_tier,
                      f.origin, f.destination, f.departure_time
               FROM bookings b
               JOIN passengers p ON p.id = b.passenger_id
               JOIN flights f ON f.id = b.flight_id
               WHERE 1=1"""
        params = []
        if passenger_id:
            q += " AND b.passenger_id=?"; params.append(passenger_id)
        if flight_id:
            q += " AND b.flight_id=?"; params.append(flight_id)
        if status:
            q += " AND b.status=?"; params.append(status)
        q += " ORDER BY b.booked_at DESC"
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def cancel_booking(booking_id: str) -> dict:
    with get_conn() as conn:
        b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not b or b["status"] == "Cancelled":
            raise ValueError("Booking not found or already cancelled.")

        # Free the seat
        conn.execute("UPDATE seats SET status='available', passenger_id=NULL WHERE id=?",
                     (b["seat_id"],))
        conn.execute("UPDATE bookings SET status='Cancelled' WHERE id=?", (booking_id,))
        freed_class = b["seat_class"]

        # Process waitlist
        wl_entry = conn.execute(
            "SELECT w.*, p.name, p.tier FROM waitlist w "
            "JOIN passengers p ON p.id=w.passenger_id "
            "WHERE w.flight_id=? ORDER BY w.priority DESC, w.added_at ASC LIMIT 1",
            (b["flight_id"],)
        ).fetchone()
        auto_booking = None
        if wl_entry:
            avail = conn.execute(
                "SELECT * FROM seats WHERE flight_id=? AND seat_class=? AND status='available' LIMIT 1",
                (b["flight_id"], wl_entry["pref_class"])
            ).fetchone()
            if not avail:
                avail = conn.execute(
                    "SELECT * FROM seats WHERE flight_id=? AND seat_class=? AND status='available' LIMIT 1",
                    (b["flight_id"], freed_class)
                ).fetchone()
            if avail:
                bid = f"BK{str(uuid.uuid4())[:6].upper()}"
                price = PRICES.get(avail["seat_class"], 5000)
                now = datetime.now().isoformat()
                conn.execute("UPDATE seats SET status='booked', passenger_id=? WHERE id=?",
                             (wl_entry["passenger_id"], avail["id"]))
                conn.execute(
                    "INSERT INTO bookings (id,passenger_id,flight_id,seat_id,seat_label,"
                    "seat_class,price,status,booked_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (bid, wl_entry["passenger_id"], b["flight_id"], avail["id"],
                     avail["label"], avail["seat_class"], price, "Confirmed", now)
                )
                conn.execute("DELETE FROM waitlist WHERE id=?", (wl_entry["id"],))
                auto_booking = {
                    "booking_id": bid, "passenger": wl_entry["name"],
                    "seat": avail["label"], "seat_class": avail["seat_class"]
                }

        return {"cancelled": booking_id, "auto_assigned": auto_booking}


def upgrade_booking(booking_id: str, new_seat_id: str) -> dict:
    with get_conn() as conn:
        b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not b or b["status"] == "Cancelled":
            raise ValueError("Booking not found.")
        new_seat = conn.execute(
            "SELECT * FROM seats WHERE id=? AND status='available'", (new_seat_id,)
        ).fetchone()
        if not new_seat:
            raise ValueError("Upgrade seat not available.")
        if new_seat["flight_id"] != b["flight_id"]:
            raise ValueError("Upgrade seat must be on the same flight.")

        old_label = b["seat_label"]
        old_seat_id = b["seat_id"]
        old_class = b["seat_class"]

        conn.execute("UPDATE seats SET status='available', passenger_id=NULL WHERE id=?", (old_seat_id,))
        conn.execute("UPDATE seats SET status='booked', passenger_id=? WHERE id=?",
                     (b["passenger_id"], new_seat_id))
        conn.execute(
            "UPDATE bookings SET seat_id=?, seat_label=?, seat_class=?, price=?, status='Upgraded' WHERE id=?",
            (new_seat_id, new_seat["label"], new_seat["seat_class"],
             PRICES.get(new_seat["seat_class"], 5000), booking_id)
        )
        return {"old_seat": old_label, "new_seat": new_seat["label"],
                "new_class": new_seat["seat_class"],
                "new_price": PRICES.get(new_seat["seat_class"], 5000)}


# ─── Waitlist ──────────────────────────────────────────────────────────────────

TIER_PRIORITY = {"Regular": 0, "Gold": 1, "Platinum": 2}


def join_waitlist(passenger_id: str, flight_id: str, pref_class: str = "Economy"):
    with get_conn() as conn:
        flight = conn.execute("SELECT id FROM flights WHERE id=?", (flight_id,)).fetchone()
        if not flight:
            raise ValueError("Flight not found.")

        # Check not already in waitlist
        if conn.execute(
            "SELECT id FROM waitlist WHERE flight_id=? AND passenger_id=?",
            (flight_id, passenger_id)
        ).fetchone():
            raise ValueError("Passenger already on waitlist for this flight.")
        # Check no active booking
        if conn.execute(
            "SELECT id FROM bookings WHERE passenger_id=? AND flight_id=? AND status!='Cancelled'",
            (passenger_id, flight_id)
        ).fetchone():
            raise ValueError("Passenger already has an active booking on this flight.")

        pax = conn.execute("SELECT tier FROM passengers WHERE id=?", (passenger_id,)).fetchone()
        if not pax:
            raise ValueError("Passenger not found.")
        priority = TIER_PRIORITY.get(pax["tier"], 0)
        conn.execute(
            "INSERT INTO waitlist (id,flight_id,passenger_id,pref_class,priority,added_at)"
            " VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), flight_id, passenger_id, pref_class, priority,
             datetime.now().isoformat())
        )


def get_waitlist(flight_id: str = None):
    with get_conn() as conn:
        q = """SELECT w.*, p.name as passenger_name, p.tier as passenger_tier,
                      f.origin, f.destination
               FROM waitlist w
               JOIN passengers p ON p.id=w.passenger_id
               JOIN flights f ON f.id=w.flight_id
               WHERE 1=1"""
        params = []
        if flight_id:
            q += " AND w.flight_id=?"; params.append(flight_id)
        q += " ORDER BY w.flight_id, w.priority DESC, w.added_at ASC"
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def remove_from_waitlist(waitlist_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM waitlist WHERE id=?", (waitlist_id,))


# ─── Reports ──────────────────────────────────────────────────────────────────

def get_dashboard_stats():
    with get_conn() as conn:
        total_flights   = conn.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
        total_passengers= conn.execute("SELECT COUNT(*) FROM passengers").fetchone()[0]
        total_users     = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_bookings = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE status!='Cancelled'"
        ).fetchone()[0]
        total_revenue   = conn.execute(
            "SELECT COALESCE(SUM(price),0) FROM bookings WHERE status!='Cancelled'"
        ).fetchone()[0]
        waitlist_total  = conn.execute("SELECT COUNT(*) FROM waitlist").fetchone()[0]
        recent = conn.execute("""
            SELECT b.id, b.seat_label, b.seat_class, b.price, b.status, b.booked_at,
                   p.name as passenger_name, f.id as flight_id,
                   f.origin, f.destination
            FROM bookings b
            JOIN passengers p ON p.id=b.passenger_id
            JOIN flights f ON f.id=b.flight_id
            ORDER BY b.booked_at DESC LIMIT 8
        """).fetchall()
        return {
            "total_flights": total_flights,
            "total_passengers": total_passengers,
            "total_users": total_users,
            "active_bookings": active_bookings,
            "total_revenue": total_revenue,
            "waitlist_total": waitlist_total,
            "recent_bookings": [dict(r) for r in recent],
        }


def get_revenue_report():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT seat_class, SUM(price) as revenue, COUNT(*) as count
            FROM bookings WHERE status!='Cancelled'
            GROUP BY seat_class
        """).fetchall()
        return [dict(r) for r in rows]


def get_occupancy_report():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT f.id, f.origin, f.destination, f.departure_time,
                   COUNT(s.id) as total_seats,
                   SUM(CASE WHEN s.status='booked' THEN 1 ELSE 0 END) as booked_seats
            FROM flights f
            JOIN seats s ON s.flight_id=f.id
            GROUP BY f.id
            ORDER BY f.departure_time
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["pct"] = round(d["booked_seats"] / d["total_seats"] * 100, 1) if d["total_seats"] else 0
            result.append(d)
        return result
