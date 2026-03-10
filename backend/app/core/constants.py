# 10.1 & 10.2 Allowed Status Values
class SlotStatus:
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class BookingStatus:
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

# 11. Business Rules & Constraints
class ScheduleConfig:
    MIN_SLOT_DURATION_MINUTES = 30
    DEFAULT_SESSION_DURATION = 60
    MAX_SESSION_DURATION = 120
    
    # Requirement 11: System time zone
    SYSTEM_TIMEZONE = "UTC" 
    
    # Buffer time between appointments (if required later)
    BUFFER_TIME_MINUTES = 0

# Error Messages (Requirement 13)
class ErrorMessages:
    OVERLAP_DETECTED = "This slot overlaps with an existing appointment."
    PAST_DATE_ERROR = "Cannot manage schedules for dates that have already passed."
    CLIENT_NOT_FOUND = "No client matched that name. Please choose from the results."
    SLOT_UNAVAILABLE = "The selected slot is no longer available."