from uuid import UUID
from fastapi import HTTPException
from schemas.booking import BookingCreate, BookingUpdate
from core.constants import ErrorMessages, SlotStatus, BookingStatus
from db.repositories.booking_repository import BookingRepository
from db.repositories.schedule_repository import ScheduleRepository
from utils.datetime_utils import is_past_date, validate_time_range
from supabase import Client

class BookingService:
    @staticmethod
    def create_booking(db: Client, booking: BookingCreate):
        # 1. Validate Slot Availability (Req 7.4)
        slot_resp = ScheduleRepository.get_slot_by_id(db, booking.slot_id)
        slot = slot_resp.data
        
        if not slot or slot['status'] != SlotStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=ErrorMessages.SLOT_UNAVAILABLE)

        # 2. Check for duplicate bookings (Req 11)
        overlap = BookingRepository.get_bookings_by_professional_and_date(
            db, booking.professional_id, booking.date
        )
        # (Logic to ensure professional isn't double-booked here)

        # 3. Transaction: Create Booking & Update Slot Status (Req 10.1)
        booking_data = BookingRepository.create_booking(db, booking.dict())
        ScheduleRepository.update_slot_status(db, booking.slot_id, SlotStatus.BOOKED)

        return {"status": "booking created successfully", "data": booking_data.data[0]}

    @staticmethod
    def cancel_booking(db: Client, booking_id: UUID):
        # Req 7.6: Reopen slot after cancellation
        booking = BookingRepository.get_booking_by_id(db, booking_id)
        if booking.data:
            ScheduleRepository.update_slot_status(db, booking.data['slot_id'], SlotStatus.AVAILABLE)
            BookingRepository.update_booking_status(db, booking_id, BookingStatus.CANCELLED)
            return {"status": "cancelled successfully"}
        raise HTTPException(status_code=404, detail="Booking not found.")

    @staticmethod
    def update_booking(db: Client, booking_id: UUID, booking: BookingUpdate):
        result = BookingRepository.update_booking(db, booking_id, booking.dict(exclude_unset=True))
        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def get_upcoming_bookings(db: Client, professional_id: UUID):
        result = BookingRepository.get_upcoming_bookings(db, professional_id)
        return {"professional_id": str(professional_id), "entries": result.data}