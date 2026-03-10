
# workflow_manager.py
from typing import Any
from agents.intent_parser import IntentParser
from agents.response_builder import ResponseBuilder
from services.schedule_service import ScheduleService
from services.booking_service import BookingService
from services.client_service import ClientService
import logging


class WorkflowManager:
    def __init__(self, db=None, professional_id=None):
        self.intent_parser = IntentParser()
        self.response_builder = ResponseBuilder()
        self.schedule_service = ScheduleService()
        self.booking_service = BookingService()
        self.client_service = ClientService()
        self.db = db  # DB client, injected by backend
        # Professional's UUID, injected by backend
        self.professional_id = professional_id
        self.intent_handlers = {
            "OPEN_SLOT": self._open_slot,
            "EDIT_SLOT": self._edit_slot,
            "DELETE_SLOT": self._delete_slot,
            "CREATE_BOOKING": self._create_booking,
            "EDIT_BOOKING": self._edit_booking,
            "DELETE_BOOKING": self._delete_booking,
            "FETCH_DAY_SCHEDULE": self._fetch_day_schedule,
            "FETCH_CLIENT_SCHEDULE": self._fetch_client_schedule,
            "VIEW_UPCOMING_SESSIONS": self._view_upcoming_sessions,
        }
        # Lightweight in-memory conversation context
        self.context = {
            "last_intent": None,
            "last_entities": {},
            "last_booking_id": None,
            "last_client_name": None,
            "last_date": None,
            "last_time": None
        }

    async def handle_chat(self, message: str) -> str:
        try:
            # 1. Parse intent
            intent_data = await self.intent_parser.parse_intent(message)
            intent = intent_data.get("intent", "UNKNOWN")
            entities = intent_data.get("entities", {})
            logging.info("Intent detected: %s", intent)

            # 2. Merge entities with context
            merged_entities = self._merge_with_context(intent, entities)
            logging.info("Merged entities with context: %s", merged_entities)

            # 3. Validate entities for each intent
            validation_error = self._validate_entities(intent, merged_entities)
            if validation_error:
                return await self.response_builder.error(validation_error)

            # 4. Route to handler
            handler = self.intent_handlers.get(intent)
            if not handler:
                return await self.response_builder.unknown_intent()

            # 5. Call handler
            result = await handler(merged_entities)

            # 6. Update context after successful operation
            self._update_context(intent, merged_entities)

            # 7. Build response
            return await self.response_builder.build(intent, result, merged_entities)
        except Exception as e:
            logging.exception("WorkflowManager error")
            return await self.response_builder.error("Sorry, something went wrong. Please try again.")

    def _merge_with_context(self, intent: str, entities: dict) -> dict:
        """
        Merge missing entities from context for conversational follow-ups.
        User-provided entities always take precedence.
        """
        merged = dict(entities) if entities else {}
        # Rule-based merge for common fields
        context = self.context
        # Fill missing fields from context if available
        for field in ["client_name", "date", "time", "start_time", "end_time", "booking_id", "slot_id"]:
            if merged.get(field) is None and context.get(f"last_{field}") is not None:
                merged[field] = context.get(f"last_{field}")
        # For booking_id, also check last_entities
        if merged.get("booking_id") is None and context["last_entities"].get("booking_id"):
            merged["booking_id"] = context["last_entities"]["booking_id"]
        return merged

    def _update_context(self, intent: str, entities: dict):
        """
        Update context memory after each successful operation.
        Only update if values exist.
        """
        self.context["last_intent"] = intent
        self.context["last_entities"] = dict(entities) if entities else {}
        for field in ["client_name", "date", "time", "start_time", "end_time", "booking_id", "slot_id"]:
            if entities.get(field):
                self.context[f"last_{field}"] = entities[field]

    def _validate_entities(self, intent: str, entities: dict) -> str | None:
        # Returns error string if validation fails, else None
        if intent == "OPEN_SLOT":
            if not all(entities.get(k) for k in ("date", "start_time", "end_time")):
                return "Please specify date, start time, and end time to open a slot."
        elif intent == "CREATE_BOOKING":
            if not all(entities.get(k) for k in ("client_name", "date", "time")):
                return "Please specify client name, date, and time to create a booking."
        elif intent == "FETCH_DAY_SCHEDULE":
            if not entities.get("date"):
                return "Please specify a date to fetch the schedule."
        elif intent == "FETCH_CLIENT_SCHEDULE":
            if not entities.get("client_name"):
                return "Please specify a client name to fetch their schedule."
        return None

    # --- Service orchestration methods ---
    async def _open_slot(self, entities: dict) -> Any:
        return await self.schedule_service.create_slot(self.db, entities)

    async def _edit_slot(self, entities: dict) -> Any:
        return await self.schedule_service.edit_slot(self.db, entities)

    async def _delete_slot(self, entities: dict) -> Any:
        return await self.schedule_service.delete_slot(self.db, entities)

    async def _create_booking(self, entities: dict) -> Any:
        # Conflict detection before creating booking
        date = entities.get("date")
        time = entities.get("time")
        # Fetch the day's schedule
        schedule = await self.schedule_service.get_day_schedule(self.db, self.professional_id, date)
        # Check for time conflict
        if schedule and "entries" in schedule:
            for entry in schedule["entries"]:
                if entry.get("start_time") == time:
                    return {"conflict": True, "date": date, "time": time}
        return await self.booking_service.create_booking(self.db, entities)

    async def _edit_booking(self, entities: dict) -> Any:
        return await self.booking_service.edit_booking(self.db, entities)

    async def _delete_booking(self, entities: dict) -> Any:
        return await self.booking_service.delete_booking(self.db, entities)

    async def _fetch_day_schedule(self, entities: dict) -> Any:
        date = entities.get("date")
        return await self.schedule_service.get_day_schedule(self.db, self.professional_id, date)

    async def _fetch_client_schedule(self, entities: dict) -> Any:
        client_name = entities.get("client_name")
        client = await self.client_service.get_client_by_name(self.db, client_name)
        if not client:
            return {"client_not_found": client_name}
        return await self.client_service.get_client_bookings(self.db, client["client_id"])

    async def _view_upcoming_sessions(self, entities: dict) -> Any:
        return await self.booking_service.get_upcoming_sessions(self.db, self.professional_id)
