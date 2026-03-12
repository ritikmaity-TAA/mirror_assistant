import logging
from uuid import UUID
from supabase import Client
from schemas.chatbot import ChatRequest, ChatResponse
from agents.workflow_manager import workflow_manager
from db.repositories.chatbot_repository import ChatbotRepository

# Initialize logger for tracking AI decisions
logger = logging.getLogger(__name__)


class ChatbotService:
    @staticmethod
    async def process_message(db: Client, request: ChatRequest) -> ChatResponse:
        """
        Requirement 5 & 8: Main entry point for the conversational interface.
        This service delegates the natural language interpretation to the 
        Workflow Manager and returns the structured response.
        """
        try:
            # 1. Fetch memory strictly for the current session
            chat_history = ChatbotRepository.get_session_history(
                db=db,
                session_id=request.session_id,
                professional_id=request.professional_id,
                limit=10  # Remembers the last 10 interactions
            )

            # 2. Save user message BEFORE processing so it's recorded even if the
            #    AI call fails mid-way — prevents session gaps on crash/restart.
            ChatbotRepository.save_message(
                db=db,
                professional_id=request.professional_id,
                session_id=request.session_id,
                role="user",
                content=request.message
            )

            # 3. Execute AI Workflow with injected memory
            ai_output = await workflow_manager.handle_message(
                db=db,
                message=request.message,
                professional_id=request.professional_id,
                chat_history=chat_history
            )

            final_reply = ai_output.get("reply", "I'm sorry, I couldn't process that request.")

            # 4. Save AI response only after successful processing
            ChatbotRepository.save_message(
                db=db,
                professional_id=request.professional_id,
                session_id=request.session_id,
                role="assistant",
                content=final_reply
            )

            # 5. Response Construction:
            # Matches the ChatResponse schema: reply, intent, and action_suggested flag.
            return ChatResponse(
                reply=final_reply,
                intent=ai_output.get("intent", "unknown"),
                action_suggested=ai_output.get("action_suggested", False)
            )

        except Exception as e:
            # Requirement 13: Action-oriented error handling
            logger.error(f"Chatbot Error: {str(e)}")
            return ChatResponse(
                reply="I encountered a technical issue while processing your request. Please try again or check your schedule manually.",
                intent="error",
                action_suggested=False
            )