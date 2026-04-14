import heapq
from collections import deque


class WaitingQueue:
    """
    Priority queue for waiting passengers.
    Platinum > Gold > Regular; within same tier, FIFO by insertion order.
    Internally uses a min-heap with (neg_priority, counter, passenger_id, seat_class_pref).
    """

    def __init__(self, flight_id: str):
        self.flight_id = flight_id
        self._heap: list = []
        self._counter = 0           # tie-breaker for FIFO within same tier

    def enqueue(self, passenger, seat_class_pref: str = "Economy"):
        priority = -passenger.tier_priority   # negate so Platinum (2) comes first
        entry = (priority, self._counter, passenger.passenger_id, seat_class_pref, passenger)
        heapq.heappush(self._heap, entry)
        self._counter += 1

    def dequeue(self):
        """Returns (passenger, seat_class_pref) or (None, None) if empty."""
        while self._heap:
            _, _, _, seat_class_pref, passenger = heapq.heappop(self._heap)
            return passenger, seat_class_pref
        return None, None

    def peek(self):
        if self._heap:
            _, _, _, seat_class_pref, passenger = self._heap[0]
            return passenger, seat_class_pref
        return None, None

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def all_entries(self) -> list:
        """Return list of (passenger, seat_class_pref) in priority order (non-destructive)."""
        sorted_heap = sorted(self._heap)
        return [(entry[4], entry[3]) for entry in sorted_heap]

    def display(self) -> str:
        if self.is_empty():
            return "  Waiting list is empty."
        lines = [f"  Waiting list for flight {self.flight_id}:"]
        for i, (passenger, pref) in enumerate(self.all_entries(), 1):
            lines.append(f"  {i}. {passenger.name} [{passenger.tier}] — prefers {pref}")
        return "\n".join(lines)

    def __len__(self):
        return self.size()

    def __repr__(self):
        return f"WaitingQueue(flight={self.flight_id}, size={self.size()})"
