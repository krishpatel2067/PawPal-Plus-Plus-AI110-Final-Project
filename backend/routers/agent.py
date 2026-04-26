"""
backend/routers/agent.py
------------------------
Agentic setup planner — two-step human-in-the-loop workflow:

  POST /agent/plan     — ask Gemini to produce a structured care plan
                         (pets + tasks) from free-text. Nothing is persisted.

  POST /agent/confirm  — accept the approved plan and create every pet and
                         task in the scheduler, then save.

The plan step uses Gemini's JSON-mode output (response_mime_type="application/json")
so the response is always parseable without fragile regex extraction.
"""

from __future__ import annotations

import datetime
import json
import os

from google import genai
from google.genai import types
from fastapi import APIRouter, Depends, HTTPException

from config import DEFAULT_USER_ID, GEMINI_MODEL, get_user_data_path
from dependencies import require_owner
from pawpal_system import Frequency, Pet, Priority, Scheduler, Task, save_data
from schemas import (
    AgentConfirmIn,
    AgentConfirmOut,
    AgentPlanIn,
    AgentPlanOut,
)

router = APIRouter(prefix="/agent", tags=["agent"])

# ---------------------------------------------------------------------------
# System prompt — instructs Gemini to produce structured JSON
# ---------------------------------------------------------------------------

_PLAN_SYSTEM = """\
You are PawPal++, a pet-care planning assistant.
Given the user's description, produce a structured JSON care plan.

Rules:
- Daily essentials (feeding, walks) → frequency "Daily", priority "HIGH".
- Weekly grooming → "Weekly", "MEDIUM".
- Monthly/annual vet checks → "Monthly" or "Yearly", "MEDIUM" or "HIGH".
- Use age 1.0 if unspecified for young animals; 5.0 for adults.
- Schedule recurring tasks starting from today's date.
- A task may apply to multiple pets: list all relevant pet names in pet_names.
- pet_names entries MUST exactly match names in the pets array; use [] for owner-level tasks.
- Limit to the most important 5-8 tasks to avoid overwhelming the owner.

Respond with ONLY a single JSON object — no markdown, no code fences — matching:
{
  "reasoning": [
    { "step": "<short step name>", "detail": "<1-2 sentence explanation>" }
  ],
  "pets": [
    { "name": "string", "species": "string", "age_years": number, "notes": "string" }
  ],
  "tasks": [
    {
      "name": "string",
      "description": "string",
      "frequency": "Once|Daily|Weekly|Monthly|Yearly",
      "priority": "HIGH|MEDIUM|LOW",
      "date": "YYYY-MM-DD",
      "time_start": "HH:MM or null",
      "duration_minutes": number,
      "pet_names": ["string"]
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# POST /agent/plan
# ---------------------------------------------------------------------------

@router.post("/plan", response_model=AgentPlanOut)
def plan(
    body: AgentPlanIn,
    scheduler: Scheduler = Depends(require_owner),
) -> AgentPlanOut:
    """
    Ask Gemini to draft a care plan from a free-text prompt.

    The plan is returned to the client as a preview — nothing is written to
    the data store at this stage. The client renders the plan and calls
    POST /agent/confirm to persist the approved version.

    Raises:
        503: GEMINI_API_KEY missing or Gemini call fails.
        502: Gemini response could not be parsed as valid JSON.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Set it in your .env file.",
        )

    today = datetime.date.today().isoformat()
    user_prompt = f"Today is {today}.\n\nUser request: {body.prompt}"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=_PLAN_SYSTEM,
                response_mime_type="application/json",
            ),
        )
        raw = response.text.strip()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Gemini API call failed: {exc}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini returned invalid JSON: {exc}. Raw: {raw[:200]}",
        )

    return AgentPlanOut(
        reasoning=data.get("reasoning", []),
        pets=data.get("pets", []),
        tasks=data.get("tasks", []),
    )


# ---------------------------------------------------------------------------
# POST /agent/confirm
# ---------------------------------------------------------------------------

@router.post("/confirm", response_model=AgentConfirmOut)
def confirm(
    body: AgentConfirmIn,
    scheduler: Scheduler = Depends(require_owner),
) -> AgentConfirmOut:
    """
    Persist an approved care plan by creating all pets and tasks.

    Pet creation order matters: tasks reference pets by name, so pets are
    created first and a name→id map is built before tasks are processed.

    Skips tasks whose date or enum values are invalid rather than aborting
    the whole batch — the client already validated these in the preview step.

    Returns counts of successfully created pets and tasks.

    All non-HTTP exceptions are caught and re-raised as HTTPException so that
    FastAPI's ExceptionMiddleware can handle them and CORSMiddleware can still
    attach the Access-Control-Allow-Origin header.  Plain ValueError / TypeError
    that escape the route handler reach ServerErrorMiddleware *after* CORS, so
    the 500 response would be missing the CORS header in the browser.
    """
    try:
        return _confirm_logic(body, scheduler)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to apply plan: {exc}")


def _confirm_logic(body: AgentConfirmIn, scheduler: Scheduler) -> AgentConfirmOut:
    name_to_id: dict[str, str] = {}
    pets_created = 0

    # ── Create pets ──────────────────────────────────────────────────────────
    for draft in body.pets:
        pet = Pet(
            name=draft.name.strip(),
            species=draft.species.strip(),
            age_years=draft.age_years,
            notes=draft.notes.strip(),
        )
        scheduler.owner.add_pet(pet)
        name_to_id[draft.name] = pet.id
        pets_created += 1

    # ── Create tasks ─────────────────────────────────────────────────────────
    tasks_created = 0
    for draft in body.tasks:
        # Parse date
        try:
            task_date = datetime.date.fromisoformat(draft.date)
        except ValueError:
            continue  # skip malformed dates

        # Parse time_start
        parsed_time = None
        if draft.time_start:
            try:
                parsed_time = datetime.time.fromisoformat(draft.time_start)
            except ValueError:
                parsed_time = None

        # Parse frequency enum
        try:
            frequency = Frequency(draft.frequency)
        except ValueError:
            frequency = Frequency.ONCE

        # Parse priority enum
        try:
            priority = Priority[draft.priority]
        except KeyError:
            priority = Priority.MEDIUM

        # Resolve all pet name references to UUIDs
        pet_ids = [
            name_to_id[n] for n in draft.pet_names if n in name_to_id
        ]

        task = Task(
            name=draft.name.strip(),
            description=draft.description.strip(),
            completed=False,
            frequency=frequency,
            date=task_date,
            priority=priority,
            pet_ids=pet_ids,
            time_start=parsed_time,
            duration_minutes=draft.duration_minutes,
        )
        scheduler.add_task(task)
        tasks_created += 1

    save_data(scheduler, get_user_data_path(DEFAULT_USER_ID))

    return AgentConfirmOut(
        pets_created=pets_created,
        tasks_created=tasks_created,
    )
