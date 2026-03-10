from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ClientBase(BaseModel):
    client_name: str

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    client_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
