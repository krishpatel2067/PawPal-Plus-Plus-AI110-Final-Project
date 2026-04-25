import pytest
from datetime import date, time
from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task


@pytest.fixture
def scheduler():
    owner = Owner(name="Alex")
    owner.add_pet(Pet(name="Mochi", species="Cat", age_years=3.0))
    owner.add_pet(Pet(name="Rex", species="Dog", age_years=5.0))
    return Scheduler(owner=owner)


def mochi_id(scheduler: Scheduler) -> str:
    """Return the UUID of Mochi (first pet)."""
    return next(p.id for p in scheduler.owner.pets if p.name == "Mochi")


def rex_id(scheduler: Scheduler) -> str:
    """Return the UUID of Rex (second pet)."""
    return next(p.id for p in scheduler.owner.pets if p.name == "Rex")


def make_task(name, d=None, priority=Priority.MEDIUM, frequency=Frequency.DAILY,
              pet_ids=None, time_start=None, duration_minutes=0):
    return Task(
        name=name,
        description="",
        completed=False,
        frequency=frequency,
        date=d or date.today(),
        priority=priority,
        pet_ids=pet_ids or [],
        time_start=time_start,
        duration_minutes=duration_minutes,
    )


# ── Basic task operations ────────────────────────────────────────────────────

def test_mark_complete_changes_task_status(scheduler):
    task = make_task("Morning Feed", pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    assert scheduler.tasks[0].completed is True


def test_add_task_increases_pet_task_count(scheduler):
    mid = mochi_id(scheduler)
    assert len(scheduler.get_tasks_for_pet(mid)) == 0
    scheduler.add_task(make_task("Morning Feed", pet_ids=[mid]))
    assert len(scheduler.get_tasks_for_pet(mid)) == 1
    scheduler.add_task(make_task("Evening Feed", pet_ids=[mid]))
    assert len(scheduler.get_tasks_for_pet(mid)) == 2


def test_duplicate_task_name_and_date_allowed(scheduler):
    """Tasks with identical names and dates are allowed — each has a unique UUID."""
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("Feed", d=d))
    scheduler.add_task(make_task("Feed", d=d))
    assert len(scheduler.tasks) == 2


# ── Sorting ──────────────────────────────────────────────────────────────────

def test_sort_by_priority(scheduler):
    scheduler.add_task(make_task("Low Task", priority=Priority.LOW))
    scheduler.add_task(make_task("High Task", priority=Priority.HIGH))
    scheduler.add_task(make_task("Medium Task", priority=Priority.MEDIUM))
    tasks = scheduler.get_tasks_sorted(["Priority"])
    assert [t.priority for t in tasks] == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_sort_by_datetime_orders_by_date_then_time(scheduler):
    later_date = date(2026, 4, 2)
    earlier_date = date(2026, 4, 1)
    scheduler.add_task(make_task("Late Task", d=later_date, time_start=time(9, 0), duration_minutes=30))
    scheduler.add_task(make_task("Early Task", d=earlier_date, time_start=time(10, 0), duration_minutes=30))
    tasks = scheduler.get_tasks_sorted(["Date & Time"])
    assert tasks[0].name == "Early Task"
    assert tasks[1].name == "Late Task"


def test_sort_by_datetime_same_date_orders_by_time(scheduler):
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("Afternoon", d=d, time_start=time(14, 0), duration_minutes=30))
    scheduler.add_task(make_task("Morning", d=d, time_start=time(8, 0), duration_minutes=30))
    tasks = scheduler.get_tasks_sorted(["Date & Time"])
    assert tasks[0].name == "Morning"
    assert tasks[1].name == "Afternoon"


def test_sort_by_datetime_untimed_tasks_sort_last(scheduler):
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("No Time", d=d))
    scheduler.add_task(make_task("Has Time", d=d, time_start=time(8, 0), duration_minutes=30))
    tasks = scheduler.get_tasks_sorted(["Date & Time"])
    assert tasks[0].name == "Has Time"
    assert tasks[1].name == "No Time"


# ── Recurring task auto-creation ─────────────────────────────────────────────

def test_completing_daily_task_creates_next_day(scheduler):
    d = date(2026, 4, 1)
    task = make_task("Feed", d=d, frequency=Frequency.DAILY, pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    dates = [t.date for t in scheduler.tasks]
    assert date(2026, 4, 2) in dates


def test_completing_weekly_task_creates_next_week(scheduler):
    d = date(2026, 4, 1)
    task = make_task("Bath", d=d, frequency=Frequency.WEEKLY, pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    dates = [t.date for t in scheduler.tasks]
    assert date(2026, 4, 8) in dates


def test_completing_monthly_task_creates_next_month(scheduler):
    d = date(2026, 1, 31)
    task = make_task("Vet", d=d, frequency=Frequency.MONTHLY, pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    dates = [t.date for t in scheduler.tasks]
    assert date(2026, 2, 28) in dates  # Jan 31 + 1 month = Feb 28


def test_completing_yearly_task_creates_next_year(scheduler):
    d = date(2026, 3, 15)
    task = make_task("Annual Checkup", d=d, frequency=Frequency.YEARLY, pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    dates = [t.date for t in scheduler.tasks]
    assert date(2027, 3, 15) in dates


def test_completing_once_task_creates_no_next(scheduler):
    task = make_task("Microchip", frequency=Frequency.ONCE, pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    assert len(scheduler.tasks) == 1


def test_recurring_next_task_is_incomplete(scheduler):
    d = date(2026, 4, 1)
    task = make_task("Feed", d=d, frequency=Frequency.DAILY, pet_ids=[mochi_id(scheduler)])
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    next_task = next(t for t in scheduler.tasks if t.date == date(2026, 4, 2))
    assert next_task.completed is False


def test_recurring_next_task_has_new_uuid(scheduler):
    """Each recurrence gets a fresh UUID so it can be managed independently."""
    d = date(2026, 4, 1)
    task = make_task("Feed", d=d, frequency=Frequency.DAILY, pet_ids=[mochi_id(scheduler)])
    original_id = task.id
    scheduler.add_task(task)
    scheduler.mark_complete(task.id)
    next_task = next(t for t in scheduler.tasks if t.date == date(2026, 4, 2))
    assert next_task.id != original_id


# ── Filtering ────────────────────────────────────────────────────────────────

def test_filter_by_pet(scheduler):
    mid = mochi_id(scheduler)
    rid = rex_id(scheduler)
    scheduler.add_task(make_task("Mochi Task", pet_ids=[mid]))
    scheduler.add_task(make_task("Rex Task", pet_ids=[rid]))
    tasks = scheduler.get_tasks_for_pet(mid)
    assert len(tasks) == 1
    assert tasks[0].name == "Mochi Task"


def test_filter_unassigned(scheduler):
    scheduler.add_task(make_task("Assigned", pet_ids=[mochi_id(scheduler)]))
    scheduler.add_task(make_task("Unassigned"))
    tasks = scheduler.get_unassigned_tasks()
    assert len(tasks) == 1
    assert tasks[0].name == "Unassigned"


def test_filter_completed(scheduler):
    mid = mochi_id(scheduler)
    done = make_task("Done", pet_ids=[mid])
    pending = make_task("Pending", pet_ids=[mid])
    scheduler.add_task(done)
    scheduler.add_task(pending)
    scheduler.mark_complete(done.id)
    tasks = scheduler.get_completed_tasks()
    assert all(t.completed for t in tasks)
    assert any(t.name == "Done" for t in tasks)


def test_filter_incomplete(scheduler):
    mid = mochi_id(scheduler)
    done = make_task("Done", pet_ids=[mid])
    pending = make_task("Pending", pet_ids=[mid])
    scheduler.add_task(done)
    scheduler.add_task(pending)
    scheduler.mark_complete(done.id)
    tasks = scheduler.get_incomplete_tasks()
    assert all(not t.completed for t in tasks)
    assert any(t.name == "Pending" for t in tasks)


def test_filter_stacking_pet_then_completed(scheduler):
    mid = mochi_id(scheduler)
    rid = rex_id(scheduler)
    mochi_done = make_task("Mochi Done", pet_ids=[mid])
    mochi_pending = make_task("Mochi Pending", pet_ids=[mid])
    rex_done = make_task("Rex Done", pet_ids=[rid])
    scheduler.add_task(mochi_done)
    scheduler.add_task(mochi_pending)
    scheduler.add_task(rex_done)
    scheduler.mark_complete(mochi_done.id)
    scheduler.mark_complete(rex_done.id)
    tasks = scheduler.get_completed_tasks(scheduler.get_tasks_for_pet(mid))
    assert len(tasks) == 1
    assert tasks[0].name == "Mochi Done"


def test_filter_stacking_pet_then_incomplete(scheduler):
    mid = mochi_id(scheduler)
    rid = rex_id(scheduler)
    mochi_done = make_task("Mochi Done", pet_ids=[mid], frequency=Frequency.ONCE)
    mochi_pending = make_task("Mochi Pending", pet_ids=[mid])
    rex_pending = make_task("Rex Pending", pet_ids=[rid])
    scheduler.add_task(mochi_done)
    scheduler.add_task(mochi_pending)
    scheduler.add_task(rex_pending)
    scheduler.mark_complete(mochi_done.id)
    tasks = scheduler.get_incomplete_tasks(scheduler.get_tasks_for_pet(mid))
    assert len(tasks) == 1
    assert tasks[0].name == "Mochi Pending"


# ── Conflict detection ───────────────────────────────────────────────────────

def test_overlapping_tasks_same_pet_detected(scheduler):
    mid = mochi_id(scheduler)
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("Walk", d=d, pet_ids=[mid],
                                 time_start=time(9, 0), duration_minutes=60))
    new_task = make_task("Groom", d=d, pet_ids=[mid],
                         time_start=time(9, 30), duration_minutes=30)
    assert len(scheduler.get_conflicts(new_task)) == 1


def test_adjacent_tasks_no_conflict(scheduler):
    mid = mochi_id(scheduler)
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("Walk", d=d, pet_ids=[mid],
                                 time_start=time(9, 0), duration_minutes=60))
    new_task = make_task("Feed", d=d, pet_ids=[mid],
                         time_start=time(10, 0), duration_minutes=30)
    assert scheduler.get_conflicts(new_task) == []


def test_overlapping_tasks_different_pets_no_conflict(scheduler):
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("Walk Mochi", d=d, pet_ids=[mochi_id(scheduler)],
                                 time_start=time(9, 0), duration_minutes=60))
    new_task = make_task("Walk Rex", d=d, pet_ids=[rex_id(scheduler)],
                         time_start=time(9, 30), duration_minutes=30)
    assert scheduler.get_conflicts(new_task) == []


def test_overlapping_tasks_different_dates_no_conflict(scheduler):
    mid = mochi_id(scheduler)
    scheduler.add_task(make_task("Walk", d=date(2026, 4, 1), pet_ids=[mid],
                                 time_start=time(9, 0), duration_minutes=60))
    new_task = make_task("Walk", d=date(2026, 4, 2), pet_ids=[mid],
                         time_start=time(9, 0), duration_minutes=60)
    assert scheduler.get_conflicts(new_task) == []


def test_task_without_time_no_conflict(scheduler):
    mid = mochi_id(scheduler)
    d = date(2026, 4, 1)
    scheduler.add_task(make_task("Walk", d=d, pet_ids=[mid],
                                 time_start=time(9, 0), duration_minutes=60))
    new_task = make_task("Feed", d=d, pet_ids=[mid])  # no time set
    assert scheduler.get_conflicts(new_task) == []
