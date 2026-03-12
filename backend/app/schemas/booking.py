from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum
from core.constants import BookingStatus

class BookingStatusEnum(str, Enum):
    SCHEDULED = BookingStatus.SCHEDULED
    RESCHEDULED = BookingStatus.RESCHEDULED
    CANCELLED = BookingStatus.CANCELLED
    COMPLETED = BookingStatus.COMPLETED
    NO_SHOW = BookingStatus.NO_SHOW

class BookingBase(BaseModel):
    professional_id: UUID
    client_id: UUID
    slot_id: UUID  # Mandatory per Req 11.c
    date: str      # YYYY-MM-DD
    start_time: str # HH:MM:SS
    end_time: str   # HH:MM:SS
    status: BookingStatusEnum = BookingStatusEnum.SCHEDULED
    booking_note: Optional[str] = ""

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    client_id: Optional[UUID] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_id: Optional[UUID] = None
    status: Optional[BookingStatusEnum] = None
    booking_note: Optional[str] = None

class Booking(BookingBase):
    booking_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True