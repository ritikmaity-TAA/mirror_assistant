from uuid import UUID
from supabase import Client
from core.constants import BookingStatus
from datetime import datetime

class BookingRepository:
    @staticmethod
    def create_booking(db: Client, booking_data: dict):
        return db.table("bookings").insert(booking_data).execute()

    @staticmethod
    def get_bookings_by_professional_and_date(db: Client, professional_id: UUID, date: str):
        return db.table("bookings")\
            .select("*")\
            .eq("professional_id", str(professional_id))\
            .eq("date", date)\
            .execute()

    @staticmethod
    def get_booking_by_id(db: Client, booking_id: UUID):
        return db.table("bookings")\
            .select("*")\
            .eq("booking_id", str(booking_id))\
            .single()\
            .execute()

    @staticmethod
    def update_booking(db: Client, booking_id: UUID, update_data: dict):
        return db.table("bookings")\
            .update(update_data)\
            .eq("booking_id", str(booking_id))\
            .execute()

    @staticmethod
    def update_booking_status(db: Client, booking_id: UUID, status: str):
        return db.table("bookings")\
            .update({"status": status})\
            .eq("booking_id", str(booking_id))\
            .execute()

    @staticmethod
    def get_upcoming_bookings(db: Client, professional_id: UUID):
        # Requirement 7.9: View upcoming sessions
        now = datetime.now().isoformat()
        return db.table("bookings")\
            .select("*, clients(client_name)")\
            .eq("professional_id", str(professional_id))\
            .gte("date", now.split('T')[0])\
            .order("date")\
            .order("start_time")\
            .execute()
