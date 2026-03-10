from uuid import UUID
from fastapi import HTTPException
from ..schemas.schedule import AvailabilitySlotCreate, AvailabilitySlotUpdate
from ..utils.datetime_utils import is_past_date, validate_time_range
from ..core.constants import ErrorMessages, SlotStatus
from supabase import Client

class ScheduleService:
    @staticmethod
    def create_slot(db: Client, slot: AvailabilitySlotCreate):
        # 1. Past Date Validation (Req 11)
        if is_past_date(slot.date):
            raise HTTPException(status_code=400, detail=ErrorMessages.PAST_DATE_ERROR)

        # 2. Logical Time Validation (Req 7.1)
        if not validate_time_range(slot.start_time, slot.end_time):
            raise HTTPException(status_code=400, detail="End time must be after start time.")

        # 3. Overlap Check (Req 11)
        existing_slots = db.table("availability_slots").select("*").eq("professional_id", str(slot.professional_id)).eq("date", slot.date).execute()
        for existing in existing_slots.data:
            if (slot.start_time < existing['end_time']) and (slot.end_time > existing['start_time']):
                raise HTTPException(status_code=409, detail=f"{ErrorMessages.OVERLAP_DETECTED} ({existing['start_time']}-{existing['end_time']})")

        result = db.table("availability_slots").insert(slot.dict()).execute()
        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def get_day_schedule(db: Client, professional_id: UUID, date_str: str):
        # Req 7.7: Ordered day timeline
        slots = db.table("availability_slots").select("*, bookings(*)").eq("professional_id", str(professional_id)).eq("date", date_str).order("start_time").execute()
        return {"date": date_str, "entries": slots.data}