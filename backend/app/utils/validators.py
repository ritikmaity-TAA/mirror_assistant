import uuid
from typing import Union, Any

def generate_uuid() -> str:
    """
    Generates a version 4 (random) UUID.
    Returns a string to ensure JSON compatibility across the system.
    """
    return str(uuid.uuid4())

def is_valid_uuid(uuid_to_test: Any) -> bool:
    """
    Industry standard check to verify if a string or object is a valid UUID.
    Prevents 'invalid input syntax' errors in PostgreSQL/Supabase.
    """
    if not uuid_to_test:
        return False
    try:
        # If it's already a UUID object, it's valid
        if isinstance(uuid_to_test, uuid.UUID):
            return True
        # If it's a string, try to parse it
        uuid.UUID(str(uuid_to_test))
        return True
    except ValueError:
        return False

def format_db_payload(data: dict) -> dict:
    """
    Deep-cleans a dictionary for Supabase/JSON.
    Converts all UUID objects, datetime objects, or Enums into strings.
    This fixes the 'Object of type UUID is not JSON serializable' error.
    """
    clean_payload = {}
    for key, value in data.items():
        if isinstance(value, uuid.UUID):
            clean_payload[key] = str(value)
        elif hasattr(value, 'value'): # Handles Python Enums automatically
            clean_payload[key] = str(value.value)
        else:
            clean_payload[key] = value
    return clean_payload