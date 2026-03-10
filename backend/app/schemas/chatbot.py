from typing import Optional, List
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str # user or assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    professional_id: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    action_suggested: Optional[bool] = False
