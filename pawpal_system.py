from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Task:
    """A single pet care task (walk, feeding, medication, etc.)."""

    name: str
    description: str
    completed: bool
    frequency: str       # e.g. "daily", "weekly", "as needed"
    date: date
    priority: Priority
    pet_names: list[str] = field(default_factory=list)  # empty = no pets assigned

    def __post_init__(self) -> None:
        """Remove duplicate pet names while preserving their original order."""
        self.pet_names = list(dict.fromkeys(self.pet_names))


@dataclass
class Pet:
    """A pet owned by the owner."""

    name: str
    species: str
    age_years: float
    notes: str = ""


@dataclass
class Owner:
    """The pet owner. Holds a list of pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"Pet '{pet.name}' already exists.")
        self.pets.append(pet)

    def remove_pet(self, name: str, scheduler: Scheduler) -> None:
        """Remove a pet by name and scrub it from all tasks in the scheduler."""
        if not any(p.name == name for p in self.pets):
            raise ValueError(f"Pet '{name}' not found.")
        self.pets = [p for p in self.pets if p.name != name]
        scheduler.remove_pet_from_tasks(name)


@dataclass
class Scheduler:
    """Manages all tasks for an owner across their pets."""

    owner: Owner
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task. Validates all pet_names exist. Merges pet_names if task name already exists."""
        unknown = [n for n in task.pet_names if not any(p.name == n for p in self.owner.pets)]
        if unknown:
            raise ValueError(f"Unknown pet(s): {', '.join(unknown)}. Add them to the owner first.")
        for existing in self.tasks:
            if existing.name == task.name:
                existing.pet_names = list(dict.fromkeys(existing.pet_names + task.pet_names))
                return
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove a task by name."""
        if not any(t.name == name for t in self.tasks):
            raise ValueError(f"Task '{name}' not found.")
        self.tasks = [t for t in self.tasks if t.name != name]

    def remove_pet_from_tasks(self, pet_name: str) -> None:
        """Scrub a pet name from all tasks. Called by Owner.remove_pet."""
        for t in self.tasks:
            t.pet_names = [n for n in t.pet_names if n != pet_name]

    def task_count_for_pet(self, pet_name: str) -> int:
        """Return the number of tasks assigned to a specific pet."""
        return len(self.get_tasks_for_pet(pet_name))

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks assigned to a specific pet."""
        return [t for t in self.tasks if pet_name in t.pet_names]

    def get_tasks_for_date(self, target_date: date) -> list[Task]:
        """Return all tasks scheduled for a given date."""
        return [t for t in self.tasks if t.date == target_date]

    def get_unassigned_tasks(self) -> list[Task]:
        """Return all tasks with no pets assigned."""
        return [t for t in self.tasks if not t.pet_names]

    def get_tasks_by_priority(self) -> list[Task]:
        """Return all tasks sorted from HIGH to LOW priority."""
        return sorted(self.tasks, key=lambda t: t.priority.value)

    def mark_complete(self, task_name: str) -> None:
        """Mark a task as completed by name."""
        for t in self.tasks:
            if t.name == task_name:
                t.completed = True
                return
        raise ValueError(f"Task '{task_name}' not found.")
