from uuid import UUID
from supabase import Client

class ClientRepository:
    @staticmethod
    def get_client_bookings(db: Client, client_id: UUID):
        return db.table("bookings")\
            .select("*, availability_slots(date, start_time, end_time)")\
            .eq("client_id", str(client_id))\
            .order("date", desc=True)\
            .execute()

    @staticmethod
    def search_clients_by_name(db: Client, name: str):
        return db.table("clients")\
            .select("client_id, client_name")\
            .ilike("client_name", f"%{name}%")\
            .execute()
