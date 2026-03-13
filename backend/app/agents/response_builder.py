import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Maps tool name → the display payload type the frontend expects
TOOL_DISPLAY_TYPE_MAP = {
    "get_day_schedule":      "day_schedule",
    "get_upcoming_bookings": "booking_list",
    "create_slot":           "slot_created",
    "delete_slot":           "slot_deleted",
    "create_booking":        "booking_created",
    "delete_booking":        "booking_cancelled",
    "search_client_by_name": "client_search",
}

# Keys that must never be surfaced in display payloads (internal use only)
_STRIP_KEYS = {"professional_id"}


def _safe_parse(raw: Any) -> Any:
    """Parse a JSON string into a Python object, or return as-is if already parsed."""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return raw


def _build_display(tool_name: str, tool_result_raw: Any) -> Optional[Dict[str, Any]]:
    """
    Convert the raw tool result into a typed display payload.
    Returns None if the tool doesn't warrant a structured display (e.g. internal lookups).
    """
    display_type = TOOL_DISPLAY_TYPE_MAP.get(tool_name)
    if not display_type:
        return None

    result = _safe_parse(tool_result_raw)

    # ---- List views --------------------------------------------------------

    if display_type == "day_schedule":
        # ScheduleService returns: {"date": "...", "entries": [...]}
        entries = result.get("entries", []) if isinstance(result, dict) else []
        items = [
            {k: v for k, v in e.items() if k not in _STRIP_KEYS}
            for e in entries
        ]
        return {"type": display_type, "items": items}

    if display_type == "booking_list":
        # BookingService.get_upcoming_bookings returns: {"entries": [...]}
        # Each entry has nested clients: {client_name} from Supabase join.
        # Flatten into top-level client_name so the frontend needs no extra fetch.
        entries = result.get("entries", []) if isinstance(result, dict) else []
        items = []
        for e in entries:
            flat = {k: v for k, v in e.items() if k not in _STRIP_KEYS and k != "clients"}
            nested = e.get("clients") or {}
            flat["client_name"] = nested.get("client_name") if isinstance(nested, dict) else None
            items.append(flat)
        return {"type": display_type, "items": items}

    if display_type == "client_search":
        # ClientService returns a list or {"data": [...]}
        if isinstance(result, list):
            clients = result
        elif isinstance(result, dict):
            clients = result.get("data", result.get("entries", []))
        else:
            clients = []
        items = [{"client_id": c.get("client_id"), "name": c.get("name")} for c in clients]
        return {"type": display_type, "items": items}

    # ---- Single-record confirmations ---------------------------------------

    if display_type == "slot_created":
        data = result.get("data", {}) if isinstance(result, dict) else {}
        item = {k: v for k, v in data.items() if k not in _STRIP_KEYS}
        return {"type": display_type, "item": item}

    if display_type == "slot_deleted":
        return {"type": display_type, "item": {"status": "cancelled"}}

    if display_type == "booking_created":
        data = result.get("data", {}) if isinstance(result, dict) else {}
        item = {k: v for k, v in data.items() if k not in _STRIP_KEYS}
        return {"type": display_type, "item": item}

    if display_type == "booking_cancelled":
        return {"type": display_type, "item": {"status": "cancelled"}}

    return None


class ResponseBuilder:
    """
    Constructs the final structured ChatResponse dict.

    - `reply`   → plain natural language only (no HTML, ever)
    - `display` → typed payload the frontend renders as cards/tables/lists
                  Frontend reads `metadata.display.type` to pick the component.
                  For bookings, only client_id is included; the frontend fetches
                  full client details from /clients/{id} as needed.
    """

    @staticmethod
    def build(
        reply: str,
        intent: str,
        executed_tools: List[Dict[str, Any]],
        tool_results: Optional[List[Any]] = None,   # parallel list of raw results
    ) -> Dict[str, Any]:

        action_suggested = len(executed_tools) > 0 or intent not in ["general_inquiry", "unknown_action"]

        last_action = None
        parameters = {}
        display = None

        if executed_tools:
            last_tool = executed_tools[-1]
            last_action = last_tool.get("name")
            try:
                parameters = json.loads(last_tool.get("arguments", "{}"))
            except Exception as e:
                logger.warning(f"Failed to parse tool arguments for metadata: {e}")

            # Build display payload from the last tool that has a display mapping.
            # Walk backwards so we pick the most "visible" result (e.g. prefer
            # get_upcoming_bookings over an intermediate search_client_by_name).
            results = tool_results or []
            for tool, raw_result in reversed(list(zip(executed_tools, results))):
                candidate = _build_display(tool.get("name", ""), raw_result)
                if candidate is not None:
                    display = candidate
                    break

        metadata = {
            "last_action": last_action,
            "parameters": parameters,
            "display": display,
        }

        response = {
            "reply": reply,
            "intent": intent,
            "action_suggested": action_suggested,
            "metadata": metadata,
        }

        logger.debug(f"Built final response payload: {response}")
        return response


response_builder = ResponseBuilder()