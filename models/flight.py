from datetime import datetime
from models.aircraft import Aircraft


class Flight:
    STATUSES = ["Scheduled", "Boarding", "Departed", "Cancelled"]

    def __init__(
        self,
        flight_id: str,
        origin: str,
        destination: str,
        departure_time: datetime,
        arrival_time: datetime,
        aircraft: Aircraft,
    ):
        self.flight_id = flight_id
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.aircraft = aircraft
        self.status = "Scheduled"

    def get_available_seats(self, seat_class: str = None):
        return self.aircraft.available_seats(seat_class)

    def is_full(self, seat_class: str = None) -> bool:
        return len(self.get_available_seats(seat_class)) == 0

    def occupancy_rate(self, seat_class: str = None) -> float:
        by_class = self.aircraft.seats_by_class()
        if seat_class:
            seats = by_class.get(seat_class, [])
        else:
            seats = [s for sl in by_class.values() for s in sl]
        if not seats:
            return 0.0
        booked = sum(1 for s in seats if s.status == "booked")
        return round(booked / len(seats) * 100, 1)

    def duration_minutes(self) -> int:
        delta = self.arrival_time - self.departure_time
        return int(delta.total_seconds() / 60)

    def to_dict(self) -> dict:
        return {
            "flight_id": self.flight_id,
            "origin": self.origin,
            "destination": self.destination,
            "departure_time": self.departure_time.isoformat(),
            "arrival_time": self.arrival_time.isoformat(),
            "status": self.status,
            "aircraft_model": self.aircraft.model,
        }

    def __repr__(self):
        return f"Flight({self.flight_id}: {self.origin}->{self.destination})"

    def __str__(self):
        dep = self.departure_time.strftime("%d %b %Y %H:%M")
        return f"{self.flight_id}  {self.origin} → {self.destination}  {dep}  [{self.status}]"
