from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str # user or assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    professional_id: UUID # Changed to UUID for industry consistency
    session_id: str
    history: Optional[List[ChatMessage]] = []

# ---------------------------------------------------------------------------
# Display payload models — consumed by the frontend for structured rendering.
# The frontend reads `metadata.display.type` and renders the appropriate
# component. The AI never writes HTML; it only produces text in `reply`.
# ---------------------------------------------------------------------------

class SlotDisplayItem(BaseModel):
    slot_id: str
    date: str
    start_time: str
    end_time: str
    status: str

class BookingDisplayItem(BaseModel):
    booking_id: str
    slot_id: str
    client_id: str          # frontend uses this to fetch full client details
    client_name: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    note: Optional[str] = None
    status: Optional[str] = None

class DisplayPayload(BaseModel):
    type: Literal[
        "day_schedule",       # get_day_schedule result
        "booking_list",       # get_upcoming_bookings result
        "slot_created",       # create_slot confirmation
        "slot_deleted",       # delete_slot confirmation
        "booking_created",    # create_booking confirmation
        "booking_cancelled",  # delete_booking confirmation
        "client_search",      # search_client_by_name result (multiple matches)
    ]
    items: Optional[List[Dict[str, Any]]] = None    # list views
    item: Optional[Dict[str, Any]] = None           # single-record confirmations

class ChatMetadata(BaseModel):
    last_action: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    display: Optional[DisplayPayload] = None        # structured UI payload

class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    action_suggested: Optional[bool] = False
    metadata: Optional[ChatMetadata] = None