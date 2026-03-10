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
        # 1. READ TEST
        "What is my current schedule for tomorrow?",
        
        # 2. CREATE SLOT (Write Action)
        "I want to open a new slot for tomorrow from 2 PM to 3 PM.",
        
        # 3. MULTI-STEP BOOKING (Search -> Fetch -> Book)
        "Can you book a session for John Kanis tomorrow at 2 PM?",
        
        # 4. VIEW UPCOMING (Verify the booking exists)
        "Show me all my upcoming bookings.",
        
        # 5. DELETE ACTION (Write Action)
        "Actually, cancel that booking I just made for John Kanis.",
        
        # 6. CLEANUP (Remove the availability slot)
        "Delete the availability slot for tomorrow at 2 PM."
    ]

    for msg in test_scenarios:
        print(f"\n💬 [USER]: {msg}")
        
        request_data = ChatRequest(
            message=msg,
            professional_id=TEST_PROF_ID
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