"""
AirBook Flask Backend
Serves: REST API + static frontend files
Run:    python server.py
"""
import os, sys, json, functools
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory, session
from utils.database import (
    init_db, get_conn,
    register_user, login_user, get_all_users, get_passenger_by_user,
    get_all_passengers, update_passenger_tier,
    get_all_flights, get_flight, get_seats, get_seat_map, get_flight_stats,
    add_flight, delete_flight, AIRCRAFT_LAYOUTS,
    book_seat, book_multiple_seats, get_bookings, cancel_booking, upgrade_booking,
    join_waitlist, get_waitlist, remove_from_waitlist,
    get_dashboard_stats, get_revenue_report, get_occupancy_report,
)

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("AIRBOOK_SECRET", "airbook-dev-secret-2024")

# ─── CORS helper ─────────────────────────────────────────────────────────────

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id, X-Role"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response

@app.route("/<path:p>", methods=["OPTIONS"])
@app.route("/", methods=["OPTIONS"])
def options_handler(*args, **kwargs):
    return jsonify({}), 200

# ─── Auth helpers ─────────────────────────────────────────────────────────────

def ok(data=None, **kw):
    return jsonify({"ok": True, "data": data, **kw})

def err(msg, code=400):
    return jsonify({"ok": False, "error": str(msg)}), code

def require_login(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
        if not uid:
            return err("Not authenticated.", 401)
        with get_conn() as conn:
            row = conn.execute("SELECT id FROM users WHERE id=?", (uid,)).fetchone()
            if not row:
                return err("Invalid session or user not found.", 401)
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
        if not uid:
            return err("Not authenticated.", 401)
        with get_conn() as conn:
            row = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
            if not row or row["role"] != "admin":
                return err("Admin access required.", 403)
        return f(*args, **kwargs)
    return wrapper

# ─── Static frontend ──────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route("/login")
def serve_login():
    return send_from_directory("static", "login.html")

@app.route("/admin")
def serve_admin():
    return send_from_directory("static", "admin.html")

# ─── Auth endpoints ───────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    d = request.json or {}
    try:
        user = register_user(d.get("username",""), d.get("email",""), d.get("password",""))
        return ok(user), 201
    except ValueError as e:
        return err(e)

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    d = request.json or {}
    try:
        user = login_user(d.get("username",""), d.get("password",""))
        return ok(user)
    except ValueError as e:
        return err(e, 401)

# ─── Admin: Users ─────────────────────────────────────────────────────────────

@app.route("/api/admin/users", methods=["GET"])
@require_admin
def api_users():
    return ok(get_all_users())

@app.route("/api/admin/stats", methods=["GET"])
@require_admin
def api_admin_stats():
    return ok(get_dashboard_stats())

@app.route("/api/admin/revenue", methods=["GET"])
@require_admin
def api_revenue():
    return ok(get_revenue_report())

@app.route("/api/admin/occupancy", methods=["GET"])
@require_admin
def api_occupancy():
    return ok(get_occupancy_report())

@app.route("/api/admin/bookings", methods=["GET"])
@require_admin
def api_all_bookings():
    return ok(get_bookings())

@app.route("/api/admin/aircraft-models", methods=["GET"])
@require_admin
def api_aircraft_models():
    return ok(list(AIRCRAFT_LAYOUTS.keys()))

# ─── Admin: Flight Management ──────────────────────────────────────────────────

@app.route("/api/admin/flights", methods=["POST"])
@require_admin
def api_add_flight():
    d = request.json or {}
    try:
        result = add_flight(
            flight_id      = d.get("flight_id","").strip().upper(),
            origin         = d.get("origin","").strip(),
            origin_full    = d.get("origin_full","").strip(),
            destination    = d.get("destination","").strip(),
            dest_full      = d.get("dest_full","").strip(),
            departure_time = d.get("departure_time",""),
            arrival_time   = d.get("arrival_time",""),
            aircraft_model = d.get("aircraft_model","Boeing 737"),
        )
        return ok(result), 201
    except ValueError as e:
        return err(e)

@app.route("/api/admin/flights/<fid>", methods=["DELETE"])
@require_admin
def api_delete_flight(fid):
    try:
        delete_flight(fid)
        return ok({"deleted": fid})
    except ValueError as e:
        return err(e)

# ─── Passengers ───────────────────────────────────────────────────────────────

@app.route("/api/passengers", methods=["GET"])
@require_admin
def api_passengers():
    return ok(get_all_passengers())

@app.route("/api/passengers/<pid>/tier", methods=["PUT"])
@require_admin
def api_update_tier(pid):
    d = request.json or {}
    update_passenger_tier(pid, d.get("tier","Regular"))
    return ok({"passenger_id": pid})

# ─── Flights ──────────────────────────────────────────────────────────────────

@app.route("/api/flights", methods=["GET"])
def api_flights():
    flights = get_all_flights()
    result = []
    for f in flights:
        stats = get_flight_stats(f["id"])
        f["stats"] = stats
        result.append(f)
    return ok(result)

@app.route("/api/flights/<fid>", methods=["GET"])
def api_flight(fid):
    f = get_flight(fid)
    if not f:
        return err("Flight not found.", 404)
    f["stats"] = get_flight_stats(fid)
    return ok(f)

@app.route("/api/flights/<fid>/seatmap", methods=["GET"])
def api_seatmap(fid):
    return ok(get_seat_map(fid))

@app.route("/api/flights/<fid>/seats", methods=["GET"])
def api_seats(fid):
    cls = request.args.get("class")
    return ok(get_seats(fid, cls))

# ─── Bookings ─────────────────────────────────────────────────────────────────

@app.route("/api/bookings", methods=["GET"])
@require_login
def api_bookings():
    uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
    pax = get_passenger_by_user(uid)

    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
        is_admin = user and user["role"] == "admin"

    pax_id   = request.args.get("passenger_id")
    fid      = request.args.get("flight_id")
    status   = request.args.get("status")

    if not pax and not is_admin:
        return err("Passenger profile not found.", 403)

    if not is_admin and (pax_id and pax_id != pax["id"]):
        return err("Not authorized to view bookings for this passenger.", 403)

    # Force the query to only return the logged in user's bookings (or the requested passenger if admin)
    if not is_admin or not pax_id:
        if not pax:
            return err("Passenger ID is required for admins to view passenger bookings.", 400)
        pax_id = pax["id"]

    return ok(get_bookings(pax_id, fid, status))

@app.route("/api/bookings", methods=["POST"])
@require_login
def api_book():
    d = request.json or {}
    try:
        uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
        pax = get_passenger_by_user(uid)

        with get_conn() as conn:
            user = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
            is_admin = user and user["role"] == "admin"

        seat_ids = d.get("seat_ids")          # multi-seat: list
        seat_id  = d.get("seat_id")           # single seat: string (legacy)
        pid      = d["passenger_id"]
        fid      = d["flight_id"]

        if not is_admin and (not pax or pax["id"] != pid):
            return err("Not authorized to book for this passenger.", 403)

        if seat_ids and isinstance(seat_ids, list):
            result = book_multiple_seats(pid, fid, seat_ids)
            return ok(result), 201
        elif seat_id:
            result = book_seat(pid, fid, seat_id)
            return ok(result), 201
        else:
            return err("Provide seat_id or seat_ids.")
    except (KeyError, ValueError) as e:
        return err(e)

@app.route("/api/bookings/<bid>/cancel", methods=["POST"])
@require_login
def api_cancel(bid):
    uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
    pax = get_passenger_by_user(uid)

    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
        is_admin = user and user["role"] == "admin"

        if not pax and not is_admin:
            return err("Passenger profile not found.", 403)

        b = conn.execute("SELECT passenger_id FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b or (not is_admin and b["passenger_id"] != pax["id"]):
            return err("Not authorized to cancel this booking.", 403)

    try:
        result = cancel_booking(bid)
        return ok(result)
    except ValueError as e:
        return err(e)

@app.route("/api/bookings/<bid>/upgrade", methods=["POST"])
@require_login
def api_upgrade(bid):
    uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
    pax = get_passenger_by_user(uid)

    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
        is_admin = user and user["role"] == "admin"

        if not pax and not is_admin:
            return err("Passenger profile not found.", 403)

        b = conn.execute("SELECT passenger_id FROM bookings WHERE id=?", (bid,)).fetchone()
        if not b or (not is_admin and b["passenger_id"] != pax["id"]):
            return err("Not authorized to upgrade this booking.", 403)

    d = request.json or {}
    try:
        result = upgrade_booking(bid, d["seat_id"])
        return ok(result)
    except (KeyError, ValueError) as e:
        return err(e)

# ─── Waitlist ─────────────────────────────────────────────────────────────────

@app.route("/api/waitlist", methods=["GET"])
@require_login
def api_waitlist():
    # Only return waitlist for current user
    uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
    pax = get_passenger_by_user(uid)
    if not pax:
        return err("Passenger profile not found.", 403)

    fid = request.args.get("flight_id")
    wl = get_waitlist(fid)
    # Filter for logged in passenger
    wl = [w for w in wl if w["passenger_id"] == pax["id"]]
    return ok(wl)

@app.route("/api/waitlist", methods=["POST"])
@require_login
def api_join_waitlist():
    uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
    pax = get_passenger_by_user(uid)

    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
        is_admin = user and user["role"] == "admin"

    d = request.json or {}
    pid = d.get("passenger_id")

    if not is_admin and (not pax or pax["id"] != pid):
        return err("Not authorized to join waitlist for this passenger.", 403)

    try:
        join_waitlist(pid, d["flight_id"], d.get("pref_class","Economy"))
        return ok({"joined": True}), 201
    except (KeyError, ValueError) as e:
        return err(e)

@app.route("/api/waitlist/<wid>", methods=["DELETE"])
@require_login
def api_remove_waitlist(wid):
    uid = request.headers.get("X-User-Id") or (request.is_json and request.json and request.json.get("_uid"))
    pax = get_passenger_by_user(uid)

    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
        is_admin = user and user["role"] == "admin"

        if not pax and not is_admin:
            return err("Passenger profile not found.", 403)

        w = conn.execute("SELECT passenger_id FROM waitlist WHERE id=?", (wid,)).fetchone()
        if not w or (not is_admin and w["passenger_id"] != pax["id"]):
            return err("Not authorized to remove this waitlist entry.", 403)

    remove_from_waitlist(wid)
    return ok({"removed": wid})

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print("\n  AirBook server starting...")
    print(f"  Frontend : http://localhost:{port}")
    print(f"  Admin    : http://localhost:{port}/admin")
    print(f"  Login    : http://localhost:{port}/login")
    print(f"  API Base : http://localhost:{port}/api\n")
    app.run(debug=debug, host="0.0.0.0", port=port)
