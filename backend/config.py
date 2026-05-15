"""
backend/config.py
-----------------
Central configuration for the PawPal++ backend.

All paths are resolved relative to this file's location (backend/) so the
server works correctly regardless of which directory it is started from.
Environment variables are loaded from the project-root .env file via
python-dotenv — see main.py for the load_dotenv() call.
"""

from pathlib import Path

# ── Directory layout ──────────────────────────────────────────────────────────

# Absolute path to the backend/ directory itself, no matter where Python is run from.
BACKEND_DIR: Path = Path(__file__).resolve().parent

# Root directory where all user data subdirectories live.
# Structure: backend/data/users/<user_id>/pawpal_data.json
DATA_ROOT: Path = BACKEND_DIR / "data" / "users"

# ── Application constants ─────────────────────────────────────────────────────

# The Gemini model identifier used for all AI calls.
# Changing this one constant updates every AI call in the system.
GEMINI_MODEL: str = "gemini-3.1-flash-lite"

# The user ID used when no authentication is in place (Phase 1 / prototype).
# Future phases can replace this with a real user identity from an auth token.
DEFAULT_USER_ID: str = "default"

# The filename that holds each user's serialized Owner + Task data.
DATA_FILENAME: str = "pawpal_data.json"

# ── Helper functions ──────────────────────────────────────────────────────────


def get_user_data_path(user_id: str = DEFAULT_USER_ID) -> Path:
    """Return the absolute path to a user's data file.

    Args:
        user_id: The user identifier. Defaults to DEFAULT_USER_ID ("default").

    Returns:
        A pathlib.Path pointing to backend/data/users/<user_id>/pawpal_data.json.
        The parent directory is created automatically if it does not yet exist,
        so callers never need to mkdir before writing.

    Example:
        >>> get_user_data_path()
        PosixPath('.../backend/data/users/default/pawpal_data.json')
    """
    user_dir = DATA_ROOT / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / DATA_FILENAME
