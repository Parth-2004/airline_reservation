import uuid


class Passenger:
    TIERS = ["Regular", "Gold", "Platinum"]

    def __init__(self, name: str, email: str, tier: str = "Regular", passenger_id: str = None):
        if tier not in self.TIERS:
            raise ValueError(f"Invalid tier: {tier}")
        self.passenger_id = passenger_id or str(uuid.uuid4())[:8].upper()
        self.name = name
        self.email = email
        self.tier = tier
        self.booking_history: list[str] = []

    @property
    def tier_priority(self) -> int:
        return self.TIERS.index(self.tier)   # higher = higher priority

    def add_booking(self, booking_id: str):
        self.booking_history.append(booking_id)

    def remove_booking(self, booking_id: str):
        if booking_id in self.booking_history:
            self.booking_history.remove(booking_id)

    def to_dict(self) -> dict:
        return {
            "passenger_id": self.passenger_id,
            "name": self.name,
            "email": self.email,
            "tier": self.tier,
            "booking_history": self.booking_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Passenger":
        p = cls(
            name=data["name"],
            email=data["email"],
            tier=data.get("tier", "Regular"),
            passenger_id=data["passenger_id"],
        )
        p.booking_history = data.get("booking_history", [])
        return p

    def __repr__(self):
        return f"Passenger({self.passenger_id}, {self.name}, {self.tier})"

    def __str__(self):
        return f"{self.name} [{self.tier}] <{self.email}>"
