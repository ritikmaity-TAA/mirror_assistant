from uuid import UUID
from supabase import Client
from core.constants import SlotStatus

class ScheduleRepository:
    @staticmethod
    def get_slots_by_professional_and_date(db: Client, professional_id: UUID, date: str):
        return db.table("availability_slots")\
            .select("*")\
            .eq("professional_id", str(professional_id))\
            .eq("date", date)\
            .execute()

    @staticmethod
    def create_slot(db: Client, slot_data: dict):
        return db.table("availability_slots").insert(slot_data).execute()

    @staticmethod
    def get_day_schedule(db: Client, professional_id: UUID, date_str: str):
        return db.table("availability_slots")\
            .select("*, bookings(*)")\
            .eq("professional_id", str(professional_id))\
            .eq("date", date_str)\
            .order("start_time")\
            .execute()

    @staticmethod
    def get_slot_by_id(db: Client, slot_id: UUID):
        return db.table("availability_slots")\
            .select("*")\
            .eq("slot_id", str(slot_id))\
            .single()\
            .execute()

    @staticmethod
    def update_slot_status(db: Client, slot_id: UUID, status: str):
        return db.table("availability_slots")\
            .update({"status": status})\
            .eq("slot_id", str(slot_id))\
            .execute()
