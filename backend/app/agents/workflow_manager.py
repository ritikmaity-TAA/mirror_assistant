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
        return (
            "You are an empathetic, efficient AI assistant managing a mental health professional's schedule. "
            "Use the provided tools to manage availability slots, handle bookings, and look up schedules or clients. "
            "If asked to create a booking but you don't have the client's ID, search for the client first. "
            "If asked to book a time but you don't know the slot ID, fetch the day's schedule first to find an available slot. "
            "Always be concise, confirm actions clearly, and guide the user if validation fails."
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
                db, AvailabilitySlotCreate(professional_id=professional_id, **kwargs)
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
            error_details = [{"field": err["loc"][-1], "issue": err["msg"]} for err in e.errors()]
            logger.warning(f"Pydantic validation failed for {function_name}: {error_details}")
            return json.dumps({"error": "Parameter validation failed", "details": error_details})

        except Exception as e:
            # Catch HTTPExceptions (like your 409 overlaps) or generic Python errors
            logger.warning(f"Tool execution failed ({function_name}): {str(e)}")
            return json.dumps({"error": str(e)})

    async def handle_message(self, db: Client, message: str, professional_id: UUID) -> Dict[str, Any]:
        """
        Main entry point for ChatbotService.
        Executes the Agentic Loop with Multi-Tool Support.
        """
        client = await groqclient.get_client()
        
        messages = [{"role": "system", "content": self._get_system_prompt()}, {"role": "user", "content": message}]
        
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