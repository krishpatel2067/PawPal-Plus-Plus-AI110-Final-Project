"""
backend/dependencies.py
-----------------------
FastAPI dependency providers shared across all routers.

Using Depends() rather than importing the scheduler directly means:
  - The data-loading path is defined once, not copied into every router.
  - Future phases can swap in per-user loading (from an auth token) without
    touching any router code.
  - Unit tests can override get_scheduler() with a fixture scheduler via
    app.dependency_overrides.
"""

from fastapi import Depends, HTTPException

from config import get_user_data_path, DEFAULT_USER_ID
from pawpal_system import Owner, Scheduler, load_data, save_data


def get_scheduler() -> Scheduler:
    """Load (or bootstrap) the scheduler for the default user.

    If no data file exists yet, a placeholder scheduler is returned so that
    the owner-setup endpoint can be called first.  All other endpoints that
    require an owner will raise 404 if the owner name is still the empty
    placeholder.

    This function is intended to be injected via ``Depends(get_scheduler)``
    in route handlers.  It re-reads the JSON file on every request, which is
    fine for a single-user prototype; a production version would layer a cache
    or a database session here instead.

    Returns:
        A fully populated Scheduler (owner + tasks) loaded from disk, or a
        fresh empty Scheduler if no save file exists yet.

    Raises:
        HTTPException 500: If the data file exists but cannot be parsed.
    """
    path = get_user_data_path(DEFAULT_USER_ID)
    try:
        scheduler = load_data(path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load data file: {exc}",
        )

    if scheduler is None:
        # No file yet — return a bootstrap scheduler with a sentinel owner name.
        # The POST /owner endpoint will populate this properly.
        scheduler = Scheduler(owner=Owner(name=""))

    return scheduler


def require_owner(scheduler: Scheduler = Depends(get_scheduler)) -> Scheduler:
    """Guard dependency: raises 404 if the owner has not been set up yet.

    Usage in a route::

        @router.get("/something")
        def handler(scheduler: Scheduler = Depends(require_owner)):
            ...

    Chains get_scheduler() internally so callers get a single Depends() call
    that both loads and validates the owner in one step.
    """
    if not scheduler.owner.name:
        raise HTTPException(
            status_code=404,
            detail="Owner not set up. POST /owner first.",
        )
    return scheduler
