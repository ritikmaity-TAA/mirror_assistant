import logging
from uuid import UUID
from supabase import Client
from schemas.chatbot import ChatRequest, ChatResponse
from agents.workflow_manager import workflow_manager
from db.repositories.chatbot_repository import ChatbotRepository

logger = logging.getLogger(__name__)

class ChatbotService:
    @staticmethod
    async def process_message(db: Client, request: ChatRequest) -> ChatResponse:
        try:
            
            message_clean = request.message.lower().strip()

            # 1. Define Synonym Groups
            BOOKING_SYNONYMS = ["booking", "appointment", "session", "meeting", "reserve", "Book"]
            SLOT_SYNONYMS = ["slot", "availability", "open hours", "schedule window",]

            # 2. Check which group the user's message belongs to
            target_intent = None
            if any(syn in message_clean for syn in BOOKING_SYNONYMS):
                target_intent = "booking"
            elif any(syn in message_clean for syn in SLOT_SYNONYMS):
                target_intent = "slot"

            # 3. If it's a "Naked Keyword" (Short message like "appointment" or "session")
            if target_intent and len(message_clean.split()) <= 2:
                gateways = {
                    "booking": {
                        "reply": "I can help with your **appointments**. Would you like to **create** a new session, **view** your upcoming bookings, or **cancel** one?",
                        "intent": "booking_menu"
                    },
                    "slot": {
                        "reply": "I'm ready to manage your **availability**. Do you want to **open** a new slot, **view** current windows, or **modify** one?",
                        "intent": "slot_menu"
                    }
                }
                
                logger.info(f"Gateway hit for synonym: {message_clean} -> {target_intent}")
                
                # Save & Return
                ChatbotRepository.save_message(db, request.professional_id, request.session_id, "user", request.message)
                ChatbotRepository.save_message(db, request.professional_id, request.session_id, "assistant", gateways[target_intent]["reply"])
                
                return ChatResponse(
                    reply=gateways[target_intent]["reply"],
                    intent=gateways[target_intent]["intent"],
                    action_suggested=True
                )

            # --- STEP 1: Fetch memory (Standard Flow) ---
            chat_history = ChatbotRepository.get_session_history(
                db=db, 
                session_id=request.session_id, 
                limit=10 
            )

            # --- STEP 2: Execute AI Workflow ---
            ai_output = await workflow_manager.handle_message(
                db=db,
                message=request.message,
                professional_id=request.professional_id,
                chat_history=chat_history
            )

            final_reply = ai_output.get("reply", "I'm sorry, I couldn't process that request.")

            # --- STEP 3: Save interactions ---
            ChatbotRepository.save_message(db, request.professional_id, request.session_id, "user", request.message)
            ChatbotRepository.save_message(db, request.professional_id, request.session_id, "assistant", final_reply)

            return ChatResponse(
                reply=final_reply,
                intent=ai_output.get("intent", "unknown"),
                action_suggested=ai_output.get("action_suggested", False),
                metadata=ai_output.get("metadata", None)
            )

        except Exception as e:
            logger.error(f"Chatbot Error: {str(e)}")
            return ChatResponse(
                reply="I encountered a technical issue. Please try again or check your schedule manually.",
                intent="error",
                action_suggested=False
            )