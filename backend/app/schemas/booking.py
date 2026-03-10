from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class BookingBase(BaseModel):
    professional_id: UUID
    client_id: UUID
    slot_id: Optional[UUID] = None
    date: str
    start_time: str
    end_time: str
    status: str = "scheduled"
    booking_note: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    client_id: Optional[UUID] = None
    date: Optional[str] = None
    time: Optional[str] = None # Added for flexibility in edit
    slot_id: Optional[UUID] = None
    status: Optional[str] = None
    booking_note: Optional[str] = None

class Booking(BookingBase):
    booking_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
