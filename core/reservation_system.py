from models.passenger import Passenger
from models.flight import Flight
from models.booking import Booking
from models.seat import Seat
from core.waiting_queue import WaitingQueue
from utils.exceptions import (
    SeatNotAvailableError, FlightNotFoundError,
    PassengerNotFoundError, BookingNotFoundError, InvalidSeatError,
)


class ReservationSystem:
    """Central coordinator for all reservation operations."""

    def __init__(self):
        self.flights: dict[str, Flight] = {}
        self.passengers: dict[str, Passenger] = {}
        self.bookings: dict[str, Booking] = {}
        self.waiting_queues: dict[str, WaitingQueue] = {}

    # ──────────────────────────── Registration ────────────────────────────

    def add_flight(self, flight: Flight):
        self.flights[flight.flight_id] = flight
        self.waiting_queues[flight.flight_id] = WaitingQueue(flight.flight_id)

    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.passenger_id] = passenger
        return passenger

    # ──────────────────────────── Booking ─────────────────────────────────

    def book_seat(self, passenger_id: str, flight_id: str, row: int, col: int) -> Booking:
        passenger = self._get_passenger(passenger_id)
        flight = self._get_flight(flight_id)

        try:
            seat = flight.aircraft.get_seat(row, col)
        except IndexError:
            raise InvalidSeatError(f"Seat at row={row}, col={col} does not exist.")

        if not seat.is_available():
            raise SeatNotAvailableError(
                f"Seat {seat.label} on flight {flight_id} is not available."
            )

        seat.book(passenger_id)
        booking = Booking(passenger, flight, seat)
        self.bookings[booking.booking_id] = booking
        passenger.add_booking(booking.booking_id)
        return booking

    # ──────────────────────────── Cancellation ────────────────────────────

    def cancel_booking(self, booking_id: str) -> str:
        booking = self._get_booking(booking_id)
        flight = booking.flight
        freed_class = booking.seat.seat_class
        booking.cancel()

        # Try to assign the freed seat to the next person on the waitlist
        assigned_msg = self._process_waitlist(flight.flight_id, freed_class)
        return assigned_msg

    def _process_waitlist(self, flight_id: str, seat_class: str) -> str:
        queue = self.waiting_queues.get(flight_id)
        if not queue or queue.is_empty():
            return ""

        passenger, pref = queue.peek()
        available = self.flights[flight_id].get_available_seats(pref or seat_class)
        if not available:
            available = self.flights[flight_id].get_available_seats(seat_class)

        if available:
            queue.dequeue()
            seat = available[0]
            booking = self.book_seat(passenger.passenger_id, flight_id, seat.row, seat.col)
            return (
                f"Waitlist: {passenger.name} was automatically assigned "
                f"seat {seat.label} ({seat.seat_class}) — Booking {booking.booking_id}"
            )
        return ""

    # ──────────────────────────── Upgrade ─────────────────────────────────

    def upgrade_seat(self, booking_id: str, new_row: int, new_col: int) -> tuple:
        booking = self._get_booking(booking_id)
        flight = booking.flight

        try:
            new_seat = flight.aircraft.get_seat(new_row, new_col)
        except IndexError:
            raise InvalidSeatError(f"Seat at row={new_row}, col={new_col} does not exist.")

        if not new_seat.is_available():
            raise SeatNotAvailableError(f"Seat {new_seat.label} is not available for upgrade.")

        old_class = booking.seat.seat_class
        old_label = booking.upgrade(new_seat)

        # original seat freed — try to fill from waitlist
        msg = self._process_waitlist(flight.flight_id, old_class)
        return old_label, new_seat.label, msg

    # ──────────────────────────── Waitlist ────────────────────────────────

    def join_waitlist(self, passenger_id: str, flight_id: str, seat_class_pref: str = "Economy"):
        passenger = self._get_passenger(passenger_id)
        _ = self._get_flight(flight_id)
        queue = self.waiting_queues[flight_id]
        queue.enqueue(passenger, seat_class_pref)

    # ──────────────────────────── Helpers ─────────────────────────────────

    def _get_passenger(self, pid: str) -> Passenger:
        if pid not in self.passengers:
            raise PassengerNotFoundError(f"Passenger {pid} not found.")
        return self.passengers[pid]

    def _get_flight(self, fid: str) -> Flight:
        if fid not in self.flights:
            raise FlightNotFoundError(f"Flight {fid} not found.")
        return self.flights[fid]

    def _get_booking(self, bid: str) -> Booking:
        if bid not in self.bookings:
            raise BookingNotFoundError(f"Booking {bid} not found.")
        return self.bookings[bid]

    # ──────────────────────────── Queries ─────────────────────────────────

    def get_passenger_bookings(self, passenger_id: str) -> list[Booking]:
        passenger = self._get_passenger(passenger_id)
        return [self.bookings[bid] for bid in passenger.booking_history if bid in self.bookings]

    def search_flights(self, origin: str = None, destination: str = None) -> list[Flight]:
        results = list(self.flights.values())
        if origin:
            results = [f for f in results if f.origin.lower() == origin.lower()]
        if destination:
            results = [f for f in results if f.destination.lower() == destination.lower()]
        return results
