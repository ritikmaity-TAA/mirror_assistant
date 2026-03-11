from fastapi import APIRouter, Depends, HTTPException
import logging
from schemas.chatbot import ChatRequest, ChatResponse
from services.chatbot_service import ChatbotService
from api.dependencies import get_supabase_client
from supabase import Client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/message", response_model=ChatResponse)
async def post_message(request: ChatRequest, db: Client = Depends(get_supabase_client)):
    try:
        return await ChatbotService.process_message(db, request)
    except Exception as e:
        logger.error(f"Chatbot processing error: {str(e)}")
        # Requirement 13: User readable error
        return ChatResponse(
            reply="I'm sorry, I'm having trouble connecting to my brain right now. Please try again in a moment.",
            intent="error",
            action_suggested=False
        )