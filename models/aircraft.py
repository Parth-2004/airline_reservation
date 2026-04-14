from models.seat import Seat


class Aircraft:
    """
    Models the physical aircraft with a 2D array of Seat objects.
    Layout: First (rows 0-1), Business (rows 2-4), Economy (rows 5+)
    """

    # class_layout: (num_rows, cols_per_row)
    DEFAULT_LAYOUT = {
        "First":    {"rows": 2, "cols": 4},
        "Business": {"rows": 4, "cols": 6},
        "Economy":  {"rows": 14, "cols": 6},
    }

    def __init__(self, model: str, layout: dict = None):
        self.model = model
        self.layout = layout or self.DEFAULT_LAYOUT
        self.seat_map: list[list[Seat]] = []
        self._initialize_seats()

    def _initialize_seats(self):
        self.seat_map = []
        row_idx = 0
        for seat_class, config in self.layout.items():
            for _ in range(config["rows"]):
                row = []
                for col in range(config["cols"]):
                    row.append(Seat(row_idx, col, seat_class))
                self.seat_map.append(row)
                row_idx += 1

    @property
    def total_rows(self) -> int:
        return len(self.seat_map)

    @property
    def capacity(self) -> int:
        return sum(len(row) for row in self.seat_map)

    def get_seat(self, row: int, col: int) -> Seat:
        if row < 0 or row >= len(self.seat_map):
            raise IndexError(f"Row {row} out of range")
        if col < 0 or col >= len(self.seat_map[row]):
            raise IndexError(f"Col {col} out of range for row {row}")
        return self.seat_map[row][col]

    def available_seats(self, seat_class: str = None) -> list[Seat]:
        seats = []
        for row in self.seat_map:
            for seat in row:
                if seat.is_available():
                    if seat_class is None or seat.seat_class == seat_class:
                        seats.append(seat)
        return seats

    def seats_by_class(self) -> dict:
        result = {"First": [], "Business": [], "Economy": []}
        for row in self.seat_map:
            for seat in row:
                result[seat.seat_class].append(seat)
        return result

    def display_map(self) -> str:
        lines = []
        current_class = None
        for row in self.seat_map:
            seat_class = row[0].seat_class
            if seat_class != current_class:
                current_class = seat_class
                lines.append(f"\n--- {seat_class} ---")
            cells = []
            for seat in row:
                symbol = "[X]" if seat.status == "booked" else "[ ]"
                cells.append(symbol)
            lines.append(f"Row {row[0].row + 1:>2}:  " + "  ".join(cells))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "seat_map": [
                [seat.to_dict() for seat in row]
                for row in self.seat_map
            ],
        }
