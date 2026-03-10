from datetime import datetime
from uuid import UUID
from typing import Optional

class ClientModel:
    def __init__(
        self,
        client_name: str,
        client_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.client_id = client_id
        self.client_name = client_name
        self.created_at = created_at
