from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from enum import Enum
from core.constants import SlotStatus

class SlotStatusEnum(str, Enum):
    AVAILABLE = SlotStatus.AVAILABLE
    BOOKED = SlotStatus.BOOKED
    BLOCKED = SlotStatus.BLOCKED
    CANCELLED = SlotStatus.CANCELLED

class AvailabilitySlotBase(BaseModel):
    professional_id: UUID
    date: str  # ISO format YYYY-MM-DD
    start_time: str  # HH:MM:SS
    end_time: str # HH:MM:SS
    status: SlotStatusEnum = SlotStatusEnum.AVAILABLE

class AvailabilitySlotCreate(AvailabilitySlotBase):
    pass

class AvailabilitySlotUpdate(BaseModel):
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[SlotStatusEnum] = None

class AvailabilitySlot(AvailabilitySlotBase):
    slot_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True