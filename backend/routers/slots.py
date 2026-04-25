"""
backend/routers/slots.py
------------------------
Endpoint for suggesting the next available time slot.

POST /suggest-slot — return the earliest conflict-free (date, time) for a
                     new task of the requested duration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from dependencies import require_owner
from pawpal_system import Scheduler
from schemas import SlotOut, SlotQuery

router = APIRouter(prefix="/suggest-slot", tags=["slots"])


@router.post("", response_model=Optional[SlotOut])
def suggest_slot(
    body: SlotQuery,
    scheduler: Scheduler = Depends(require_owner),
) -> Optional[SlotOut]:
    """Return the earliest available (date, time) slot for a new task.

    Searches up to 30 days forward from ``starting_from`` (defaults to today).
    If ``pet_id`` is provided, only considers existing tasks assigned to that
    pet when checking for conflicts. Returns null if no slot is found.
    """
    result = scheduler.suggest_next_slot(
        duration_minutes=body.duration_minutes,
        pet_id=body.pet_id,
        starting_from=body.starting_from,
    )

    if result is None:
        return None

    suggested_date, suggested_time = result
    return SlotOut(
        date=suggested_date,
        time_start=suggested_time.strftime("%H:%M"),
    )
