from supabase import Client
from uuid import UUID
from fastapi import HTTPException
from core.constants import ErrorMessages
from db.repositories.client_repository import ClientRepository


class ClientService:
    @staticmethod
    def get_client_bookings(db: Client, client_id: UUID):
        """
        Requirement 7.8: Output shall include upcoming and past bookings, 
        date/time, and status.
        """
        # Fetching bookings joined with slot details for time/date
        result = ClientRepository.get_client_bookings(db, client_id)

        if not result.data:
            return {"message": "No bookings found for this client.", "entries": []}

        return {
            "client_id": str(client_id),
            "entries": result.data
        }

    @staticmethod
    def get_client_by_name(db: Client, name: str):
        """
        Requirement 13: Error handling for 'No client matched that name'.
        Supports the Chatbot's need to find a client ID from a natural language name.
        """
        # Using 'ilike' for case-insensitive partial matching (fuzzy search)
        result = ClientRepository.search_clients_by_name(db, name)

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=ErrorMessages.CLIENT_NOT_FOUND
            )

        # If multiple matches found, the Chatbot logic (Requirement 8.3)
        # will ask for clarification.
        return {
            "count": len(result.data),
            "clients": result.data
        }
