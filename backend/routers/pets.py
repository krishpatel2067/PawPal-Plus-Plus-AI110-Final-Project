"""
backend/routers/pets.py
-----------------------
Endpoints for managing pets that belong to the current owner.

GET    /pets              — list all pets
POST   /pets              — add a new pet
DELETE /pets/{pet_name}   — remove a pet and scrub it from all tasks
"""

from fastapi import APIRouter, Depends, HTTPException, status

from config import DEFAULT_USER_ID, get_user_data_path
from dependencies import require_owner
from pawpal_system import Pet, Scheduler, save_data
from schemas import PetIn, PetOut

router = APIRouter(prefix="/pets", tags=["pets"])


def _pet_to_out(pet: Pet) -> PetOut:
    """Convert a Pet dataclass to its API response shape."""
    return PetOut(
        id=pet.id,
        name=pet.name,
        species=pet.species,
        age_years=pet.age_years,
        notes=pet.notes,
    )


@router.get("", response_model=list[PetOut])
def list_pets(scheduler: Scheduler = Depends(require_owner)) -> list[PetOut]:
    """Return all pets belonging to the current owner."""
    return [_pet_to_out(p) for p in scheduler.owner.pets]


@router.post("", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def add_pet(body: PetIn, scheduler: Scheduler = Depends(require_owner)) -> PetOut:
    """Add a new pet to the owner's list.

    Returns 409 Conflict if a pet with the same name already exists.
    """
    try:
        new_pet = Pet(
            name=body.name.strip(),
            species=body.species.strip(),
            age_years=body.age_years,
            notes=body.notes.strip(),
        )
        scheduler.owner.add_pet(new_pet)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    save_data(scheduler, get_user_data_path(DEFAULT_USER_ID))
    return _pet_to_out(new_pet)


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pet(
    pet_id: str,
    scheduler: Scheduler = Depends(require_owner),
) -> None:
    """Remove a pet by UUID and scrub it from all tasks.

    Returns 404 if no pet with that id exists.
    """
    try:
        scheduler.owner.remove_pet(pet_id, scheduler)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    save_data(scheduler, get_user_data_path(DEFAULT_USER_ID))
