from models.flight import Flight
from core.waiting_queue import WaitingQueue


class ReportGenerator:
    def occupancy_report(self, flight: Flight) -> dict:
        by_class = flight.aircraft.seats_by_class()
        report = {}
        for cls, seats in by_class.items():
            total = len(seats)
            booked = sum(1 for s in seats if s.status == "booked")
            report[cls] = {
                "total": total,
                "booked": booked,
                "available": total - booked,
                "occupancy_pct": round(booked / total * 100, 1) if total else 0,
            }
        return report

    def revenue_report(self, bookings: dict, flight_id: str = None) -> dict:
        relevant = [
            b for b in bookings.values()
            if b.status != "Cancelled" and (flight_id is None or b.flight.flight_id == flight_id)
        ]
        total = sum(b.price for b in relevant)
        by_class = {}
        for b in relevant:
            cls = b.seat.seat_class
            by_class[cls] = by_class.get(cls, 0) + b.price
        return {"total": total, "by_class": by_class, "booking_count": len(relevant)}

    def waitlist_report(self, queues: dict) -> dict:
        return {
            fid: {
                "size": q.size(),
                "entries": [
                    {"name": p.name, "tier": p.tier, "preference": pref}
                    for p, pref in q.all_entries()
                ],
            }
            for fid, q in queues.items()
        }

    def full_summary(self, flights: dict, bookings: dict, queues: dict) -> str:
        lines = ["\n" + "=" * 50, "  SYSTEM SUMMARY REPORT", "=" * 50]
        for fid, flight in flights.items():
            lines.append(f"\nFlight {fid}  {flight.origin} → {flight.destination}")
            occ = self.occupancy_report(flight)
            for cls, data in occ.items():
                lines.append(
                    f"  {cls:10s}: {data['booked']:>3}/{data['total']:>3} seats "
                    f"({data['occupancy_pct']}%)"
                )
            rev = self.revenue_report(bookings, fid)
            lines.append(f"  Revenue   : ₹{rev['total']:,}")
            wl = queues.get(fid)
            if wl:
                lines.append(f"  Waitlist  : {wl.size()} passenger(s)")
        lines.append("=" * 50)
        return "\n".join(lines)
