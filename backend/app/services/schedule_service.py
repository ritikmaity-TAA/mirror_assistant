from uuid import UUID
from fastapi import HTTPException
from schemas.schedule import AvailabilitySlotCreate, AvailabilitySlotUpdate
from utils.datetime_utils import is_past_date, validate_time_range
from core.constants import ErrorMessages, SlotStatus
from db.repositories.schedule_repository import ScheduleRepository
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
        existing_slots = ScheduleRepository.get_slots_by_professional_and_date(
            db, slot.professional_id, slot.date
        )
        for existing in existing_slots.data:
            if (slot.start_time < existing['end_time']) and (slot.end_time > existing['start_time']):
                raise HTTPException(
                    status_code=409, 
                    detail=f"{ErrorMessages.OVERLAP_DETECTED} ({existing['start_time']}-{existing['end_time']})"
                )

        result = ScheduleRepository.create_slot(db, slot.dict())
        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def get_day_schedule(db: Client, professional_id: UUID, date_str: str):
        # Req 7.7: Ordered day timeline
        slots = ScheduleRepository.get_day_schedule(db, professional_id, date_str)
        return {"date": date_str, "entries": slots.data}

    @staticmethod
    def update_slot(db: Client, slot_id: UUID, slot: AvailabilitySlotUpdate):
        # Business logic for updates (e.g., prevent updating booked slots)
        existing = ScheduleRepository.get_slot_by_id(db, slot_id)
        if existing.data and existing.data['status'] == SlotStatus.BOOKED:
            raise HTTPException(status_code=400, detail="Cannot update a slot that is already booked.")
            
        result = ScheduleRepository.update_slot_status(db, slot_id, slot.status)
        return {"status": "success", "data": result.data[0]}

    @staticmethod
    def delete_slot(db: Client, slot_id: UUID):
        # Requirements might vary, but usually deleting a slot reopens it or removes it
        # For now, we'll just remove/cancel it
        result = ScheduleRepository.update_slot_status(db, slot_id, SlotStatus.CANCELLED)
        return {"status": "success", "message": "Slot marked as cancelled."}