import json
import os
from datetime import datetime


class FileManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def save_json(self, data, filename: str):
        with open(self._path(filename), "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_json(self, filename: str):
        path = self._path(filename)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def save_bookings(self, bookings: dict):
        data = [b.to_dict() for b in bookings.values()]
        self.save_json(data, "bookings.json")

    def save_passengers(self, passengers: dict):
        data = [p.to_dict() for p in passengers.values()]
        self.save_json(data, "passengers.json")

    def load_passengers(self) -> list[dict]:
        return self.load_json("passengers.json") or []

    def load_bookings(self) -> list[dict]:
        return self.load_json("bookings.json") or []
