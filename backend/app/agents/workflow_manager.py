import asyncio
import json
import logging
from uuid import UUID
from typing import Dict, Any, List
from pydantic import ValidationError
from supabase import Client

from core.config import MODEL_NAME
from services.ai_service import groqclient
from services.schedule_service import ScheduleService
from services.client_service import ClientService
from services.booking_service import BookingService
from agents.intent_parser import intent_parser
from agents.response_builder import response_builder
from schemas.schedule import AvailabilitySlotCreate, AvailabilitySlotUpdate
from schemas.booking import BookingCreate, BookingUpdate

logger = logging.getLogger(__name__)

# ============================================================================
# Tool Schemas for Production
# ============================================================================
PRODUCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_day_schedule",
            "description": "Fetch the professional's schedule and available slots for a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "The date to check in YYYY-MM-DD format (e.g., '2026-03-18')",
                    }
                },
                "required": ["date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_client_by_name",
            "description": "Search for a client's ID in the database using their name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The name of the client to search for."}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_slot",
            "description": "Open a new availability slot for the professional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format."},
                    "start_time": {"type": "string", "description": "Start time in HH:MM format."},
                    "end_time": {"type": "string", "description": "End time in HH:MM format."}
                },
                "required": ["date", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_slot",
            "description": "Delete or cancel an existing availability slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "string", "description": "The UUID of the slot to delete."}
                },
                "required": ["slot_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": "Create a new booking/appointment for a client in a specific slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "The UUID of the client."},
                    "slot_id": {"type": "string", "description": "The UUID of the available slot."},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format."},
                    "start_time": {"type": "string", "description": "Start time in HH:MM format."},
                    "end_time": {"type": "string", "description": "End time in HH:MM format."},
                    "booking_note": {"type": "string", "description": "Optional notes for the booking."}
                },
                "required": ["client_id", "slot_id", "date", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_booking",
            "description": "Cancel or delete an existing booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "The UUID of the booking to delete."}
                },
                "required": ["booking_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_bookings",
            "description": "Fetch the professional's upcoming scheduled sessions.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }
]


class WorkflowManager:
    def __init__(self):
        self.model = MODEL_NAME
        self.max_iterations = 5

    def _get_system_prompt(self) -> str:
        return ("You are Mirror Assistant, an empathetic, highly efficient, and precise AI scheduling manager for mental health professionals. "
                "Your EXCLUSIVE role is to manage availability slots, handle client bookings, and retrieve schedule information. "
                "Under no circumstances are you to act as a general-purpose AI, a therapist, or a clinical advisor.\n\n"

                "### STRICT GUARDRAILS & BOUNDARIES (CRITICAL):\n"
                "1. STAY ON TOPIC: You must strictly refuse to discuss anything outside of schedule and booking management. If the user asks about coding, politics, general knowledge, or weather, politely decline and pivot back to their schedule.\n"
                "2. NO CLINICAL OR MEDICAL ADVICE: You are an administrative tool. You must never offer mental health advice, comment on a client's condition, or discuss clinical treatments.\n"
                "3. NO OPINIONS OR CONTROVERSY: Do not engage in any controversial, subjective, or harmful conversations. Stick strictly to facts and data from the database.\n"
                "4. OUT-OF-BOUNDS SCRIPT: If the user asks an out-of-bounds question, respond gently but firmly with: 'I am specifically designed to assist with your scheduling and bookings. How can I help you manage your calendar today?'\n\n"

                "### CORE RULES & TOOL USAGE SOP:\n"
                "1. NEVER HALLUCINATE IDs: You cannot invent `client_id` or `slot_id` UUIDs. You must ALWAYS use tools to fetch them first.\n"
                "2. THE BOOKING FLOW: If asked to create a booking, follow this exact sequence:\n"
                "   - Step 1: Use `search_client_by_name` to get the `client_id`.\n"
                "   - Step 2: Use `get_day_schedule` to verify the requested time is open and extract the specific `slot_id`.\n"
                "   - Step 3: Use `create_booking` with the retrieved IDs.\n"
                "3. THE SLOT CREATION FLOW: If asked to open a new slot, always respect existing appointments. If a tool returns a 409 Overlap error, DO NOT blindly retry. Stop, explain the conflict to the professional, and ask how they want to proceed.\n"
                "4. CANCELLATIONS & RESCHEDULING: To cancel or reschedule, first verify the existing appointment using tools before executing delete or create actions.\n\n"

                "### HANDLING AMBIGUITY & ERRORS:\n"
                "- If a client search returns multiple results, ask the professional to clarify which client they meant.\n"
                "- If the professional's request is missing crucial data (e.g., 'Book John for tomorrow' but no time is given), politely ask for the missing detail.\n"
                "- If a tool validation fails, calmly explain the exact issue to the user and offer a logical next step.\n\n"

                "### TONE & FORMATTING:\n"
                "- Tone: Professional, warm, concise, and reassuring. Do not be overly chatty.\n"
                "- Formatting: Use clear Markdown. Use bullet points for lists and bold text to highlight dates, times, and client names."
                )

    def _get_tool_map(self, db: Client, professional_id: UUID) -> Dict[str, callable]:
        """
        Encapsulates the dependency injection and routes LLM tool calls to the correct services.
        Uses **kwargs to seamlessly unpack LLM arguments into Pydantic models.
        """
        return {
            "get_day_schedule": lambda date_str, **kwargs: ScheduleService.get_day_schedule(db, professional_id, date_str),
            "search_client_by_name": lambda name, **kwargs: ClientService.get_client_by_name(db, name),
            "create_slot": lambda **kwargs: ScheduleService.create_slot(
                db, AvailabilitySlotCreate(
                    professional_id=professional_id, **kwargs)
            ),
            "delete_slot": lambda slot_id, **kwargs: ScheduleService.delete_slot(db, UUID(slot_id)),
            "create_booking": lambda **kwargs: BookingService.create_booking(
                db, BookingCreate(professional_id=professional_id, **kwargs)
            ),
            "delete_booking": lambda booking_id, **kwargs: BookingService.cancel_booking(db, UUID(booking_id)),
            "get_upcoming_bookings": lambda **kwargs: BookingService.get_upcoming_bookings(db, professional_id)
        }

    async def _execute_tool(self, tool_call, tool_map: Dict[str, callable]) -> str:
        """
        Executes a single tool safely and formats the output/errors for the LLM context window.
        """
        function_name = tool_call.function.name
        try:
            function_args = json.loads(tool_call.function.arguments)
            logger.info(f"LLM Tool Call: {function_name}({function_args})")

            func_to_call = tool_map.get(function_name)
            if not func_to_call:
                return json.dumps({"error": f"Function '{function_name}' not implemented."})

            result = func_to_call(**function_args)

            if asyncio.iscoroutine(result):
                function_result = await result
            else:
                function_result = result

            return json.dumps(function_result, default=str)

        except ValidationError as e:
            # Format Pydantic errors so the AI knows exactly which parameter it messed up
            error_details = [{"field": err["loc"][-1],
                              "issue": err["msg"]} for err in e.errors()]
            logger.warning(
                f"Pydantic validation failed for {function_name}: {error_details}")
            return json.dumps({"error": "Parameter validation failed", "details": error_details})

        except Exception as e:
            # Catch HTTPExceptions (like your 409 overlaps) or generic Python errors
            logger.warning(
                f"Tool execution failed ({function_name}): {str(e)}")
            return json.dumps({"error": str(e)})

    async def handle_message(self, db: Client, message: str, professional_id: UUID, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Main entry point for ChatbotService.
        Executes the Agentic Loop with Multi-Tool Support.
        """
        client = await groqclient.get_client()

        messages = [{"role": "system", "content": self._get_system_prompt()}]

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": message})

        # Generate the tool routing map once per request
        tool_map = self._get_tool_map(db, professional_id)

        executed_tools_history: List[str] = []
        iteration = 0

        try:
            # Initial LLM Assessment
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=PRODUCTION_TOOLS,
                tool_choice="auto"
            )

            # Agentic Tool Execution Loop
            while response.choices[0].message.tool_calls and iteration < self.max_iterations:
                iteration += 1
                response_message = response.choices[0].message
                messages.append(response_message)

                for tool_call in response_message.tool_calls:
                    executed_tools_history.append(tool_call.function.name)

                    # Offload the try/catch logic to our new isolated helper method
                    result_str = await self._execute_tool(tool_call, tool_map)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result_str,
                    })

                # Re-evaluate with the new tool context
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=PRODUCTION_TOOLS,
                    tool_choice="auto",
                )

            # Final Processing
            final_reply = response.choices[0].message.content or "I have processed your request."
            intent = intent_parser.determine_intent(executed_tools_history)

            return response_builder.build(final_reply, intent, bool(executed_tools_history))

        except Exception as e:
            logger.error(f"WorkflowManager Error: {str(e)}")
            return response_builder.build(
                reply="I encountered an internal error trying to process your request.",
                intent="error",
                tools_executed=False
            )


workflow_manager = WorkflowManager()
