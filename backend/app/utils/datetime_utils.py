from datetime import datetime, date, timezone
from typing import Union

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
    """End time must be later than start time."""
    return start_time < end_time