"""
backend/routers/owner.py
------------------------
Endpoints for managing the owner record.

GET  /owner        — retrieve current owner (404 if not yet created)
POST /owner        — create or replace the owner
DELETE /owner      — permanently delete all saved data
"""

from fastapi import APIRouter, Depends, HTTPException, status

from config import DEFAULT_USER_ID, get_user_data_path
from dependencies import get_scheduler
from pawpal_system import Owner, Scheduler, delete_data, save_data
from schemas import MessageOut, OwnerIn, OwnerOut

router = APIRouter(prefix="/owner", tags=["owner"])


@router.get("", response_model=OwnerOut)
def get_owner(scheduler: Scheduler = Depends(get_scheduler)) -> OwnerOut:
    """Return the current owner's name.

    Returns 404 if no owner has been created yet (i.e. no data file exists
    or the owner name is empty). The frontend uses this to decide whether to
    show the setup screen or the main app.
    """
    if not scheduler.owner.name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No owner found. POST /owner to create one.",
        )
    return OwnerOut(name=scheduler.owner.name)


@router.post("", response_model=OwnerOut, status_code=status.HTTP_201_CREATED)
def create_owner(body: OwnerIn) -> OwnerOut:
    """Create a new owner and initialise an empty scheduler for them.

    If a data file already exists, it is overwritten. This effectively acts
    as a "reset" — the frontend should warn the user before calling this when
    an owner already exists.
    """
    new_scheduler = Scheduler(owner=Owner(name=body.name.strip()))
    path = get_user_data_path(DEFAULT_USER_ID)
    save_data(new_scheduler, path)
    return OwnerOut(name=new_scheduler.owner.name)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner() -> None:
    """Permanently delete all saved data (owner, pets, and tasks).

    Returns 204 No Content on success. Idempotent — safe to call even if no
    data file exists.
    """
    path = get_user_data_path(DEFAULT_USER_ID)
    delete_data(path)
