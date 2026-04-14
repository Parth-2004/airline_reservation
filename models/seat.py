class Seat:
    CLASSES = ["Economy", "Business", "First"]
    PRICES = {"Economy": 5000, "Business": 15000, "First": 30000}

    def __init__(self, row: int, col: int, seat_class: str):
        if seat_class not in self.CLASSES:
            raise ValueError(f"Invalid seat class: {seat_class}")
        self.row = row
        self.col = col
        self.seat_class = seat_class
        self.status = "available"   # available | booked | blocked
        self.passenger_id = None

    @property
    def label(self) -> str:
        col_letter = chr(65 + self.col)
        return f"{self.row + 1}{col_letter}"

    @property
    def price(self) -> int:
        return self.PRICES[self.seat_class]

    def book(self, passenger_id: str):
        self.status = "booked"
        self.passenger_id = passenger_id

    def release(self):
        self.status = "available"
        self.passenger_id = None

    def is_available(self) -> bool:
        return self.status == "available"

    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "col": self.col,
            "seat_class": self.seat_class,
            "status": self.status,
            "passenger_id": self.passenger_id,
            "label": self.label,
        }

    def __repr__(self):
        return f"Seat({self.label}, {self.seat_class}, {self.status})"
