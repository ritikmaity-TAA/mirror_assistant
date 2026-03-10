from uuid import UUID
from fastapi import HTTPException
from supabase import Client

class ClientService:
    @staticmethod
    def get_client_bookings(db: Client, client_id: UUID):
        """
        Requirement 7.8: Output shall include upcoming and past bookings, 
        date/time, and status.
        """
        # Fetching bookings joined with slot details for time/date
        result = db.table("bookings")\
            .select("*, availability_slots(date, start_time, end_time)")\
            .eq("client_id", str(client_id))\
            .order("date", desc=True)\
            .execute()
        
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
        result = db.table("clients")\
            .select("client_id, client_name")\
            .ilike("client_name", f"%{name}%")\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404, 
                detail=f"No client matched the name '{name}'. Please try a different name."
            )
            
        # If multiple matches found, the Chatbot logic (Requirement 8.3) 
        # will ask for clarification.
        return {
            "count": len(result.data),
            "clients": result.data
        }