from datetime import datetime
from uuid import UUID
from typing import Optional
from app.core.constants import SlotStatus

class AvailabilitySlotModel:
    def __init__(
        self,
        professional_id: UUID,
        date: str,
        start_time: str,
        end_time: str,
        slot_id: Optional[UUID] = None,
        # Using constant for default value
        status: str = SlotStatus.AVAILABLE,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.slot_id = slot_id
        self.professional_id = professional_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """Standardizing for Supabase JSON conversion"""
        return {k: str(v) if isinstance(v, UUID) else v for k, v in self.__dict__.items() if v is not None}