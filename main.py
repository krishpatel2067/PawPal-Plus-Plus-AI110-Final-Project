from datetime import date
from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(label: str, tasks: list[Task]) -> None:
    print(f"\n{label}")
    if not tasks:
        print("  (no tasks)")
    for t in tasks:
        status = "✓" if t.completed else "○"
        pets = ", ".join(t.pet_names) if t.pet_names else "None"
        print(f"  [{status}] {t.name} | {pets} | {t.date} | {t.frequency}")


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


# ── Setup ──────────────────────────────────────────

owner = Owner(name="Alex")
scheduler = Scheduler(owner=owner)

mochi = Pet(name="Mochi", species="Cat", age_years=3.0)
biscuit = Pet(name="Biscuit", species="Dog", age_years=5.5, notes="Allergic to chicken")

owner.add_pet(mochi)
owner.add_pet(biscuit)

today = date(2026, 3, 28)
tomorrow = date(2026, 3, 29)

scheduler.add_task(Task("Morning Walk",   "Walk around the block",    False, "daily",   today,    ["Biscuit"]))
scheduler.add_task(Task("Evening Walk",   "Walk around the block",    False, "daily",   tomorrow, ["Biscuit"]))
scheduler.add_task(Task("Mochi Feeding",  "Half cup dry food",        False, "daily",   today,    ["Mochi"]))
scheduler.add_task(Task("Flea Treatment", "Apply topical treatment",  False, "monthly", today,    ["Mochi", "Biscuit"]))
scheduler.add_task(Task("Vet Checkup",    "Annual wellness exam",     False, "yearly",  tomorrow, ["Mochi"]))
scheduler.add_task(Task("House Rules",    "No pets on the sofa",      False, "always",  today,    []))

# ── Normal scenarios ───────────────────────────────

section("All tasks")
print_tasks("", scheduler.tasks)

section("Tasks for Biscuit")
print_tasks("", scheduler.get_tasks_for_pet("Biscuit"))

section("Tasks for Mochi")
print_tasks("", scheduler.get_tasks_for_pet("Mochi"))

section("Tasks for today")
print_tasks("", scheduler.get_tasks_for_date(today))

section("Mark 'Morning Walk' complete")
scheduler.mark_complete("Morning Walk")
print_tasks("Today's tasks after marking complete:", scheduler.get_tasks_for_date(today))

section("Remove Mochi and her tasks")
owner.remove_pet("Mochi", scheduler)
scheduler.remove_task("Mochi Feeding")
scheduler.remove_task("Vet Checkup")
print(f"\n  Owner's pets: {[p.name for p in owner.pets]}")
print_tasks("Remaining tasks:", scheduler.tasks)

# ── Edge cases ─────────────────────────────────────

section("Edge case: add duplicate pet")
try:
    owner.add_pet(Pet(name="Biscuit", species="Dog", age_years=5.5))
except ValueError as e:
    print(f"  ERROR: {e}")

section("Edge case: remove pet that doesn't exist")
try:
    owner.remove_pet("Rex", scheduler)
except ValueError as e:
    print(f"  ERROR: {e}")

section("Edge case: add task for unknown pet")
try:
    scheduler.add_task(Task("Bath Time", "Scrub scrub", False, "weekly", today, ["Rex"]))
except ValueError as e:
    print(f"  ERROR: {e}")

section("Edge case: merge task with same name for existing pet")
owner.add_pet(Pet(name="Mochi", species="Cat", age_years=3.0))
scheduler.add_task(Task("Evening Walk", "Walk around the block", False, "daily", tomorrow, ["Mochi"]))
print_tasks("Evening Walk after merging Mochi:", scheduler.get_tasks_for_pet("Mochi"))

section("Edge case: remove task that doesn't exist")
try:
    scheduler.remove_task("Yoga Session")
except ValueError as e:
    print(f"  ERROR: {e}")

section("Edge case: mark complete task that doesn't exist")
try:
    scheduler.mark_complete("Yoga Session")
except ValueError as e:
    print(f"  ERROR: {e}")

section("Edge case: task assigned to no pets")
print_tasks("Tasks with no pets assigned:", scheduler.get_unassigned_tasks())

section("Edge case: get tasks for date with no tasks")
print_tasks("Tasks for 2000-01-01:", scheduler.get_tasks_for_date(date(2000, 1, 1)))
