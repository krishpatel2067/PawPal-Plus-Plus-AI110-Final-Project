import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state initialization ────────────────────

if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "task_form_version" not in st.session_state:
    st.session_state.task_form_version = 0
if "pet_form_version" not in st.session_state:
    st.session_state.pet_form_version = 0

# ── Section 1: Owner Setup ──────────────────────────

st.header("Owner Setup")

owner_name = st.text_input("Your name", placeholder="e.g. Alex")

if st.button("Create Owner"):
    if not owner_name.strip():
        st.error("Please enter a name.")
    else:
        st.session_state.owner = Owner(name=owner_name.strip())
        st.session_state.scheduler = Scheduler(owner=st.session_state.owner)
        st.success(f"Welcome, {owner_name.strip()}!")

if st.session_state.owner:
    st.caption(f"Current owner: **{st.session_state.owner.name}**")

# ── Section 2: Manage Pets ──────────────────────────

if st.session_state.owner:
    st.divider()
    st.header("Manage Pets")

    with st.form(f"add_pet_form_{st.session_state.pet_form_version}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_name = st.text_input("Name")
        with col2:
            species = st.text_input("Species", placeholder="e.g. Cat, Dog")
        with col3:
            age = st.number_input("Age (years)", min_value=0.0, step=0.5)
        notes = st.text_input("Notes", placeholder="e.g. Allergic to chicken")
        submitted = st.form_submit_button("Add Pet")

    if submitted:
        if not pet_name.strip() or not species.strip():
            st.error("Name and species are required.")
        else:
            try:
                st.session_state.owner.add_pet(
                    Pet(
                        name=pet_name.strip(),
                        species=species.strip(),
                        age_years=age,
                        notes=notes.strip(),
                    )
                )
                st.success(f"Added {pet_name.strip()}!")
                st.session_state.pet_form_version += 1
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    pets = st.session_state.owner.pets
    if not pets:
        st.info("No pets yet. Add one above.")
    else:
        for pet in pets:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"**{pet.name}** — {pet.species}, {pet.age_years}y"
                    + (f" _{pet.notes}_" if pet.notes else "")
                )
            with col2:
                if st.button("🗑️", key=f"remove_pet_{pet.name}"):
                    try:
                        st.session_state.owner.remove_pet(
                            pet.name, st.session_state.scheduler
                        )
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

# ── Section 3: Tasks ────────────────────────────────

if st.session_state.owner:
    st.divider()
    st.header("Tasks")

    pet_names = [p.name for p in st.session_state.owner.pets]

    with st.form(f"add_task_form_{st.session_state.task_form_version}"):
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("Task name")
            frequency = st.text_input("Frequency", placeholder="e.g. daily, weekly")
            priority = st.selectbox("Priority", [p.name for p in Priority])
        with col2:
            description = st.text_input("Description")
            task_date = st.date_input("Date", value=date.today())
            assigned_pets = st.multiselect("Assign to pets", pet_names)
        submitted = st.form_submit_button("Add Task")

    if submitted:
        if not task_name.strip() or not frequency.strip():
            st.error("Task name and frequency are required.")
        else:
            try:
                st.session_state.scheduler.add_task(
                    Task(
                        name=task_name.strip(),
                        description=description.strip(),
                        completed=False,
                        frequency=frequency.strip(),
                        date=task_date,
                        priority=Priority[priority],
                        pet_names=assigned_pets,
                    )
                )
                st.success(f"Added task '{task_name.strip()}'!")
                st.session_state.task_form_version += 1
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.subheader("Schedule")
    col1, col2 = st.columns(2)
    with col1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names)
    with col2:
        filter_date = st.date_input("Filter by date", value=None, key="filter_date")

    scheduler = st.session_state.scheduler
    if filter_pet != "All" and filter_date:
        tasks = [
            t for t in scheduler.get_tasks_for_pet(filter_pet) if t.date == filter_date
        ]
    elif filter_pet != "All":
        tasks = scheduler.get_tasks_for_pet(filter_pet)
    elif filter_date:
        tasks = scheduler.get_tasks_for_date(filter_date)
    else:
        tasks = scheduler.get_tasks_by_priority()

    if not tasks:
        st.info("No tasks match the current filter.")
    else:
        for task in tasks:
            col1, col2, col3 = st.columns([5, 1, 1])
            status = "✓" if task.completed else "○"
            pets_label = ", ".join(task.pet_names) if task.pet_names else "None"
            with col1:
                st.markdown(
                    f"**[{status}] {task.name}** | {task.priority.name} | {pets_label} | {task.date} | {task.frequency}"
                )
                if task.description:
                    st.caption(task.description)
            with col2:
                if not task.completed:
                    if st.button("✅", key=f"complete_{task.name}"):
                        st.session_state.scheduler.mark_complete(task.name)
                        st.rerun()
            with col3:
                if st.button("🗑️", key=f"remove_task_{task.name}"):
                    try:
                        st.session_state.scheduler.remove_task(task.name)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

# TODO: make priority not default
# TODO: add none to filter by pets
