from uuid import UUID
from datetime import time
from fastapi import HTTPException
from schemas.booking import BookingCreate, BookingUpdate
from core.constants import ErrorMessages, SlotStatus, BookingStatus
from db.repositories.booking_repository import BookingRepository
from db.repositories.schedule_repository import ScheduleRepository
from utils.validators import generate_uuid
from supabase import Client


def _to_time(t: str) -> time:
    """
    Parses a time string of either HH:MM or HH:MM:SS into a datetime.time object.
    Ensures all comparisons are time-aware, not lexicographic string comparisons.
    """
    parts = t.split(":")
    hour, minute = int(parts[0]), int(parts[1])
    second = int(parts[2]) if len(parts) == 3 else 0
    return time(hour, minute, second)


class BookingService:
    @staticmethod
    def create_booking(db: Client, booking: BookingCreate):
        # 1. Fetch the Parent Availability Window
        slot_resp = ScheduleRepository.get_slot_by_id(db, str(booking.slot_id))
        # Handle cases where .data might be a list or a single dict
        parent_slot = slot_resp.data[0] if isinstance(slot_resp.data, list) else slot_resp.data
        
        if not parent_slot or parent_slot.get('status') != SlotStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=ErrorMessages.SLOT_UNAVAILABLE)

        # 2. Extract Times for Comparison — parsed to time objects to handle
        #    mixed HH:MM (LLM) vs HH:MM:SS (DB) formats safely
        t_start = _to_time(parent_slot['start_time'])
        t_end   = _to_time(parent_slot['end_time'])
        b_start = _to_time(booking.start_time)
        b_end   = _to_time(booking.end_time)

        # 3. Check for overlapping bookings (Req 11.b)
        overlap = BookingRepository.get_bookings_by_professional_and_date(
            db, str(booking.professional_id), booking.date
        )
        for b in overlap.data:
            if b.get('status') != BookingStatus.CANCELLED:
                if (b_start < _to_time(b['end_time'])) and (b_end > _to_time(b['start_time'])):
                    raise HTTPException(status_code=409, detail="Time conflict with an existing booking.")

        # --- SMART FIX: SLOT SPLITTING LOGIC ---
        
        # 4. If booking starts AFTER slot starts, create a 'Before' slot
        if b_start > t_start:
            before_data = {
                "slot_id": generate_uuid(),
                "professional_id": str(parent_slot['professional_id']),
                "date": parent_slot['date'],
                "start_time": t_start.strftime("%H:%M:%S"),
                "end_time": b_start.strftime("%H:%M:%S"),
                "status": SlotStatus.AVAILABLE
            }
            ScheduleRepository.create_slot(db, before_data)

        # 5. If booking ends BEFORE slot ends, create an 'After' slot
        # This is what allows John Mirror to book the remaining time!
        if b_end < t_end:
            after_data = {
                "slot_id": generate_uuid(),
                "professional_id": str(parent_slot['professional_id']),
                "date": parent_slot['date'],
                "start_time": b_end.strftime("%H:%M:%S"),
                "end_time": t_end.strftime("%H:%M:%S"),
                "status": SlotStatus.AVAILABLE
            }
            ScheduleRepository.create_slot(db, after_data)

        # 6. Update the Parent Slot to match the Booking exactly and mark as BOOKED
        update_payload = {
            "start_time": b_start.strftime("%H:%M:%S"),
            "end_time": b_end.strftime("%H:%M:%S"),
            "status": SlotStatus.BOOKED
        }
        ScheduleRepository.update_slot(db, str(booking.slot_id), update_payload)

        # 7. Create the actual Booking Record
        booking_payload = booking.model_dump(mode="json")
        booking_payload["booking_id"] = generate_uuid()
        result = BookingRepository.create_booking(db, booking_payload)

        return {"status": "booking created and slot split successfully", "data": result.data[0]}

    @staticmethod
    def cancel_booking(db: Client, booking_id: UUID):
        booking = BookingRepository.get_booking_by_id(db, str(booking_id))

        if not booking:
            raise HTTPException(status_code=404, detail="invalid booking identifier")

        slot_id        = str(booking['slot_id'])
        professional_id = str(booking['professional_id'])
        date           = booking['date']
        booked_start   = _to_time(booking['start_time'])
        booked_end     = _to_time(booking['end_time'])

        # Find all AVAILABLE fragments on the same date for this professional.
        # Adjacent fragments are ones that touch the booked slot's boundary exactly.
        all_slots = ScheduleRepository.get_slots_by_professional_and_date(
            db, professional_id, date
        )
        fragment_ids = []
        merged_start = booked_start
        merged_end   = booked_end

        for s in all_slots.data:
            if s['slot_id'] == slot_id:
                continue
            if s.get('status') != SlotStatus.AVAILABLE:
                continue
            s_start = _to_time(s['start_time'])
            s_end   = _to_time(s['end_time'])
            # Adjacent if it ends exactly where booked slot starts (before-fragment)
            # or starts exactly where booked slot ends (after-fragment)
            if s_end == booked_start or s_start == booked_end:
                fragment_ids.append(s['slot_id'])
                merged_start = min(merged_start, s_start)
                merged_end   = max(merged_end, s_end)

        # Expand the booked slot to cover the merged window and mark AVAILABLE
        ScheduleRepository.update_slot(db, slot_id, {
            "start_time": merged_start.strftime("%H:%M:%S"),
            "end_time":   merged_end.strftime("%H:%M:%S"),
            "status":     SlotStatus.AVAILABLE
        })

        # Delete orphaned fragments (safe: no bookings reference them)
        for fid in fragment_ids:
            ScheduleRepository.delete_slot(db, fid)

        BookingRepository.update_booking_status(db, str(booking_id), BookingStatus.CANCELLED)

        return {
            "success_state": True,
            "cancellation_state": BookingStatus.CANCELLED,
            "message": "booking cancelled successfully"
        }

    @staticmethod
    def update_booking(db: Client, booking_id: UUID, booking: BookingUpdate):
        update_data = booking.model_dump(mode="json", exclude_unset=True)
        result = BookingRepository.update_booking(db, str(booking_id), update_data)
        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def get_upcoming_bookings(db: Client, professional_id: UUID):
        result = BookingRepository.get_upcoming_bookings(db, str(professional_id))
        return {"professional_id": str(professional_id), "entries": result.data}    