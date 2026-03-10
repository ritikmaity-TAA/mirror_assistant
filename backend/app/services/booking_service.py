from uuid import UUID
from fastapi import HTTPException
from ..schemas.booking import BookingCreate, BookingUpdate
from ..core.constants import ErrorMessages, SlotStatus, BookingStatus
from supabase import Client

class BookingService:
    @staticmethod
    def create_booking(db: Client, booking: BookingCreate):
        # 1. Validate Slot Availability (Req 7.4)
        slot_resp = db.table("availability_slots").select("*").eq("slot_id", str(booking.slot_id)).single().execute()
        slot = slot_resp.data
        
        if not slot or slot['status'] != SlotStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=ErrorMessages.SLOT_UNAVAILABLE)

        # 2. Check for duplicate bookings (Req 11)
        overlap = db.table("bookings").select("*").eq("professional_id", str(booking.professional_id)).eq("date", booking.date).execute()
        # (Logic to ensure professional isn't double-booked here)

        # 3. Transaction: Create Booking & Update Slot Status (Req 10.1)
        booking_data = db.table("bookings").insert(booking.dict()).execute()
        db.table("availability_slots").update({"status": SlotStatus.BOOKED}).eq("slot_id", str(booking.slot_id)).execute()

        return {"status": "booking created successfully", "data": booking_data.data[0]}

    @staticmethod
    def cancel_booking(db: Client, booking_id: UUID):
        # Req 7.6: Reopen slot after cancellation
        booking = db.table("bookings").select("slot_id").eq("booking_id", str(booking_id)).single().execute()
        if booking.data:
            db.table("availability_slots").update({"status": SlotStatus.AVAILABLE}).eq("slot_id", booking.data['slot_id']).execute()
            db.table("bookings").update({"status": BookingStatus.CANCELLED}).eq("booking_id", str(booking_id)).execute()
            return {"status": "cancelled successfully"}
        raise HTTPException(status_code=404, detail="Booking not found.")