import asyncio
import os
import sys
import logging
from uuid import UUID

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from app package
from db.supabase import supabase
from services.chatbot_service import ChatbotService
from schemas.chatbot import ChatRequest

# Set logging to INFO so we see the "LLM Tool Call" logs in the console
logging.basicConfig(level=logging.INFO)

async def test_chatbot_service():
    print("\n" + "="*60)
    print("🚀 MIRROR ASSISTANT: FULL AGENTIC ACTION TEST")
    print("="*60)

    TEST_PROF_ID = "550e8400-e29b-41d4-a716-446655440000"

    # Scenarios designed to trigger Multi-Step Tool Reasoning
    test_scenarios = [
    
    "What does my schedule look like for tomorrow?",
    "Please open a new availability slot for tomorrow morning from 9:00 AM to 12:00 PM.",
    "Actually, open another slot tomorrow from 11:00 AM to 2:00 PM.",
    "Okay, instead of that, open a slot on the day after tomorrow from 3 PM to 6 PM.",
    "Can you book a 60-minute session for 'Jon Miror' tomorrow starting at 10 AM?",
    "Oh, Sorry i meant John Mirror, book a 30-min session for him tomorrow at 10AM",
    "I also need to see Bishal tomorrow at 10 AM. Book him in.",
    "Since 10 AM is taken, book Bishal tomorrow at 11 AM instead.",
    "Show me all my upcoming bookings for the rest of the week.",
    "Something came up. Move Bishal's appointment to the day after tomorrow at 4 PM.",
    "Can you open a slot for yesterday from 2 PM to 4 PM?",
    "Cancel the appointment with John Mirror for tomorrow.",
    "Delete my availability slot.",
    "Sorry, I meant delete the availability slot for tomorrow morning."
]

    for msg in test_scenarios:
        print(f"\n💬 [USER]: {msg}")
        
        request_data = ChatRequest(
            message=msg,
            professional_id=TEST_PROF_ID,
            session_id="test-session-123"
        )

        try:
            # Full flow: API Request -> Service -> Agent -> Tools -> DB -> Response Builder
            response = await ChatbotService.process_message(supabase, request_data)
            
            print(f"🤖 [AI]: {response.reply}")
            print(f"🎯 [INTENT]: {response.intent}")
            print(f"⚡ [ACTION TAKEN]: {response.action_suggested}")
            
        except Exception as e:
            # This captures validation errors or DB constraint failures
            print(f"❌ [SYSTEM ERROR]: {str(e)}")

    print("\n" + "=")
    print("🏁 TEST SUITE COMPLETED")
    print("=")

if __name__ == "__main__":
    asyncio.run(test_chatbot_service())