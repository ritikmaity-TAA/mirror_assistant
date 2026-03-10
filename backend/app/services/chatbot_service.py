import logging
from supabase import Client
from schemas.chatbot import ChatRequest, ChatResponse
from agents.workflow_manager import workflow_manager

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
            # 1. Logic Delegation:
            # We send the raw message and professional context to the AI Agent.
            # The agent will use tool calling to hit your other services (Booking/Schedule).
            ai_output = await workflow_manager.handle_message(
                db=db,
                message=request.message,
                professional_id=request.professional_id
            )

            # 2. Response Construction:
            # Matches the ChatResponse schema: reply, intent, and action_suggested flag.
            return ChatResponse(
                reply=ai_output.get(
                    "reply", "I'm sorry, I couldn't process that request."),
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
