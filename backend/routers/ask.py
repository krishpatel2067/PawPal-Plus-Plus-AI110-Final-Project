"""
backend/routers/ask.py
----------------------
POST /ask  — RAG-powered pet-care advisor.

Flow:
  1. Retrieve top FAQ chunks + live user data via TF-IDF (retriever.py).
  2. Build a structured prompt (system + user message) that grounds Gemini
     in the retrieved context.
  3. Call the Gemini API and return the answer + source citations.
"""

import os

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException

from config import GEMINI_MODEL
from dependencies import require_owner
from pawpal_system import Scheduler
from rag.retriever import retrieve
from schemas import AskIn, AskOut, SourceOut

router = APIRouter(prefix="/ask", tags=["advisor"])

# ---------------------------------------------------------------------------
# System prompt — defines the AI persona and grounding rules
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are PawPal++, a knowledgeable and friendly pet-care advisor.
Answer the user's question using ONLY the information provided in the context below.
If the context does not contain enough information to answer the question fully,
say so honestly and recommend consulting a licensed veterinarian.

Rules:
- Be concise: 2-5 sentences unless a longer answer is clearly warranted.
- Do not invent facts or medication dosages not present in the context.
- Refer to the owner's actual pets by name when the live data is relevant.
- Do not answer questions unrelated to pet care (e.g. cooking, finance, coding).
"""


def _build_prompt(question: str, chunks: list[dict]) -> str:
    """Assemble the grounded prompt sent to Gemini."""
    context_blocks: list[str] = []
    for chunk in chunks:
        header = f"[{chunk['title']}]"
        context_blocks.append(f"{header}\n{chunk['content']}")

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
    Answer a pet-care question using retrieved context + Gemini.

    The endpoint:
      - Runs TF-IDF retrieval over the FAQ + live user data.
      - Constructs a grounded prompt and calls the Gemini model.
      - Returns the model's answer alongside the source chunks used.

    Raises:
        422: If the request body is malformed.
        503: If the Gemini API key is missing or the model call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Set it in your .env file.",
        )

    # ── Retrieve relevant context ────────────────────────────────────────────
    chunks = retrieve(body.question, scheduler, top_k=4)

    # ── Build and send prompt ────────────────────────────────────────────────
    prompt = _build_prompt(body.question, chunks)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=_SYSTEM_PROMPT,
        )
        response = model.generate_content(prompt)
        answer = response.text.strip()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Gemini API call failed: {exc}",
        )

    # ── Build source list for the response ──────────────────────────────────
    sources = [
        SourceOut(
            id=chunk["id"],
            title=chunk["title"],
            source=chunk.get("source", "faq"),
        )
        for chunk in chunks
    ]

    return AskOut(answer=answer, sources=sources)
