import logging
from typing import List

logger = logging.getLogger(__name__)

class IntentParser:
    """
    Analyzes the conversation history and tool calls to determine the user's primary intent.
    """
    
    # Mapping of tool names to business intents
    TOOL_INTENT_MAP = {
        "get_day_schedule": "check_schedule",
        "get_client_bookings": "check_client_history",
        "search_client_by_name": "client_search",
        "create_booking": "book_appointment",
        "cancel_booking": "cancel_appointment",
        "check_weather": "dummy_test" # Used for the dummy test
    }

    @staticmethod
    def determine_intent(self,tool_calls_history: List[str]) -> str:
        """
        Derives the intent based on the executed tools. If no tools were called,
        defaults to a general inquiry.
        """
        if not tool_calls_history:
            return "general_inquiry"

        # Use the most significant/latest tool called to determine the primary intent
        primary_tool = tool_calls_history[-1]
        intent = self.TOOL_INTENT_MAP.get(primary_tool, "unknown_action")
        
        logger.debug(f"Parsed intent '{intent}' from tool history: {tool_calls_history}")
        return intent

intent_parser = IntentParser()