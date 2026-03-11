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
    # ==========================================
    # PHASE 1: SYSTEM AWARENESS & SLOT CREATION
    # ==========================================
    
    # 1. READ: Baseline check
    # Tests: get_day_schedule, date parsing ("tomorrow")
    "What does my schedule look like for tomorrow?",
    
    # 2. WRITE: Standard slot creation
    # Tests: create_slot, time parsing (AM/PM)
    "Please open a new availability slot for tomorrow morning from 9:00 AM to 12:00 PM.",
    
    # 3. CONSTRAINT TEST: Overlapping Slot (Should Fail Gracefully)
    # Tests: AI's ability to catch the 409 Conflict error and explain it to the user.
    "Actually, open another slot tomorrow from 11:00 AM to 2:00 PM.",
    
    # 4. WRITE: Future slot creation (for later rescheduling tests)
    # Tests: create_slot, relative date parsing ("day after tomorrow")
    "Okay, instead of that, open a slot on the day after tomorrow from 3 PM to 6 PM.",

    # ==========================================
    # PHASE 2: BOOKING & FUZZY LOGIC
    # ==========================================
    
    # 5. MULTI-STEP: Fuzzy Search & Book
    # Tests: search_client_by_name (with a typo), get_day_schedule, create_booking
    "Can you book a 60-minute session for 'Jon Miror' tomorrow starting at 10 AM?",

    # 6. WRITE: Booking a slot with correct name
    "Oh, Sorry i meant John Mirror, book a 30-min session for him tomorrow at 10AM",
    
    # 7. CONSTRAINT TEST: Double Booking (Should Fail Gracefully)
    # Tests: create_booking conflict. AI should explain the slot is taken or there's an overlap.
    "I also need to see Bishal tomorrow at 10 AM. Book him in.",
    
    # 8. MULTI-STEP: Booking without explicit Date/Slot ID
    # Tests: AI logic. AI knows John Mirror is booked tomorrow, so it should infer the date/slot.
    "Since 10 AM is taken, book Bishal tomorrow at 11 AM instead.",

    # ==========================================
    # PHASE 3: COMPLEX REASONING & RESCHEDULING
    # ==========================================
    
    # 9. READ: Verify state
    # Tests: get_upcoming_bookings to ensure John Mirror and Bishal are in the system.
    "Show me all my upcoming bookings for the rest of the week.",
    
    # 10. MULTI-STEP: Reschedule (Delete + Create)
    # Tests: search_client_by_name, delete_booking, create_booking.
    "Something came up. Move Bishal's appointment to the day after tomorrow at 4 PM.",
    
    # 11. EDGE CASE: Past Date Action (Should Fail Gracefully)
    # Tests: Validation rules (Req 11). System should reject past actions.
    "Can you open a slot for yesterday from 2 PM to 4 PM?",

    # ==========================================
    # PHASE 4: CLEANUP & CANCELLATIONS
    # ==========================================
    
    # 12. DELETE: Standard cancellation
    # Tests: search_client_by_name, delete_booking
    "Cancel the appointment with John Mirror for tomorrow.",
    
    # 13. AMBIGUOUS DELETE: Lack of specific parameters
    # Tests: AI should ask a clarifying question ("Which slot?") rather than guessing.
    "Delete my availability slot.",
    
    # 14. EXACT DELETE: Proper cleanup
    # Tests: get_day_schedule, delete_slot
    "Sorry, I meant delete the availability slot for tomorrow morning."
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