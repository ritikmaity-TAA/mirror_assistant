import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from services.booking_service import BookingService
from schemas.booking import BookingCreate
from core.constants import SlotStatus, BookingStatus

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_repos(monkeypatch):
    schedule_mock = MagicMock()
    booking_mock = MagicMock()
    monkeypatch.setattr("services.booking_service.ScheduleRepository", schedule_mock)
    monkeypatch.setattr("services.booking_service.BookingRepository", booking_mock)
    return schedule_mock, booking_mock

def test_booking_50_10_split_logic(mock_db, mock_repos):
    """
    Scenario: 2-hour availability (11:00 to 13:00).
    Request: Book at 11:00.
    Expect: 
    1. Original slot becomes 11:00-12:00 (BOOKED).
    2. New slot created for 12:00-13:00 (AVAILABLE).
    3. Booking record shows 11:00-11:50 (Work Time).
    """
    schedule_repo, booking_repo = mock_repos
    prof_id = uuid4()
    slot_id = uuid4()

    # 1. Setup: Professional is free from 11:00 to 13:00
    schedule_repo.get_slot_by_id.return_value.data = [{
        "slot_id": str(slot_id),
        "professional_id": str(prof_id),
        "date": "2027-03-12",
        "start_time": "11:00",
        "end_time": "13:00",
        "status": SlotStatus.AVAILABLE
    }]
    booking_repo.get_bookings_by_professional_and_date.return_value.data = []
    booking_repo.create_booking.return_value.data = [{"booking_id": "test-id"}]

    booking_request = BookingCreate(
        slot_id=slot_id,
        professional_id=prof_id,
        client_id=uuid4(),
        date="2027-03-12",
        start_time="11:00",
        end_time="11:30" # User asks for 30, but CEO rule forces 60 total
    )

    # 2. Execute
    BookingService.create_booking(mock_db, booking_request)

    # 3. Verify Slot Update (The 50+10 block)
    # The original slot should now be exactly 1 hour (11:00 to 12:00)
    update_args = schedule_repo.update_slot.call_args[0]
    assert update_args[2]["start_time"] == "11:00"
    assert update_args[2]["end_time"] == "12:00" 
    assert update_args[2]["status"] == SlotStatus.BOOKED

    # 4. Verify Slot Splitting (The remainder)
    # A new slot should be created for the remaining 1 hour (12:00 to 13:00)
    create_slot_args = schedule_repo.create_slot.call_args[0]
    assert create_slot_args[1]["start_time"] == "12:00"
    assert create_slot_args[1]["end_time"] == "13:00"
    assert create_slot_args[1]["status"] == SlotStatus.AVAILABLE

    # 5. Verify Booking Record (The 50 min work)
    # The patient/client should only see 11:00 to 11:50
    create_booking_args = booking_repo.create_booking.call_args[0]
    assert create_booking_args[1]["end_time"] == "11:50"

def test_booking_overlap_fail(mock_db, mock_repos):
    schedule_repo, booking_repo = mock_repos
    
    # 1. Setup Parent Slot (Must be AVAILABLE to reach overlap check)
    schedule_repo.get_slot_by_id.return_value.data = [{
        "slot_id": str(uuid4()),
        "status": SlotStatus.AVAILABLE,
        "start_time": "10:00",
        "end_time": "14:00"
    }]
    
    # Existing booking at 11:00 to 12:00
    booking_repo.get_bookings_by_professional_and_date.return_value.data = [{
        "start_time": "11:00",
        "end_time": "12:00",
        "status": BookingStatus.SCHEDULED
    }]
    
    booking_request = BookingCreate(
        slot_id=uuid4(),
        professional_id=uuid4(),
        client_id=uuid4(),
        date="2027-03-12",
        start_time="11:30", # Overlaps with 11:00-12:00
        end_time="12:00"
    )

    with pytest.raises(HTTPException) as exc:
        BookingService.create_booking(mock_db, booking_request)
    assert exc.value.status_code == 409