from uuid import UUID
from datetime import date, datetime
from fastapi import HTTPException
from schemas.schedule import AvailabilitySlotCreate, AvailabilitySlotUpdate
from utils.datetime_utils import is_past_date, validate_time_range
from utils.validators import generate_uuid
from core.constants import ErrorMessages, SlotStatus
from db.repositories.schedule_repository import ScheduleRepository
from supabase import Client


def _to_time(t: str):
    """Parse HH:MM or HH:MM:SS string to datetime.time."""
    from datetime import time
    parts = t.split(":")
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    return time(h, m, s)


class ScheduleService:
    @staticmethod
    def create_slot(db: Client, slot: AvailabilitySlotCreate):
        # 1. Past Date Validation (Req 11)
        if is_past_date(slot.date):
            raise HTTPException(status_code=400, detail=ErrorMessages.PAST_DATE_ERROR)

        # 1b. Past Time Validation for today — date alone is not enough.
        #     A slot starting at 08:00 on today's date is invalid if it's already 14:00.
        slot_date = date.fromisoformat(slot.date) if isinstance(slot.date, str) else slot.date
        if slot_date == date.today():
            slot_start = _to_time(slot.start_time)
            now_time = datetime.now().time().replace(second=0, microsecond=0)
            if slot_start < now_time:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot create a slot that starts in the past."
                )

        # 2. Logical Time Validation (Req 7.1)
        if not validate_time_range(slot.start_time, slot.end_time):
            raise HTTPException(status_code=400, detail="End time must be after start time.")

        # 3. Overlap Check (Req 11) — uses time objects, not string comparison
        existing_slots = ScheduleRepository.get_slots_by_professional_and_date(
            db, str(slot.professional_id), slot.date
        )
        new_start = _to_time(slot.start_time)
        new_end   = _to_time(slot.end_time)
        for existing in existing_slots.data:
            # Ignore cancelled slots so they don't block new time windows
            if existing.get("status") == SlotStatus.CANCELLED:
                continue
            if (new_start < _to_time(existing["end_time"])) and (new_end > _to_time(existing["start_time"])):
                raise HTTPException(
                    status_code=409,
                    detail=f"{ErrorMessages.OVERLAP_DETECTED} ({existing['start_time']}-{existing['end_time']})"
                )

        # 4. Manual UUID Generation & String Cleaning
        slot_data = slot.model_dump(mode="json")
        slot_data["slot_id"] = generate_uuid()
        # Stringify everything for Supabase/JSON safety
        slot_data = {k: str(v) if isinstance(v, UUID) else v for k, v in slot_data.items()}

        result = ScheduleRepository.create_slot(db, slot_data)

        if not result.data:
            raise HTTPException(status_code=500, detail="Database insertion failed.")

        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def get_day_schedule(db: Client, professional_id: UUID, date_str: str):
        # Req 7.7: Ordered day timeline
        slots = ScheduleRepository.get_day_schedule(db, str(professional_id), date_str)
        return {"date": date_str, "entries": slots.data if slots.data else []}

    @staticmethod
    def update_slot(db: Client, slot_id: UUID, slot: AvailabilitySlotUpdate):
        # Business logic: prevent updating booked slots
        existing = ScheduleRepository.get_slot_by_id(db, str(slot_id))
        slot_record = existing.data[0] if isinstance(existing.data, list) and existing.data else existing.data

        if not slot_record:
            raise HTTPException(status_code=404, detail="invalid slot identifier")

        if slot_record.get("status") == SlotStatus.BOOKED:
            raise HTTPException(status_code=400, detail="Cannot update a slot that is already booked.")

        # Perform update
        update_data = slot.model_dump(mode="json", exclude_unset=True)
        result = ScheduleRepository.update_slot(db, str(slot_id), update_data)

        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def delete_slot(db: Client, slot_id: UUID):
        # Req 7.3: Validation before deletion
        existing = ScheduleRepository.get_slot_by_id(db, str(slot_id))
        slot_record = existing.data[0] if isinstance(existing.data, list) and existing.data else existing.data

        if not slot_record:
            raise HTTPException(status_code=404, detail="invalid slot identifier")

        if slot_record.get("status") == SlotStatus.BOOKED:
            raise HTTPException(status_code=400, detail="deletion blocked due to active booking")

        # Proceed to cancel
        result = ScheduleRepository.update_slot_status(db, str(slot_id), SlotStatus.CANCELLED)
        return {"status": "success", "message": "Slot marked as cancelled."}