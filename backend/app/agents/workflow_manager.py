import asyncio
import json
import logging
from uuid import UUID
from typing import Dict, Any, List

from supabase import Client

# Using absolute imports matching the mirror_assistant_backend/app structure
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
        return (
            "You are an empathetic, efficient AI assistant managing a mental health professional's schedule. "
            "Use the provided tools to manage availability slots, handle bookings, and look up schedules or clients. "
            "If asked to create a booking but you don't have the client's ID, search for the client first. "
            "If asked to book a time but you don't know the slot ID, fetch the day's schedule first to find an available slot. "
            "Always be concise, confirm actions clearly, and guide the user if validation fails."
        )

    async def handle_message(self, db: Client, message: str, professional_id: UUID) -> Dict[str, Any]:
        """
        Main entry point for ChatbotService.
        Executes the Agentic Loop with Multi-Tool Support.
        """
        client = await groqclient.get_client()
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message},
        ]

        # Map tool names to lambda wrappers that handle Pydantic model creation and dependency injection
        available_functions = {
            "get_day_schedule": lambda date_str: ScheduleService.get_day_schedule(db, professional_id, date_str),
            "search_client_by_name": lambda name: ClientService.get_client_by_name(db, name),
            "create_slot": lambda date, start_time, end_time: ScheduleService.create_slot(
                db, AvailabilitySlotCreate(professional_id=professional_id, date=date, start_time=start_time, end_time=end_time)
            ),
            "delete_slot": lambda slot_id: ScheduleService.delete_slot(db, UUID(slot_id)),
            "create_booking": lambda client_id, slot_id, date, start_time, end_time, booking_note="": BookingService.create_booking(
                db, BookingCreate(professional_id=professional_id, client_id=UUID(client_id), slot_id=UUID(slot_id), date=date, start_time=start_time, end_time=end_time, booking_note=booking_note)
            ),
            "delete_booking": lambda booking_id: BookingService.cancel_booking(db, UUID(booking_id)),
            "get_upcoming_bookings": lambda: BookingService.get_upcoming_bookings(db, professional_id)
        }

        executed_tools_history: List[str] = []
        iteration = 0

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=PRODUCTION_TOOLS,
                tool_choice="auto"
            )

            while response.choices[0].message.tool_calls and iteration < self.max_iterations:
                iteration += 1
                response_message = response.choices[0].message
                messages.append(response_message)

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    executed_tools_history.append(function_name)

                    logger.info(f"LLM Tool Call: {function_name}({function_args})")

                    try:
                        func_to_call = available_functions.get(function_name)
                        if not func_to_call:
                            raise ValueError(f"Function {function_name} not implemented.")
                        
                        # Note: In heavy production, wrap blocking I/O db calls in asyncio.to_thread()
                        function_result = func_to_call(**function_args)
                        result_str = json.dumps(function_result, default=str)
                        
                    except Exception as e:
                        logger.warning(f"Tool execution failed ({function_name}): {str(e)}")
                        # Feed the error back to the LLM so it can correct the user
                        result_str = json.dumps({"error": str(e)})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result_str,
                    })

                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=PRODUCTION_TOOLS,
                    tool_choice="auto",
                )

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
