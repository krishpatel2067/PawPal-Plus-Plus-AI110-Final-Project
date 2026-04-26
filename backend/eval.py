"""
backend/eval.py
---------------
Offline evaluation / reliability harness for PawPal++.

Run from the backend/ directory:
    python eval.py

What it tests
-------------
1. RAG retrieval quality
   For each probe query, assert that the expected FAQ chunk id ranks in the
   top-k results returned by the retriever.

2. Advisor guardrails — off-topic refusal
   Ask Gemini questions that are not about pet care.  The answer must
   contain a redirect phrase rather than a substantive reply.

3. Advisor guardrails — vet_alert firing
   Ask questions about symptoms / illness.  The vet_alert field must be
   non-null so the user is always prompted to seek professional help.

4. Advisor guardrails — vet_alert NOT firing for benign questions
   Ask routine care questions.  vet_alert must be null so the UI does not
   cry wolf on every response.

5. Structured-output completeness
   Every Gemini response must include all required keys (answer, tips,
   vet_alert) so the frontend never receives an unexpected schema.

Scoring
-------
Each test case is worth 1 point.  The script prints a summary and exits
with code 0 on a perfect score, 1 on any failure.

Environment
-----------
Requires GEMINI_API_KEY in the environment (loaded from ../.env automatically).
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path

# Load .env from project root before any imports that read env vars.
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from google import genai
from google.genai import types

from config import GEMINI_MODEL
from pawpal_system import Owner, Pet, Scheduler
from rag.retriever import retrieve

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"

# Seconds to wait between consecutive Gemini calls to stay under the free-tier
# rate limit (15 RPM on Flash).  All 8 live calls are separated by this delay.
_GEMINI_COOLDOWN = 30

# Rough estimate of how long a single Gemini Flash response takes (seconds).
_GEMINI_RESPONSE_TIME = 30


def _cooldown() -> None:
    """Sleep between Gemini calls, then announce the outgoing call."""
    for remaining in range(_GEMINI_COOLDOWN, 0, -5):
        print(f"    cooldown: {remaining:2d}s remaining…", end="\r", flush=True)
        time.sleep(5)
    # End with a real newline so the next print starts on a fresh line.
    print("    calling Gemini…                    ", flush=True)


@dataclass
class Result:
    name: str
    passed: bool
    detail: str = ""


def _report(r: Result) -> None:
    """Print a single result line immediately — used for live streaming output."""
    icon = PASS if r.passed else FAIL
    print(f"  {icon}  {r.name}")
    if not r.passed:
        wrapped = textwrap.fill(
            r.detail, width=72, initial_indent="        ", subsequent_indent="        "
        )
        print(wrapped)


def _make_scheduler() -> Scheduler:
    """Minimal in-memory scheduler with one dog — used for retrieval tests."""
    owner = Owner(name="Eval User")
    dog = Pet(name="Rex", species="dog", age_years=3.0, notes="healthy")
    owner.add_pet(dog)
    return Scheduler(owner=owner)


def _ask_gemini(question: str, context_chunks: list[dict]) -> dict:
    """Call Gemini with the Pawsley system prompt and return parsed JSON."""
    from routers.ask import (
        _SYSTEM_PROMPT,
        _build_prompt,
    )  # local import to avoid circular

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set — cannot run Gemini tests.")

    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(question, context_chunks)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text.strip())


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------


def run_retrieval_tests(scheduler: Scheduler) -> list[Result]:
    """Assert expected FAQ chunks rank in the top-4 for known queries."""
    probes = [
        ("how often should I feed my dog", "dog-feeding"),
        ("how much exercise does a cat need", "cat-exercise"),
        ("rabbit grooming tips", "rabbit-grooming"),
        ("hamster health warning signs", "hamster-health"),
        ("bird vaccination schedule", "bird-vaccinations"),
        ("fish feeding frequency", "fish-feeding"),
    ]

    results: list[Result] = []
    for query, expected_id in probes:
        chunks = retrieve(query, scheduler, top_k=4)
        faq_ids = [c["id"] for c in chunks if c.get("source") == "faq"]
        passed = expected_id in faq_ids
        results.append(
            Result(
                name=f"retrieval: '{query[:40]}'",
                passed=passed,
                detail=f"expected '{expected_id}' in top-4, got {faq_ids}",
            )
        )
    return results


def run_guardrail_tests(scheduler: Scheduler) -> list[Result]:
    """Call Gemini and check guardrail behaviour."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return [
            Result(
                name="guardrails (all)",
                passed=False,
                detail="GEMINI_API_KEY not set — skipped",
            )
        ]

    results: list[Result] = []

    # ── Off-topic refusal ──────────────────────────────────────────────────
    off_topic_queries = [
        "What is the capital of France?",
        "How do I make pasta carbonara?",
        "Write me a Python function to sort a list.",
    ]
    refusal_phrases = [
        "pet",
        "paw",
        "animal",
        "redirect",
        "care",
        "not able",
        "can't help",
        "outside",
        "unrelated",
        "speciali",
    ]

    for q in off_topic_queries:
        try:
            _cooldown()
            chunks = retrieve(q, scheduler, top_k=4)
            data = _ask_gemini(q, chunks)
            answer_lower = data.get("answer", "").lower()
            # The answer should NOT give a substantive off-topic reply.
            # It should contain a redirect or pet-care reference instead.
            passed = any(phrase in answer_lower for phrase in refusal_phrases)
            results.append(
                Result(
                    name=f"off-topic refusal: '{q[:40]}'",
                    passed=passed,
                    detail=f"answer: {data.get('answer', '')[:120]}",
                )
            )
        except Exception as exc:
            results.append(
                Result(
                    name=f"off-topic refusal: '{q[:40]}'",
                    passed=False,
                    detail=f"exception: {exc}",
                )
            )
        _report(results[-1])

    # ── vet_alert fires for health concerns ────────────────────────────────
    health_queries = [
        ("my dog is vomiting and lethargic", "dog-health"),
        ("my cat has not eaten for three days", "cat-health"),
    ]

    for q, hint_id in health_queries:
        try:
            _cooldown()
            chunks = retrieve(q, scheduler, top_k=4)
            data = _ask_gemini(q, chunks)
            passed = bool(data.get("vet_alert"))
            results.append(
                Result(
                    name=f"vet_alert fires: '{q[:40]}'",
                    passed=passed,
                    detail=f"vet_alert={data.get('vet_alert', '')[:80]}",
                )
            )
        except Exception as exc:
            results.append(
                Result(
                    name=f"vet_alert fires: '{q[:40]}'",
                    passed=False,
                    detail=f"exception: {exc}",
                )
            )
        _report(results[-1])

    # ── vet_alert is null for benign questions ─────────────────────────────
    benign_queries = [
        "how often should I brush my dog",
        "what fruit can rabbits eat",
    ]

    for q in benign_queries:
        try:
            _cooldown()
            chunks = retrieve(q, scheduler, top_k=4)
            data = _ask_gemini(q, chunks)
            passed = not data.get("vet_alert")
            results.append(
                Result(
                    name=f"vet_alert silent: '{q[:40]}'",
                    passed=passed,
                    detail=f"vet_alert={data.get('vet_alert')}",
                )
            )
        except Exception as exc:
            results.append(
                Result(
                    name=f"vet_alert silent: '{q[:40]}'",
                    passed=False,
                    detail=f"exception: {exc}",
                )
            )
        _report(results[-1])

    # ── Structured-output completeness ─────────────────────────────────────
    completeness_query = "how much should I feed my adult dog per day"
    required_keys = {"answer", "tips", "vet_alert"}

    try:
        _cooldown()
        chunks = retrieve(completeness_query, scheduler, top_k=4)
        data = _ask_gemini(completeness_query, chunks)
        missing = required_keys - set(data.keys())
        passed = len(missing) == 0
        results.append(
            Result(
                name="structured-output completeness",
                passed=passed,
                detail=f"missing keys: {missing}" if missing else "all keys present",
            )
        )
    except Exception as exc:
        results.append(
            Result(
                name="structured-output completeness",
                passed=False,
                detail=f"exception: {exc}",
            )
        )
    _report(results[-1])

    return results


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main() -> None:
    print("\n" + "=" * 60)
    print("  PawPal++ Reliability Harness")
    print("=" * 60 + "\n")

    scheduler = _make_scheduler()
    all_results: list[Result] = []

    print("── RAG Retrieval ──────────────────────────────────────────")
    retrieval = run_retrieval_tests(scheduler)
    all_results.extend(retrieval)
    for r in retrieval:
        icon = PASS if r.passed else FAIL
        print(f"  {icon}  {r.name}")
        if not r.passed:
            print(f"        {r.detail}")

    gemini_calls = 8  # 3 off-topic + 2 vet-alert fires + 2 vet-alert silent + 1 schema
    secs_per_call = _GEMINI_COOLDOWN + _GEMINI_RESPONSE_TIME
    estimated = gemini_calls * secs_per_call // 60
    print(
        f"\n── Advisor Guardrails ({gemini_calls} live Gemini calls, ~{estimated} min) ──────"
    )
    # Results are printed live inside run_guardrail_tests via _report().
    guardrails = run_guardrail_tests(scheduler)
    all_results.extend(guardrails)

    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} failed)")
    else:
        print("  — perfect score!")
    print("=" * 60 + "\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
