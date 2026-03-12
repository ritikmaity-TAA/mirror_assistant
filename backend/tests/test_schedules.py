import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from fastapi import HTTPException
from services.schedule_service import ScheduleService
from schemas.schedule import AvailabilitySlotCreate
from core.constants import SlotStatus, ErrorMessages

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_repo(monkeypatch):
    mock = MagicMock()
    # Path must match where ScheduleRepository is imported in your service
    monkeypatch.setattr("services.schedule_service.ScheduleRepository", mock)
    return mock

def test_create_slot_success(mock_db, mock_repo):
    # Setup - HH:mm format
    prof_id = uuid4()
    slot_data = AvailabilitySlotCreate(
        professional_id=prof_id,
        date="2027-12-01",
        start_time="09:00",
        end_time="10:00"
    )
    mock_repo.get_slots_by_professional_and_date.return_value.data = []
    mock_repo.create_slot.return_value.data = [{"slot_id": str(uuid4())}]

    result = ScheduleService.create_slot(mock_db, slot_data)

    assert result["status"] == "success"
    mock_repo.create_slot.assert_called_once()

def test_create_slot_zero_duration_fail(mock_db, mock_repo):
    # Fixes the '14th date' problem (16:30 to 16:30)
    slot_data = AvailabilitySlotCreate(
        professional_id=uuid4(),
        date="2027-03-14",
        start_time="16:30",
        end_time="16:30"
    )
    
    with pytest.raises(HTTPException) as exc:
        ScheduleService.create_slot(mock_db, slot_data)
    assert exc.value.status_code == 400
    assert "End time must be strictly after start time" in exc.value.detail

def test_delete_slot_booked_fail(mock_db, mock_repo):
    # Setup
    slot_id = uuid4()
    mock_repo.get_slot_by_id.return_value.data = [
        {"slot_id": str(slot_id), "status": SlotStatus.BOOKED}
    ]

    with pytest.raises(HTTPException) as exc:
        ScheduleService.delete_slot(mock_db, slot_id)
    assert exc.value.status_code == 400
    assert "active booking" in exc.value.detail.lower()

def test_create_slot_past_time_fail(mock_db, mock_repo):
    # Setup - Attempting to create a slot for 1 hour ago
    from datetime import datetime, timedelta
    one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%H:%M")
    today = datetime.now().strftime("%Y-%m-%d")
    
    slot_data = AvailabilitySlotCreate(
        professional_id=uuid4(),
        date=today,
        start_time=one_hour_ago,
        end_time="23:59"
    )

    # Execute & Verify
    with pytest.raises(HTTPException) as exc:
        ScheduleService.create_slot(mock_db, slot_data)
    assert exc.value.status_code == 400
    assert "already passed" in exc.value.detail