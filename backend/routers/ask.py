"""
backend/routers/ask.py
----------------------
POST /ask  — RAG-powered pet-care advisor with a specialised persona.

Phase 6 additions
-----------------
* Persona: Pawsley — warm, playful, pet-loving tone.
* Structured output: Gemini is asked for JSON { answer, tips, vet_alert }
  so each section can be rendered distinctly in the UI.
* Guardrail: vet_alert fires only when the model detects a health risk;
  off-topic questions are refused by the system prompt.

Flow:
  1. Retrieve top FAQ chunks + live user data via TF-IDF.
  2. Build a grounded prompt with the retrieved context.
  3. Call Gemini in JSON mode and parse the structured response.
  4. Return { answer, tips, vet_alert, sources }.
"""

from __future__ import annotations

import json
import os

from google import genai
from google.genai import types
from fastapi import APIRouter, Depends, HTTPException

from config import GEMINI_MODEL
from dependencies import require_owner
from pawpal_system import Scheduler
from rag.retriever import retrieve
from schemas import AskIn, AskOut, SourceOut

router = APIRouter(prefix="/ask", tags=["advisor"])

# ---------------------------------------------------------------------------
# Persona & structured-output system prompt (Phase 6 specialisation)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are Pawsley, PawPal++'s warm and playful pet-care advisor who genuinely adores animals.
Your tone is friendly, encouraging, and occasionally uses light pet-themed warmth
("your fluffy friend", "your little furball") — but you never sacrifice accuracy for cuteness.

Answer using ONLY the information in the provided context.
If the context is insufficient, say so warmly and suggest consulting a vet.
Do NOT answer questions unrelated to pet care (cooking, finance, coding, etc.) — \
respond with a gentle redirect instead.
Do NOT invent facts, medication dosages, or treatments absent from the context.
Refer to the owner's actual pets by name when live data is relevant.

You MUST respond with a single JSON object — no markdown, no code fences:
{
  "answer":    "<main response, 2-5 sentences, friendly Pawsley tone>",
  "tips":      ["<short actionable tip>"],
  "vet_alert": "<calm urgent message if professional care may be needed, else null>"
}

Field rules:
  answer    — conversational, warm, grounded in context only.
  tips      — 0 to 3 practical bite-sized actions the owner can take today; \
empty array [] if none apply.
  vet_alert — set ONLY for symptoms, illness, injury, medication questions, or any \
situation where delaying professional care could harm the animal. \
Calm and clear, not alarmist. Null otherwise.
"""

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_prompt(question: str, chunks: list[dict]) -> str:
    """Assemble the grounded user-turn prompt sent to Gemini."""
    context_blocks = [
        f"[{chunk['title']}]\n{chunk['content']}" for chunk in chunks
    ]
    context_text = "\n\n".join(context_blocks)
    return (
        f"CONTEXT:\n{context_text}\n\n"
        f"USER QUESTION: {question}\n\n"
        "Please answer based on the context above."
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("", response_model=AskOut)
def ask_advisor(
    body: AskIn,
    scheduler: Scheduler = Depends(require_owner),
) -> AskOut:
    """
    Answer a pet-care question using retrieved context + Gemini (Pawsley persona).

    Returns a structured response — answer, tips, optional vet alert — alongside
    the source chunks used to ground the reply.

    Raises:
        503: GEMINI_API_KEY missing or Gemini call fails.
        502: Gemini returned unparseable JSON.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Set it in your .env file.",
        )

    # ── Retrieval ────────────────────────────────────────────────────────────
    chunks = retrieve(body.question, scheduler, top_k=4)
    prompt = _build_prompt(body.question, chunks)

    # ── Gemini call (JSON mode) ───────────────────────────────────────────────
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        raw = response.text.strip()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Gemini API call failed: {exc}")

    # ── Parse structured response ─────────────────────────────────────────────
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini returned invalid JSON: {exc}. Raw: {raw[:200]}",
        )

    # ── Sources ───────────────────────────────────────────────────────────────
    sources = [
        SourceOut(id=c["id"], title=c["title"], source=c.get("source", "faq"))
        for c in chunks
    ]

    return AskOut(
        answer=data.get("answer", ""),
        tips=data.get("tips", []),
        vet_alert=data.get("vet_alert") or None,
        sources=sources,
    )
