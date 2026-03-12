import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResponseBuilder:
    """
    Constructs the final structured response dict that ChatbotService expects.
    """

    @staticmethod
    def build(reply: str, intent: str, tools_executed: bool) -> Dict[str, Any]:
        """
        Builds the dictionary ensuring the schema: reply, intent, action_suggested.
        """
        # An action is only confirmed if tools were actually executed AND the intent
        # is a recognised action. Using `or` previously caused unknown_action +
        # tools_executed=True to wrongly return True, masking unexpected agent behaviour.
        NON_ACTIONABLE = {"general_inquiry", "unknown_action", "error"}
        action_suggested = tools_executed and intent not in NON_ACTIONABLE

        response = {
            "reply": reply,
            "intent": intent,
            "action_suggested": action_suggested
        }

        logger.debug(f"Built final response payload: {response}")
        return response

response_builder = ResponseBuilder()