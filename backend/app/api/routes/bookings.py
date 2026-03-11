from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
import logging
from schemas.booking import BookingCreate, BookingUpdate
from services.booking_service import BookingService
from api.dependencies import get_supabase_client
from supabase import Client

# Configure logging for industry-standard traceability
logger = logging.getLogger(__name__)

# Prefix matches Req 12 logical grouping
router = APIRouter(prefix="/schedule/bookings", tags=["Bookings"])

# 12.4 Create Booking
@router.post("/", response_model=dict)
def create_booking(booking: BookingCreate, db: Client = Depends(get_supabase_client)):
    """
    Creates a new booking. 
    Matches requirement: validation for slot availability and client existence.
    """
    try:
        return BookingService.create_booking(db, booking)
    except HTTPException as e:
        # Re-raise custom business logic errors (e.g., 409 Conflict, 400 Bad Request)
        raise e
    except Exception as e:
        logger.error(f"CRITICAL: Booking creation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal Server Error: Booking could not be completed. Please contact support."
        )

# 12.5 Update Booking
@router.put("/{booking_id}", response_model=dict)
def update_booking(booking_id: UUID, booking: BookingUpdate, db: Client = Depends(get_supabase_client)):
    """
    Updates an existing booking.
    Matches requirement: validation for conflict or invalid identifiers.
    """
    try:
        return BookingService.update_booking(db, booking_id, booking)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"CRITICAL: Update failed for booking {booking_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal Server Error: Update failed."
        )

# 12.6 Delete/Cancel Booking
@router.delete("/{booking_id}", response_model=dict)
def cancel_booking(booking_id: UUID, db: Client = Depends(get_supabase_client)):
    """
    Cancels or deletes a booking.
    Matches requirement: Returns success state, cancellation state, or failure reason.
    """
    try:
        return BookingService.cancel_booking(db, booking_id)
    except HTTPException as e:
        # This will return "invalid booking identifier" with 404 or "failure reason" with 400
        raise e
    except Exception as e:
        logger.error(f"CRITICAL: Cancellation failed for {booking_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal Server Error: Cancellation failed."
        )

# # Extra utility for the Professional's Dashboard
# @router.get("/upcoming/{professional_id}", response_model=dict)
# def get_upcoming_bookings(professional_id: UUID, db: Client = Depends(get_supabase_client)):
#     try:
#         return BookingService.get_upcoming_bookings(db, professional_id)
#     except Exception as e:
#         logger.error(f"Failed to fetch upcoming bookings for {professional_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Could not retrieve upcoming bookings.")