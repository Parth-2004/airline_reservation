import uuid
from datetime import datetime
from models.seat import Seat


class Booking:
    STATUSES = ["Confirmed", "Cancelled", "Upgraded"]

    def __init__(
        self,
        passenger,          # Passenger object
        flight,             # Flight object
        seat: Seat,
        booking_id: str = None,
    ):
        self.booking_id = booking_id or "BK" + str(uuid.uuid4())[:6].upper()
        self.passenger = passenger
        self.flight = flight
        self.seat = seat
        self.booking_time = datetime.now()
        self.status = "Confirmed"
        self.price = seat.price

    def cancel(self):
        self.seat.release()
        self.status = "Cancelled"
        self.passenger.remove_booking(self.booking_id)

    def upgrade(self, new_seat: Seat):
        old_label = self.seat.label
        self.seat.release()
        new_seat.book(self.passenger.passenger_id)
        self.seat = new_seat
        self.price = new_seat.price
        self.status = "Upgraded"
        return old_label

    def receipt(self) -> str:
        lines = [
            "=" * 42,
            f"  BOOKING CONFIRMATION",
            "=" * 42,
            f"  Booking ID  : {self.booking_id}",
            f"  Passenger   : {self.passenger.name}",
            f"  Flight      : {self.flight.flight_id}",
            f"  Route       : {self.flight.origin} → {self.flight.destination}",
            f"  Seat        : {self.seat.label} ({self.seat.seat_class})",
            f"  Departure   : {self.flight.departure_time.strftime('%d %b %Y %H:%M')}",
            f"  Price       : ₹{self.price:,}",
            f"  Status      : {self.status}",
            "=" * 42,
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "booking_id": self.booking_id,
            "passenger_id": self.passenger.passenger_id,
            "flight_id": self.flight.flight_id,
            "seat_label": self.seat.label,
            "seat_row": self.seat.row,
            "seat_col": self.seat.col,
            "seat_class": self.seat.seat_class,
            "booking_time": self.booking_time.isoformat(),
            "status": self.status,
            "price": self.price,
        }

    def __repr__(self):
        return f"Booking({self.booking_id}, {self.passenger.name}, {self.seat.label})"
