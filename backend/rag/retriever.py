"""
backend/rag/retriever.py
------------------------
TF-IDF retrieval over two sources:

  1. Curated FAQ — static JSON at backend/data/knowledge/pet_care_faq.json.
     Each chunk has: id, species, topic, title, content.

  2. Live user context — the owner's pets and upcoming tasks injected at
     query time so answers reflect the user's actual schedule and animals.

The retriever is intentionally dependency-free (no embeddings, no vector DB)
so the project stays lightweight and the scoring logic is fully auditable.

Public API
----------
retrieve(query, scheduler, top_k) -> list[dict]
    Returns the top_k most relevant chunks, each with an added "score" field.
    Live user context chunks are always included (they don't compete for slots).
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pawpal_system import Scheduler

# ---------------------------------------------------------------------------
# FAQ corpus location
# ---------------------------------------------------------------------------

_FAQ_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge" / "pet_care_faq.json"

# Module-level cache so the file is read only once per process.
_FAQ_CHUNKS: list[dict] | None = None


def _load_faq() -> list[dict]:
    global _FAQ_CHUNKS
    if _FAQ_CHUNKS is None:
        with open(_FAQ_PATH, encoding="utf-8") as fh:
            _FAQ_CHUNKS = json.load(fh)
    return _FAQ_CHUNKS


# ---------------------------------------------------------------------------
# Tokenisation helpers
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for", "of",
    "and", "or", "but", "not", "be", "are", "was", "were", "i", "my",
    "his", "her", "their", "what", "how", "when", "do", "does", "can",
    "should", "will", "with", "this", "that", "have", "has", "by",
}


def _tokenise(text: str) -> list[str]:
    """Lowercase, strip punctuation, remove stop words."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


# ---------------------------------------------------------------------------
# TF-IDF scorer
# ---------------------------------------------------------------------------

def _tf(tokens: list[str]) -> dict[str, float]:
    """Term frequency — normalised by document length."""
    if not tokens:
        return {}
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    return {t: c / total for t, c in counts.items()}


def _build_idf(corpus: list[list[str]]) -> dict[str, float]:
    """IDF over the FAQ corpus. Computed once per retrieval call."""
    n = len(corpus)
    df: dict[str, int] = {}
    for doc in corpus:
        for term in set(doc):
            df[term] = df.get(term, 0) + 1
    return {term: math.log((n + 1) / (freq + 1)) + 1.0 for term, freq in df.items()}


def _score(query_tokens: list[str], doc_tokens: list[str], idf: dict[str, float]) -> float:
    """TF-IDF dot product between query and document."""
    doc_tf = _tf(doc_tokens)
    total = 0.0
    for term in query_tokens:
        total += idf.get(term, 0.0) * doc_tf.get(term, 0.0)
    return total


# ---------------------------------------------------------------------------
# Live user context builder
# ---------------------------------------------------------------------------

def _user_context_chunks(scheduler: "Scheduler") -> list[dict]:
    """
    Synthesise a small set of plain-text chunks from the user's live data.
    These are always appended verbatim — they are not scored because they
    are unconditionally relevant to every query.
    """
    chunks: list[dict] = []
    pets = scheduler.owner.pets

    if not pets:
        return chunks

    # One chunk per pet describing species + age + notes
    for pet in pets:
        lines = [f"The owner has a {pet.species} named {pet.name} (age: {pet.age_years} years)."]
        if pet.notes:
            lines.append(f"Notes: {pet.notes}")

        # Upcoming tasks for this pet
        pet_tasks = [
            t for t in scheduler.tasks
            if pet.id in t.pet_ids and not t.completed
        ]
        if pet_tasks:
            task_summaries = [
                f"{t.name} on {t.date} ({t.priority} priority)"
                for t in sorted(pet_tasks, key=lambda x: x.date)[:5]
            ]
            lines.append("Upcoming tasks: " + "; ".join(task_summaries) + ".")

        chunks.append({
            "id": f"user-pet-{pet.id}",
            "species": pet.species.lower(),
            "topic": "user-data",
            "title": f"Live data for {pet.name}",
            "content": " ".join(lines),
            "score": None,  # always included, not ranked
            "source": "user-data",
        })

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve(query: str, scheduler: "Scheduler", top_k: int = 4) -> list[dict]:
    """
    Return the top_k FAQ chunks most relevant to the query, plus all live
    user-context chunks appended at the end.

    Each returned dict is a copy of the original FAQ chunk with two extra keys:
        "score"  — float (TF-IDF relevance score)
        "source" — "faq" | "user-data"

    Args:
        query:     The user's natural-language question.
        scheduler: The loaded Scheduler so live pet/task data can be included.
        top_k:     Maximum number of FAQ chunks to return (default 4).

    Returns:
        A list of chunk dicts sorted descending by score, followed by user
        context chunks.
    """
    faq_chunks = _load_faq()

    query_tokens = _tokenise(query)

    # Tokenise all FAQ documents for IDF calculation
    doc_token_lists = [_tokenise(chunk["title"] + " " + chunk["content"]) for chunk in faq_chunks]
    idf = _build_idf(doc_token_lists)

    # Score each FAQ chunk
    scored: list[dict] = []
    for chunk, doc_tokens in zip(faq_chunks, doc_token_lists):
        s = _score(query_tokens, doc_tokens, idf)
        scored.append({**chunk, "score": s, "source": "faq"})

    # Sort by score descending, take top_k
    scored.sort(key=lambda c: c["score"], reverse=True)
    top_chunks = scored[:top_k]

    # Append live user context (always included, no score competition)
    user_chunks = _user_context_chunks(scheduler)
    return top_chunks + user_chunks
