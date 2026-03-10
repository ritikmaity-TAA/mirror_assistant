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
        # If tools were executed, an action was likely taken or suggested
        action_suggested = tools_executed or intent not in ["general_inquiry", "unknown_action"]
        
        response = {
            "reply": reply,
            "intent": intent,
            "action_suggested": action_suggested
        }
        
        logger.debug(f"Built response: {response}")
        return response

response_builder = ResponseBuilder()