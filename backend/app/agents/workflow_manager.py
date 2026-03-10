import asyncio
import json
import logging
from uuid import UUID
from typing import Dict, Any, List
from core.config import MODEL_NAME

from supabase import Client

# Import existing services and constants
from services.ai_service import groqclient
from services.schedule_service import ScheduleService
from services.client_service import ClientService
from agents.intent_parser import intent_parser
from agents.response_builder import response_builder

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
                        "description": "The date to check in YYYY-MM-DD format (e.g., '2026-03-10')",
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
                    "name": {
                        "type": "string",
                        "description": "The full or partial name of the client to search for.",
                    }
                },
                "required": ["name"],
            },
        },
    }
]


class WorkflowManager:
    def __init__(self):
        # Groq models specialized for tool use
        self.model = MODEL_NAME
        self.max_iterations = 5

    def _get_system_prompt(self) -> str:
        return (
            "You are a helpful AI assistant managing a professional's booking schedule. "
            "Use the provided tools to fetch schedules, find clients, and manage bookings. "
            "If a user asks for information you don't have, use a tool to fetch it. "
            "Always be concise and professional."
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

        # Tool Execution Map (Wraps your services to inject db & professional_id)
        # Note: In a true async environment, if your services do blocking I/O, 
        # consider wrapping them in asyncio.to_thread()
        available_functions = {
            "get_day_schedule": lambda date_str: ScheduleService.get_day_schedule(db, professional_id, date_str),
            "search_client_by_name": lambda name: ClientService.get_client_by_name(db, name)
        }

        executed_tools_history: List[str] = []
        iteration = 0

        try:
            # Initial LLM call
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=PRODUCTION_TOOLS,
                tool_choice="auto"
            )

            # Agentic Loop
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
                        # Execute the mapped service function
                        func_to_call = available_functions.get(function_name)
                        if not func_to_call:
                            raise ValueError(f"Function {function_name} not implemented.")
                        
                        function_result = func_to_call(**function_args)
                        result_str = json.dumps(function_result, default=str)
                        
                    except Exception as e:
                        logger.error(f"Tool execution error ({function_name}): {str(e)}")
                        result_str = json.dumps({"error": str(e)})

                    # Append tool result back to the LLM context
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result_str,
                    })

                # Call LLM again with tool results
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=PRODUCTION_TOOLS,
                    tool_choice="auto",
                )

            # Loop finished. Extract final answer.
            final_reply = response.choices[0].message.content or "I have processed your request."
            
            # Use auxiliary agents to format the final output
            intent = intent_parser.determine_intent(executed_tools_history)
            return response_builder.build(final_reply, intent, bool(executed_tools_history))

        except Exception as e:
            logger.error(f"WorkflowManager Error: {str(e)}")
            return response_builder.build(
                reply="I encountered an error trying to process your request.",
                intent="error",
                tools_executed=False
            )

workflow_manager = WorkflowManager()