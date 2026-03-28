import pytest
from datetime import date
from pawpal_system import Owner, Pet, Priority, Scheduler, Task


@pytest.fixture
def scheduler():
    owner = Owner(name="Alex")
    owner.add_pet(Pet(name="Mochi", species="Cat", age_years=3.0))
    return Scheduler(owner=owner)


def test_mark_complete_changes_task_status(scheduler):
    task = Task("Morning Feed", "Half cup dry food", False, "daily", date.today(), Priority.MEDIUM, ["Mochi"])
    scheduler.add_task(task)
    scheduler.mark_complete("Morning Feed")
    assert scheduler.tasks[0].completed is True


def test_add_task_increases_pet_task_count(scheduler):
    assert scheduler.task_count_for_pet("Mochi") == 0
    scheduler.add_task(Task("Morning Feed", "Half cup dry food", False, "daily", date.today(), Priority.MEDIUM, ["Mochi"]))
    assert scheduler.task_count_for_pet("Mochi") == 1
    scheduler.add_task(Task("Evening Feed", "Half cup dry food", False, "daily", date.today(), Priority.MEDIUM, ["Mochi"]))
    assert scheduler.task_count_for_pet("Mochi") == 2
