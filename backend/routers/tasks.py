"""
backend/routers/tasks.py
------------------------
Endpoints for managing tasks in the scheduler.

GET  /tasks                       — list tasks with optional filter + sort
POST /tasks                       — create a new task
DELETE /tasks/{task_id}           — delete a task by UUID
POST   /tasks/{task_id}/complete  — mark a task complete (spawns recurrence)
"""

from datetime import time as dt_time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from config import DEFAULT_USER_ID, get_user_data_path
from dependencies import require_owner
from pawpal_system import Frequency, Priority, Scheduler, Task, save_data
from schemas import TaskIn, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_out(task: Task) -> TaskOut:
    """Convert a Task dataclass to its API response shape."""
    return TaskOut(
        id=task.id,
        name=task.name,
        description=task.description,
        completed=task.completed,
        frequency=task.frequency.value,
        date=task.date,
        priority=task.priority.name,
        pet_ids=task.pet_ids,
        time_start=task.time_start.strftime("%H:%M") if task.time_start else None,
        duration_minutes=task.duration_minutes,
    )


@router.get("", response_model=list[TaskOut])
def list_tasks(
    filter_pet: Optional[str] = Query(default=None, description="Filter by pet UUID."),
    filter_status: Optional[str] = Query(
        default="all",
        description="Filter by completion: 'all' | 'completed' | 'incomplete'.",
    ),
    sort_by: Optional[str] = Query(
        default=None,
        description="Comma-separated sort keys, e.g. 'Priority,Date & Time'.",
    ),
    scheduler: Scheduler = Depends(require_owner),
) -> list[TaskOut]:
    """Return tasks, optionally filtered by pet and/or status, then sorted.

    Filters are applied first (pet → status), then sort. This mirrors the
    behaviour of the original Streamlit app's stacked filter + sort controls.
    """
    # Start with all tasks, then narrow down.
    tasks = list(scheduler.tasks)

    if filter_pet:
        tasks = scheduler.get_tasks_for_pet(filter_pet, tasks)

    status_key = (filter_status or "all").lower()
    if status_key == "completed":
        tasks = scheduler.get_completed_tasks(tasks)
    elif status_key == "incomplete":
        tasks = scheduler.get_incomplete_tasks(tasks)

    # sort_by is a comma-separated string; split and strip whitespace.
    sort_keys = [k.strip() for k in sort_by.split(",")] if sort_by else []
    tasks = scheduler.get_tasks_sorted(sort_keys, tasks)

    return [_task_to_out(t) for t in tasks]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskIn,
    scheduler: Scheduler = Depends(require_owner),
) -> TaskOut:
    """Create a new task and append it to the scheduler.

    Returns 400 if an unknown pet id is supplied or if the frequency /
    priority value is not recognised.
    """
    # Parse the time_start string ("HH:MM") into a datetime.time object.
    parsed_time: Optional[dt_time] = None
    if body.time_start:
        try:
            parsed_time = dt_time.fromisoformat(body.time_start)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time_start format '{body.time_start}'. Use HH:MM.",
            )

    # Validate enum values before constructing the Task so the error is clear.
    try:
        frequency = Frequency(body.frequency)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown frequency '{body.frequency}'. "
                   f"Valid values: {[f.value for f in Frequency]}",
        )

    try:
        priority = Priority[body.priority]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown priority '{body.priority}'. "
                   f"Valid values: {[p.name for p in Priority]}",
        )

    new_task = Task(
        name=body.name.strip(),
        description=body.description.strip(),
        completed=False,
        frequency=frequency,
        date=body.date,
        priority=priority,
        pet_ids=body.pet_ids,
        time_start=parsed_time,
        duration_minutes=body.duration_minutes,
    )

    try:
        scheduler.add_task(new_task)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    save_data(scheduler, get_user_data_path(DEFAULT_USER_ID))
    return _task_to_out(new_task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    scheduler: Scheduler = Depends(require_owner),
) -> None:
    """Delete a task by UUID.

    Returns 404 if no task with that id exists.
    """
    try:
        scheduler.remove_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    save_data(scheduler, get_user_data_path(DEFAULT_USER_ID))


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: str,
    scheduler: Scheduler = Depends(require_owner),
) -> TaskOut:
    """Mark a task as complete.

    If the task is recurring, a new task is automatically scheduled for the
    next occurrence with a fresh UUID. Returns the completed task.

    Returns 404 if no incomplete task with that id exists.
    """
    try:
        scheduler.mark_complete(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    save_data(scheduler, get_user_data_path(DEFAULT_USER_ID))

    # Return the now-completed task.
    completed = next(t for t in scheduler.tasks if t.id == task_id)
    return _task_to_out(completed)
