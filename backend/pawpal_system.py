from __future__ import annotations
import json
import uuid
from pathlib import Path
from dataclasses import dataclass, field, replace
from dateutil.relativedelta import relativedelta
from datetime import date, time, timedelta
from enum import Enum


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Frequency(Enum):
    ONCE = "Once"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"


@dataclass
class Task:
    """A single pet care task (walk, feeding, medication, etc.).

    Each task carries a UUID ``id`` that is generated automatically on creation.
    The id is stable across save/load cycles and is the canonical way to
    reference a specific task from the API layer.

    ``pet_ids`` holds UUID strings of the pets this task is assigned to,
    rather than names, so pet renames or duplicate names never break references.
    """

    name: str
    description: str
    completed: bool
    frequency: Frequency
    date: date
    priority: Priority
    # UUID v4 string — generated once at creation, never changes.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pet_ids: list[str] = field(default_factory=list)  # empty = no pets assigned
    time_start: time | None = None
    duration_minutes: int = 0

    def __post_init__(self) -> None:
        """Remove duplicate pet IDs while preserving their original order."""
        self.pet_ids = list(dict.fromkeys(self.pet_ids))


@dataclass
class Pet:
    """A pet owned by the owner.

    Names are display labels only — duplicate names are allowed.
    The ``id`` UUID is the canonical identifier used everywhere internally.
    """

    name: str
    species: str
    age_years: float
    notes: str = ""
    # UUID v4 string — generated once at creation, never changes.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Owner:
    """The pet owner. Holds a list of pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list. Duplicate names are allowed."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str, scheduler: Scheduler) -> None:
        """Remove a pet by UUID and scrub it from all tasks in the scheduler.

        Raises:
            ValueError: If no pet with that id exists.
        """
        target = next((p for p in self.pets if p.id == pet_id), None)
        if target is None:
            raise ValueError(f"Pet with id '{pet_id}' not found.")
        self.pets = [p for p in self.pets if p.id != pet_id]
        # Scrub the pet's id from every task's pet_ids list.
        scheduler.remove_pet_from_tasks(pet_id)


@dataclass
class Scheduler:
    """Manages all tasks for an owner across their pets."""

    owner: Owner
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task. Validates all pet_ids exist on the owner.

        Duplicate task names and dates are allowed — each task is uniquely
        identified by its UUID, not by name or date.
        """
        unknown = [i for i in task.pet_ids if not any(p.id == i for p in self.owner.pets)]
        if unknown:
            raise ValueError(f"Unknown pet id(s): {', '.join(unknown)}.")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its UUID id.

        Raises:
            ValueError: If no task with that id exists.
        """
        if not any(t.id == task_id for t in self.tasks):
            raise ValueError(f"Task with id '{task_id}' not found.")
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def remove_pet_from_tasks(self, pet_id: str) -> None:
        """Scrub a pet UUID from all tasks. Called by Owner.remove_pet."""
        for t in self.tasks:
            t.pet_ids = [i for i in t.pet_ids if i != pet_id]

    def get_tasks_for_pet(self, pet_id: str, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks assigned to a specific pet (matched by UUID)."""
        src = tasks if tasks is not None else self.tasks
        return [t for t in src if pet_id in t.pet_ids]

    def get_unassigned_tasks(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks with no pets assigned."""
        src = tasks if tasks is not None else self.tasks
        return [t for t in src if not t.pet_ids]

    def get_completed_tasks(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return completed tasks."""
        src = tasks if tasks is not None else self.tasks
        return [t for t in src if t.completed]

    def get_incomplete_tasks(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return incomplete tasks."""
        src = tasks if tasks is not None else self.tasks
        return [t for t in src if not t.completed]

    def get_tasks_sorted(self, sort_keys: list[str], tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by an ordered list of keys: 'Priority' and/or 'Date & Time'.
        Keys are applied left-to-right, so the first key is the primary sort."""
        src = tasks if tasks is not None else self.tasks

        def make_key(t: Task) -> tuple:
            parts: list = []
            for key in sort_keys:
                if key == "Priority":
                    parts.append(t.priority.value)
                elif key == "Date & Time":
                    parts.append(t.date)
                    parts.append(t.time_start or time.max)
            return tuple(parts)

        return sorted(src, key=make_key)

    def suggest_next_slot(
        self,
        duration_minutes: int,
        pet_id: str | None = None,
        starting_from: date | None = None,
    ) -> tuple[date, time] | None:
        """Return the earliest (date, time) where a task of duration_minutes fits
        without conflicting with existing scheduled tasks for the given pet.
        Searches up to 30 days forward from starting_from (default: today).
        If pet_id is None, checks against all scheduled tasks."""
        DAY_START = 8 * 60   # 08:00
        DAY_END = 22 * 60    # 22:00
        search_date = starting_from or date.today()

        for _ in range(30):
            base = self.get_tasks_for_pet(pet_id) if pet_id else list(self.tasks)
            day_tasks = sorted(
                [t for t in base if t.date == search_date and t.time_start and t.duration_minutes > 0],
                key=lambda t: t.time_start.hour * 60 + t.time_start.minute,
            )
            candidate_m = DAY_START
            for task in day_tasks:
                task_start_m = task.time_start.hour * 60 + task.time_start.minute
                if candidate_m + duration_minutes <= task_start_m:
                    return search_date, time(candidate_m // 60, candidate_m % 60)
                task_end_m = task_start_m + task.duration_minutes
                if task_end_m > candidate_m:
                    candidate_m = task_end_m
            if candidate_m + duration_minutes <= DAY_END:
                return search_date, time(candidate_m // 60, candidate_m % 60)
            search_date += timedelta(days=1)

        return None

    def get_conflicts(self, task: Task) -> list[Task]:
        """Return existing tasks whose time window overlaps with the given task.
        Only tasks sharing at least one pet (by UUID) on the same date are checked.
        Tasks without a time_start, duration, or pet are skipped."""
        if task.time_start is None or task.duration_minutes <= 0:
            return []

        def to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute

        task_start = to_minutes(task.time_start)
        task_end = task_start + task.duration_minutes
        conflicts = []

        for existing in self.tasks:
            if existing.id == task.id:
                continue
            if existing.date != task.date:
                continue
            if existing.time_start is None or existing.duration_minutes <= 0:
                continue
            # Only flag conflicts between tasks that share at least one pet.
            if not task.pet_ids or not existing.pet_ids:
                continue
            if not set(task.pet_ids) & set(existing.pet_ids):
                continue
            existing_start = to_minutes(existing.time_start)
            existing_end = existing_start + existing.duration_minutes
            if task_start < existing_end and existing_start < task_end:
                conflicts.append(existing)

        return conflicts

    def _next_date(self, d: date, freq: Frequency) -> date | None:
        """Return the next occurrence date for a given frequency, or None for ONCE."""
        if freq == Frequency.ONCE:
            return None
        if freq == Frequency.DAILY:
            return d + timedelta(days=1)
        if freq == Frequency.WEEKLY:
            return d + timedelta(weeks=1)
        if freq == Frequency.MONTHLY:
            return d + relativedelta(months=1)
        # YEARLY
        return d + relativedelta(years=1)

    def mark_complete(self, task_id: str) -> None:
        """Mark a task as completed and schedule the next occurrence if recurring.

        The recurrence is appended as a new Task with a fresh UUID so it can
        be independently managed (completed, deleted, etc.).

        Raises:
            ValueError: If no incomplete task with that id exists.
        """
        for t in self.tasks:
            if t.id != task_id or t.completed:
                continue
            t.completed = True
            next_d = self._next_date(t.date, t.frequency)
            if next_d is not None:
                self.tasks.append(replace(t, date=next_d, completed=False, id=str(uuid.uuid4())))
            return

        raise ValueError(f"Incomplete task with id '{task_id}' not found.")


# ── Persistence ──────────────────────────────────────────────────────────────

def _task_to_dict(t: Task) -> dict:
    """Serialize a Task dataclass instance to a plain dict suitable for JSON."""
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "completed": t.completed,
        "frequency": t.frequency.value,
        "date": t.date.isoformat(),
        "priority": t.priority.name,
        "pet_ids": t.pet_ids,
        "time_start": t.time_start.strftime("%H:%M") if t.time_start else None,
        "duration_minutes": t.duration_minutes,
    }


def _task_from_dict(d: dict) -> Task:
    """Deserialize a plain dict (from JSON) back into a Task."""
    return Task(
        id=d["id"],
        name=d["name"],
        description=d["description"],
        completed=d["completed"],
        frequency=Frequency(d["frequency"]),
        date=date.fromisoformat(d["date"]),
        priority=Priority[d["priority"]],
        pet_ids=d["pet_ids"],
        time_start=time.fromisoformat(d["time_start"]) if d["time_start"] else None,
        duration_minutes=d["duration_minutes"],
    )


def _pet_to_dict(p: Pet) -> dict:
    """Serialize a Pet dataclass instance to a plain dict suitable for JSON."""
    return {
        "id": p.id,
        "name": p.name,
        "species": p.species,
        "age_years": p.age_years,
        "notes": p.notes,
    }


def _pet_from_dict(d: dict) -> Pet:
    """Deserialize a plain dict (from JSON) back into a Pet."""
    return Pet(
        id=d["id"],
        name=d["name"],
        species=d["species"],
        age_years=d["age_years"],
        notes=d.get("notes", ""),
    )


def save_data(scheduler: Scheduler, path: Path | str) -> None:
    """Serialize the owner and all tasks to a JSON file."""
    data = {
        "owner": {
            "name": scheduler.owner.name,
            "pets": [_pet_to_dict(p) for p in scheduler.owner.pets],
        },
        "tasks": [_task_to_dict(t) for t in scheduler.tasks],
    }
    Path(path).write_text(json.dumps(data, indent=2))


def delete_data(path: Path | str) -> None:
    """Delete the saved data file if it exists."""
    p = Path(path)
    if p.exists():
        p.unlink()


def load_data(path: Path | str) -> Scheduler | None:
    """Load owner and tasks from a JSON file. Returns None if the file doesn't exist."""
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    owner = Owner(name=data["owner"]["name"])
    for pet in data["owner"]["pets"]:
        owner.pets.append(_pet_from_dict(pet))
    scheduler = Scheduler(owner=owner)
    scheduler.tasks = [_task_from_dict(t) for t in data["tasks"]]
    return scheduler
