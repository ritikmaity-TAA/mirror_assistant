from uuid import UUID
from fastapi import HTTPException
from schemas.booking import BookingCreate, BookingUpdate
from core.constants import ErrorMessages, SlotStatus, BookingStatus
from db.repositories.booking_repository import BookingRepository
from db.repositories.schedule_repository import ScheduleRepository
from utils.validators import generate_uuid
from supabase import Client

class BookingService:
    @staticmethod
    def create_booking(db: Client, booking: BookingCreate):
        # 1. Fetch the Parent Availability Window
        slot_resp = ScheduleRepository.get_slot_by_id(db, str(booking.slot_id))
        # Handle cases where .data might be a list or a single dict
        parent_slot = slot_resp.data[0] if isinstance(slot_resp.data, list) else slot_resp.data
        
        if not parent_slot or parent_slot.get('status') != SlotStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=ErrorMessages.SLOT_UNAVAILABLE)

        # 2. Extract Times for Comparison
        t_start, t_end = parent_slot['start_time'], parent_slot['end_time']
        b_start, b_end = booking.start_time, booking.end_time

        # 3. Check for overlapping bookings (Req 11.b)
        overlap = BookingRepository.get_bookings_by_professional_and_date(
            db, str(booking.professional_id), booking.date
        )
        for b in overlap.data:
            if b.get('status') != BookingStatus.CANCELLED:
                if (b_start < b['end_time']) and (b_end > b['start_time']):
                    raise HTTPException(status_code=409, detail="Time conflict with an existing booking.")

        # --- SMART FIX: SLOT SPLITTING LOGIC ---
        
        # 4. If booking starts AFTER slot starts, create a 'Before' slot
        if b_start > t_start:
            before_data = {
                "slot_id": generate_uuid(),
                "professional_id": str(parent_slot['professional_id']),
                "date": parent_slot['date'],
                "start_time": t_start,
                "end_time": b_start,
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
                "start_time": b_end,
                "end_time": t_end,
                "status": SlotStatus.AVAILABLE
            }
            ScheduleRepository.create_slot(db, after_data)

        # 6. Update the Parent Slot to match the Booking exactly and mark as BOOKED
        update_payload = {
            "start_time": b_start,
            "end_time": b_end,
            "status": SlotStatus.BOOKED
        }
        ScheduleRepository.update_slot_status(db, str(booking.slot_id), update_payload)

        # 7. Create the actual Booking Record
        booking_payload = booking.model_dump(mode="json")
        booking_payload["booking_id"] = generate_uuid()
        result = BookingRepository.create_booking(db, booking_payload)

        return {"status": "booking created and slot split successfully", "data": result.data[0]}

    @staticmethod
    def cancel_booking(db: Client, booking_id: UUID):
        res = BookingRepository.get_booking_by_id(db, str(booking_id))
        booking = res.data[0] if isinstance(res.data, list) else res.data
        
        if not booking:
            raise HTTPException(status_code=404, detail="invalid booking identifier")

        # Reopen slot so it's available again
        ScheduleRepository.update_slot_status(db, str(booking['slot_id']), SlotStatus.AVAILABLE)
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