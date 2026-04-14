# AirBook -- Airline Seat Reservation System

**Live Demo:** [https://Parth2004.pythonanywhere.com](https://Parth2004.pythonanywhere.com)

A full-stack airline reservation system built with **Flask** and **SQLite**, featuring real-time seat maps, multi-seat booking, waitlist management, and an admin dashboard.

## Features

### User Dashboard
- Browse available flights with live occupancy stats
- Interactive seat map with multi-seat selection (up to 9 seats)
- Book, cancel, and upgrade reservations
- Join waitlists with priority based on passenger tier
- View booking history and flight reports

### Admin Panel
- System overview with real-time metrics
- Add/delete flights with multiple aircraft models (Boeing 737, Airbus A320, Boeing 777, Airbus A380)
- Manage users and passenger tiers (Regular, Gold, Platinum)
- View all bookings with cancel capability
- Revenue and occupancy analytics

### Core Logic
- **Priority Waitlist**: Platinum > Gold > Regular with FIFO within same tier
- **Auto-Assignment**: When a booking is cancelled, the next waitlisted passenger is automatically assigned
- **Atomic Multi-Seat Booking**: All seats booked in a single transaction -- if any fail, none are booked
- **Seat Upgrade**: Move to a higher class with automatic seat swap

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Database | SQLite (file-based) |
| Frontend | Vanilla HTML, CSS, JavaScript |
| Deployment | PythonAnywhere |

## Project Structure

```
airline_reservation/
├── server.py              # Flask app with REST API endpoints
├── requirements.txt       # Python dependencies
├── .gitignore
├── static/
│   ├── index.html         # User dashboard (SPA)
│   ├── admin.html         # Admin panel (SPA)
│   └── login.html         # Authentication page
├── utils/
│   ├── database.py        # SQLite database layer
│   ├── exceptions.py      # Custom exception classes
│   ├── file_manager.py    # JSON file I/O utility
│   └── report_generator.py# Report generation
├── models/
│   ├── aircraft.py        # Aircraft class with seat map
│   ├── booking.py         # Booking model
│   ├── flight.py          # Flight model
│   ├── passenger.py       # Passenger model
│   └── seat.py            # Seat model
└── core/
    ├── reservation_system.py  # Central reservation coordinator
    └── waiting_queue.py       # Priority queue (heap-based)
```

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Parth-2004/airline_reservation.git
cd airline_reservation

# 2. Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python server.py
```

The app will be available at:
- **User Dashboard**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
- **Login Page**: http://localhost:5000/login

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login |

### Flights
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flights` | List all flights with stats |
| GET | `/api/flights/<id>` | Get single flight |
| GET | `/api/flights/<id>/seatmap` | Get seat map (grouped by row) |
| GET | `/api/flights/<id>/seats` | Get seats (optional `?class=` filter) |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/bookings` | Get bookings (filter by passenger/flight/status) |
| POST | `/api/bookings` | Book seat(s) -- supports `seat_id` or `seat_ids[]` |
| POST | `/api/bookings/<id>/cancel` | Cancel a booking |
| POST | `/api/bookings/<id>/upgrade` | Upgrade to a different seat |

### Waitlist
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/waitlist` | Get waitlist entries |
| POST | `/api/waitlist` | Join waitlist |
| DELETE | `/api/waitlist/<id>` | Remove from waitlist |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | Dashboard statistics |
| GET | `/api/admin/users` | All users |
| GET | `/api/admin/revenue` | Revenue breakdown by class |
| GET | `/api/admin/occupancy` | Flight occupancy report |
| POST | `/api/admin/flights` | Add a new flight |
| DELETE | `/api/admin/flights/<id>` | Delete a flight |

## Deployment

Deployed on **PythonAnywhere** (free tier) at [https://Parth2004.pythonanywhere.com](https://Parth2004.pythonanywhere.com).

The SQLite database persists on PythonAnywhere's filesystem. No external database service required.

## License

This project is built for educational / college demonstration purposes.
