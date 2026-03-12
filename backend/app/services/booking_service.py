from uuid import UUID
from fastapi import HTTPException
from schemas.booking import BookingCreate, BookingUpdate
from core.constants import ErrorMessages, SlotStatus, BookingStatus
from db.repositories.booking_repository import BookingRepository
from db.repositories.schedule_repository import ScheduleRepository
from utils.validators import generate_uuid
from utils.datetime_utils import calculate_time_block, is_past_datetime # Make sure to add this to utils!
from supabase import Client

class BookingService:
    @staticmethod
    def create_booking(db: Client, booking: BookingCreate):
        booking.start_time = booking.start_time[:5]
        booking.end_time = booking.end_time[:5]
        # 0. Past-Time Validation (Mandatory Rule)
        if is_past_datetime(booking.date, booking.start_time):
            raise HTTPException(status_code=400, detail="Cannot create a booking for a time that has already passed.")
            
        # 1. Fetch the Parent Availability Window
        slot_resp = ScheduleRepository.get_slot_by_id(db, str(booking.slot_id))
        parent_slot = slot_resp.data[0] if isinstance(slot_resp.data, list) and slot_resp.data else slot_resp.data
        
        if not parent_slot or parent_slot.get('status') != SlotStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=ErrorMessages.SLOT_UNAVAILABLE)

        # 2. Force 50 mins session + 10 mins buffer (60 mins total block)
        work_end, total_block_end = calculate_time_block(booking.start_time)
        
        t_start, t_end = parent_slot['start_time'], parent_slot['end_time']
        b_start = booking.start_time
        
        # Consistent normalization for comparison (ensures 11:00 == 11:00:00)
        def norm(t): return t if len(t.split(':')) == 3 else f"{t}:00"
        
        # Check if the calculated end time exceeds the parent slot's availability
        if norm(total_block_end) > norm(t_end):
             raise HTTPException(status_code=400, detail="The 60-minute session (incl. buffer) exceeds the available window.")

        # 3. Check for overlapping bookings (Req 11.b)
        overlap = BookingRepository.get_bookings_by_professional_and_date(
            db, str(booking.professional_id), booking.date
        )
        for b in overlap.data:
            if b.get('status') != BookingStatus.CANCELLED:
                if (norm(b_start) < norm(b['end_time'])) and (norm(total_block_end) > norm(b['start_time'])):
                    raise HTTPException(status_code=409, detail="Time conflict with an existing booking.")

        # --- SMART FIX: SLOT SPLITTING LOGIC ---
        
        # 4. Create 'Before' slot if booking doesn't start at the very beginning of the window
        # We use norm() to prevent ghost slots caused by string mismatches (11:00 vs 11:00:00)
        if norm(b_start) > norm(t_start):
            before_data = {
                "slot_id": generate_uuid(),
                "professional_id": str(parent_slot['professional_id']),
                "date": parent_slot['date'],
                "start_time": t_start,
                "end_time": b_start,
                "status": SlotStatus.AVAILABLE
            }
            ScheduleRepository.create_slot(db, before_data)

        # 5. Create 'After' slot if there is time left AFTER the 10-min buffer
        if norm(total_block_end) < norm(t_end):
            after_data = {
                "slot_id": generate_uuid(),
                "professional_id": str(parent_slot['professional_id']),
                "date": parent_slot['date'],
                "start_time": total_block_end,
                "end_time": t_end,
                "status": SlotStatus.AVAILABLE
            }
            ScheduleRepository.create_slot(db, after_data)

        # 6. Update the Original Slot to match the 60-min block and mark as BOOKED
        update_payload = {
            "start_time": b_start,
            "end_time": total_block_end,
            "status": SlotStatus.BOOKED
        }
        ScheduleRepository.update_slot_status(db, str(booking.slot_id), update_payload)

        # 7. Create the actual Booking Record
        booking_payload = booking.model_dump(mode="json")
        booking_payload["booking_id"] = generate_uuid()
        # Ensure the booking record reflects the 50-min work time for the CEO
        booking_payload["end_time"] = work_end 
        
        # Ensure UUID stringification consistency
        booking_payload = {k: str(v) if k.endswith('_id') else v for k, v in booking_payload.items()}
        result = BookingRepository.create_booking(db, booking_payload)

        return {"status": "booking created with 10m buffer and slot split successfully", "data": result.data[0]}

    @staticmethod
    def cancel_booking(db: Client, booking_id: UUID):
        res = BookingRepository.get_booking_by_id(db, str(booking_id))
        booking = res.data[0] if isinstance(res.data, list) and res.data else res.data
        
        if not booking:
            raise HTTPException(status_code=404, detail="invalid booking identifier")

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
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Booking update failed or not found.")
            
        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def get_upcoming_bookings(db: Client, professional_id: UUID):
        result = BookingRepository.get_upcoming_bookings(db, str(professional_id))
        return {"professional_id": str(professional_id), "entries": result.data}