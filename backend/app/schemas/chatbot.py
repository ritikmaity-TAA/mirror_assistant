from typing import Optional, List, Dict
from uuid import UUID
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str # user or assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    professional_id: UUID # Changed to UUID for industry consistency
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    action_suggested: Optional[bool] = False