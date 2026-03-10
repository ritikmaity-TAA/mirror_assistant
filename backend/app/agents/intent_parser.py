import logging
from typing import List

logger = logging.getLogger(__name__)

class IntentParser:
    """
    Analyzes the conversation history and tool calls to determine the user's primary intent.
    """
    
    # Mapping of tool names to business intents based on Todo.md Req 7
    TOOL_INTENT_MAP = {
        "create_slot": "open_slot",
        "update_slot": "edit_slot",
        "delete_slot": "delete_slot",
        "create_booking": "create_booking",
        "update_booking": "edit_booking",
        "delete_booking": "delete_booking",
        "get_day_schedule": "check_day_schedule",
        "get_client_bookings": "check_client_schedule",
        "get_upcoming_bookings": "check_upcoming_bookings",
        "search_client_by_name": "client_search"
    }

    @staticmethod
    def determine_intent(tool_calls_history: List[str]) -> str:
        """
        Derives the intent based on the executed tools. If no tools were called,
        defaults to a general inquiry.
        """
        if not tool_calls_history:
            return "general_inquiry"

        # Use the most significant/latest tool called to determine the primary intent
        primary_tool = tool_calls_history[-1]
        intent = IntentParser.TOOL_INTENT_MAP.get(primary_tool, "unknown_action")
        
        logger.debug(f"Parsed intent '{intent}' from tool history: {tool_calls_history}")
        return intent

intent_parser = IntentParser()