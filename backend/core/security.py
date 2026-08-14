# JWT validation lives in `api/deps.py` (the actual FastAPI dependency).
# This module re-exports the shared `settings` object so existing imports
# (`from core.security import settings`) keep working - `core/config.py`
# is the single source of truth for all environment configuration.
from core.config import settings

__all__ = ["settings"]
