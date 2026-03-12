import logging
from uuid import UUID
from typing import List, Dict
from supabase import Client

logger = logging.getLogger(__name__)

class ChatbotRepository:
    
    @staticmethod
    def save_message(db: Client, professional_id: UUID, session_id: str, role: str, content: str) -> bool:
        """Saves a single chat message to the database."""
        try:
            data = {
                "professional_id": str(professional_id), 
                "session_id": str(session_id),
                "role": str(role),
                "content": str(content)
            }
            db.table("chat_history").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save chat message to DB: {str(e)}")
            return False

    @staticmethod
    def get_session_history(db: Client, session_id: str, professional_id: UUID, limit: int = 10) -> List[Dict[str, str]]:
        """Fetches the last N messages for this specific session scoped to the professional.
        Filtering on both session_id AND professional_id prevents cross-professional
        history leakage in the unlikely event of a session_id collision.
        """
        try:
            response = db.table("chat_history") \
                .select("role, content") \
                .eq("session_id", str(session_id)) \
                .eq("professional_id", str(professional_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            # Reverse the list so it's chronologically correct (oldest -> newest)
            messages = response.data[::-1] if response.data else []
            return messages

        except Exception as e:
            logger.error(f"Failed to fetch chat history: {str(e)}")
            return []