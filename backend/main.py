# backend/main.py
# ---------------------------------------------------------------------------
# FastAPI application entry point for PawPal++.
#
# Startup:
#   uvicorn main:app --reload          (from the backend/ directory)
#   uvicorn backend.main:app --reload  (from the project root)
#
# The .env file at the project root is loaded automatically so that
# GEMINI_API_KEY (and any future env vars) are available to all modules.
# ---------------------------------------------------------------------------

from dotenv import load_dotenv

# Load .env before anything else so os.environ is populated for all imports.
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import owner, pets, tasks, slots, ask, agent

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PawPal++ API",
    description="Backend API for the PawPal++ pet-care scheduling system.",
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
# Allow the Vite dev server (http://localhost:5173) to call this API.
# In production, replace the origin with the deployed frontend URL.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS, …
    allow_headers=["*"],  # Content-Type, Authorization, …
)

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
# Plain Python exceptions (ValueError, KeyError, etc.) that escape a route
# handler skip FastAPI's ExceptionMiddleware and reach ServerErrorMiddleware,
# which produces a 500 *after* CORSMiddleware has already run — so the
# response has no Access-Control-Allow-Origin header and the browser reports a
# CORS error instead of the real 500.  This handler converts every unhandled
# exception into a JSONResponse before that happens.


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


# Register all routers — each brings its own prefix and tags.
app.include_router(owner.router)
app.include_router(pets.router)
app.include_router(tasks.router)
app.include_router(slots.router)
app.include_router(ask.router)
app.include_router(agent.router)


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    """Liveness probe — confirms the API is running and reachable.

    Returns:
        JSON body ``{"status": "ok", "version": "2.0.0"}``.
    """
    return {"status": "ok", "version": "2.0.0"}
