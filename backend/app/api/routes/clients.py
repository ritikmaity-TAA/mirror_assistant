from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
import logging
from services.client_service import ClientService
from api.dependencies import get_supabase_client
from supabase import Client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedule/client", tags=["Clients"])

@router.get("/{client_id}", response_model=dict)
def get_client_bookings(client_id: UUID, db: Client = Depends(get_supabase_client)):
    try:
        return ClientService.get_client_bookings(db, client_id)
    except Exception as e:
        logger.error(f"Error fetching bookings for client {client_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Client not found or no bookings exist")

@router.get("/search/name", response_model=dict)
def search_client(name: str, db: Client = Depends(get_supabase_client)):
    try:
        return ClientService.get_client_by_name(db, name)
    except Exception as e:
        logger.error(f"Client search failed for {name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")