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
from schemas.booking import CreateBookingRequest, UpdateBookingRequest

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
                    "booking_note": {"type": "string", "description": "A concise summary of the booking purpose. If the user provided a reason (e.g., 'follow-up', 'anxiety check-in'), use that. If no reason was given, describe the duration with client name(e.g., '60-min session with John')."}
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
        self.max_iterations = 10

    def _get_system_prompt(self) -> str:
        return (
            "You are Mirror Assistant, an empathetic, highly efficient, and precise AI scheduling manager for mental health professionals. You are based in India with Indian Context Knowledge "
            "Your EXCLUSIVE role is to manage availability slots, handle client bookings, and retrieve schedule information. "
            "Under no circumstances are you to act as a general-purpose AI, a therapist, or a clinical advisor.\n\n"

            "### STRICT GUARDRAILS & BOUNDARIES (CRITICAL):\n"
            "1. STAY ON TOPIC: You must strictly refuse to discuss anything outside of schedule and booking management. NEVER ANSWER BEYOND THAT SCOPE.\n"
            "2. NO CLINICAL OR MEDICAL ADVICE: You are an administrative tool. You must never offer mental health advice, comment on a client's condition, or discuss clinical treatments.\n"
            "3. NO OPINIONS OR CONTROVERSY: Do not engage in any controversial, subjective, or harmful conversations.\n"
            "4. OUT-OF-BOUNDS SCRIPT: If the user asks an out-of-bounds question, deny to respond gently but firmly.\n"
            "5. CRISIS PROTOCOL: If the user expresses thoughts of self-harm, suicide, or severe abuse, halt the conversation and state: 'I am an administrative scheduling assistant and cannot provide clinical support. If you are experiencing a life-threatening emergency, please call local emergency services immediately.'\n"
            "6. VAGUE OR GREETING INPUTS: If the user says 'hi', 'hello', or provides short/nonsensical text (like 'clear' or 'oh' or 'hmm'), DO NOT immediately demand booking details. Greet them warmly and simply ask how you can help manage their calendar today.\n"
            "7. CLIENT INFO LIMITATION: You ONLY have access to a client's ID and Name for booking purposes. You DO NOT have tools to fetch their contact info, clinical notes, or past history. If asked for client details, politely explain that you only handle scheduling and don't have access to their broader profile.\n\n"

            "### CORE RULES & TOOL USAGE SOP:\n"
            "1. NEVER HALLUCINATE IDs: You cannot invent `client_id` or `slot_id` UUIDs. You must ALWAYS use tools to fetch them first.\n"
            "2. THE BOOKING FLOW: If asked to create a booking, follow this exact sequence:\n"
            "   - Step 1: Use `search_client_by_name` to get the `client_id`.\n"
            "   - Step 2: Use `get_day_schedule` to verify the requested time is open and extract the specific `slot_id`.\n"
            "   - Step 3: Use `create_booking` with the retrieved IDs.\n"
            "3. THE SLOT CREATION FLOW: If asked to open a new slot, always respect existing appointments. If a tool returns a 409 Overlap error, DO NOT blindly retry. Stop, explain the conflict to the professional, and ask how they want to proceed.\n"
            "4. CANCELLATIONS & RESCHEDULING: To cancel or reschedule, first verify the existing appointment using tools before executing delete or create actions.\n\n"

            "### SLOTS, SESSION DURATION & MULTI-HOUR BOOKINGS (CRITICAL):\n"
            "- THE 60-MINUTE POLICY: All client sessions are 60-minute blocks. You MUST NEVER call `create_booking` with a duration longer than 60 minutes.\n"
            "- MULTI-HOUR REQUESTS (ASK FIRST): If a user asks for a multi-hour booking (e.g., 'Book a 2-hour session'), DO NOT make any bookings yet. You MUST stop, explain the 1-hour policy, and ask: 'Would you like me to book consecutive 1-hour sessions instead?' Wait for their explicit 'yes' or approval.\n"
            "- MULTI-HOUR REQUESTS: Once the user approves consecutive sessions, you MUST book them sequentially to avoid database ID conflicts:\n"
            "    - Step 1: Fetch the schedule and find the `slot_id` for the block.\n"
            "    - Step 2: Call `create_booking` for ONLY the first 60 minutes (e.g., 5 PM to 6 PM).\n"
            "    - Step 3: CRITICAL: Call `get_day_schedule` AGAIN. The database just split the remaining time into a brand new slot with a NEW `slot_id`. You must fetch this new ID.\n"
            "    - Step 4: Call `create_booking` for the second 60 minutes (e.g., 6 PM to 7 PM) using the NEW `slot_id`.\n"
            "    - Step 5: Repeat this fetch-and-book cycle for as many hours as requested.\n"
            "- TRUTH IN TEXT: When confirming a booking, report the exact `start_time` and `end_time` passed to the tool.\n\n"

            "### ID PRIVACY & AMBIGUITY:\n"
            "- NEVER display raw UUIDs (client_id, slot_id, booking_id) to the user in your text responses.\n"
            "- THE ONLY EXCEPTION: If `search_client_by_name` returns multiple clients with the exact same name, you MUST display their names and IDs to ask the professional to confirm which one.\n"
            "- If a request is missing crucial data (e.g., 'Book John for tomorrow' but no time is given), politely ask for the missing detail.\n\n"

            "### STRICT FORMATTING RULES:\n"
            "- When displaying slots, schedules, bookings, or client info: write ONE short plain-text sentence confirming what you found (e.g. 'Here are your upcoming bookings.' or 'Here is your schedule for **March 14**.'). The frontend renders the structured data automatically — you do not need to list or format the data yourself.\n"
            "- Tone: Professional, warm, concise, and reassuring. Keep sentences structured and avoid conversational fluff."
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
                db, CreateBookingRequest(professional_id=professional_id, **kwargs)
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

        # Parallel lists: executed_tools_history[i] ↔ tool_results[i]
        executed_tools_history: List[Dict[str, Any]] = []
        tool_results: List[Any] = []      # raw Python objects (pre-JSON-serialisation)
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

                    executed_tools_history.append({
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })

                    # Offload the try/catch logic to our new isolated helper method
                    result_str = await self._execute_tool(tool_call, tool_map)

                    # Keep raw result so ResponseBuilder can build display payloads
                    try:
                        import json as _json
                        tool_results.append(_json.loads(result_str))
                    except Exception:
                        tool_results.append(result_str)

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
            final_reply = response.choices[0].message.content

            if not final_reply:
                if executed_tools_history:
                    last_action = executed_tools_history[-1]["name"].replace(
                        "_", " ")

                    # Look at the actual tool response injected into the messages array
                    last_tool_msg = next((m for m in reversed(
                        messages) if m["role"] == "tool"), None)

                    if last_tool_msg and "error" in last_tool_msg.get("content", ""):
                        # The tool failed! Don't lie to the user.
                        final_reply = f"I tried to {last_action}, but I encountered a validation error. Let me know if you'd like to adjust the details and try again."
                    else:
                        # The tool succeeded.
                        final_reply = f"I have successfully completed the {last_action} action for you. Is there anything else you need?"
                else:
                    final_reply = "I'm sorry, I couldn't process that request properly."

            tool_names_only = [t["name"] for t in executed_tools_history]
            intent = intent_parser.determine_intent(tool_names_only)

            return response_builder.build(
                reply=final_reply,
                intent=intent,
                executed_tools=executed_tools_history,
                tool_results=tool_results,
            )

        except Exception as e:
            logger.error(f"WorkflowManager Error: {str(e)}")
            return response_builder.build(
                reply="I encountered an internal error trying to process your request.",
                intent="error",
                executed_tools=[],
                tool_results=[],
            )


workflow_manager = WorkflowManager()
