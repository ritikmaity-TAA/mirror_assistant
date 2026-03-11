from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
import logging
from schemas.schedule import AvailabilitySlotCreate, AvailabilitySlotUpdate
from services.schedule_service import ScheduleService
from api.dependencies import get_supabase_client
from supabase import Client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.post("/slots", response_model=dict)
def create_slot(slot: AvailabilitySlotCreate, db: Client = Depends(get_supabase_client)):
    try:
        return ScheduleService.create_slot(db, slot)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in create_slot: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Slot creation failed")

@router.put("/slots/{slot_id}", response_model=dict)
def update_slot(slot_id: UUID, slot: AvailabilitySlotUpdate, db: Client = Depends(get_supabase_client)):
    try:
        return ScheduleService.update_slot(db, slot_id, slot)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating slot {slot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Slot update failed")

@router.delete("/slots/{slot_id}", response_model=dict)
def delete_slot(slot_id: UUID, db: Client = Depends(get_supabase_client)):
    try:
        return ScheduleService.delete_slot(db, slot_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting slot {slot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Slot deletion failed")

@router.get("/day", response_model=dict)
def get_day_schedule(professional_id: UUID = Query(...), date: str = Query(...), db: Client = Depends(get_supabase_client)):
    try:
        return ScheduleService.get_day_schedule(db, professional_id, date)
    except Exception as e:
        logger.error(f"Error fetching schedule for {date}: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve schedule")