import re
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Union

def normalize_datetime(text: str) -> dict | None:
    """
    Convert natural language date/time expressions to normalized values.
    Returns dict with 'date' (YYYY-MM-DD) and 'time' (HH:MM) or None values.
    """
    text = text.lower().strip()
    today = date.today()
    parsed_date = _parse_relative_day(text)
    if not parsed_date:
        parsed_date = _parse_weekday(text)
    parsed_time = _parse_time(text)
    result = {"date": parsed_date.isoformat() if parsed_date else None, "time": parsed_time}
    logging.debug("Normalized datetime: %s", result)
    return result

def _parse_relative_day(text: str) -> date | None:
    today = date.today()
    if re.search(r"\btoday\b", text):
        return today
    if re.search(r"\btomorrow\b", text):
        return today + timedelta(days=1)
    if re.search(r"day after tomorrow", text):
        return today + timedelta(days=2)
    return None

def _parse_weekday(text: str) -> date | None:
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = date.today()
    for i, wd in enumerate(weekdays):
        # next monday, next friday, etc.
        if f"next {wd}" in text:
            days_ahead = (i - today.weekday() + 7) % 7
            days_ahead = days_ahead or 7
            return today + timedelta(days=days_ahead)
        # this monday, this friday, etc.
        if f"this {wd}" in text:
            days_ahead = (i - today.weekday()) % 7
            return today + timedelta(days=days_ahead)
        # just 'monday', 'friday', etc.
        if re.search(rf"\b{wd}\b", text):
            days_ahead = (i - today.weekday() + 7) % 7
            days_ahead = days_ahead or 7
            return today + timedelta(days=days_ahead)
    return None

def _parse_time(text: str) -> str | None:
    # Time of day phrases
    if "morning" in text:
        return "09:00"
    if "afternoon" in text:
        return "14:00"
    if "evening" in text:
        return "18:00"

    # Match times like '3 pm', '3:30 pm', '15:00', '10', '10:30'
    time_patterns = [
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",
        r"(\d{1,2})\s*(am|pm)",
        r"(\d{1,2})"
    ]
    for pat in time_patterns:
        m = re.search(pat, text)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2)) if m.lastindex and m.lastindex >= 2 and m.group(2) else 0
            ampm = m.group(3).lower() if m.lastindex and m.lastindex >= 3 and m.group(3) else None
            if ampm == "pm" and hour < 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute:02d}"
    return None

# Defensive: If parsing fails, always return None values
def _safe_normalize_datetime(text: str) -> dict:
    try:
        return normalize_datetime(text)
    except Exception:
        return {"date": None, "time": None}

def get_now() -> datetime:
    """Returns current UTC time."""
    return datetime.now(timezone.utc)

def is_past_date(target_date: Union[str, date]) -> bool:
    """Checks if the provided date is before today."""
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    return target_date < date.today()

def is_past_datetime(target_date: str, target_time: str) -> bool:
    """Checks if the specific slot/booking is in the past."""
    combined = datetime.fromisoformat(f"{target_date}T{target_time}")
    # Assuming the input time is local to the professional, adjust if using UTC
    return combined < datetime.now()

def validate_time_range(start_time: str, end_time: str) -> bool:
    """
    Industry Standard: End time must be strictly greater than start time.
    Prevents 'Zero-Duration' slots like 16:30 to 16:30.
    """
    if not start_time or not end_time:
        return False
    return start_time < end_time