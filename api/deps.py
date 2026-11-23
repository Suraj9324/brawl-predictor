"""FastAPI dependencies."""

from sqlalchemy.orm import Session

from db.session import get_db

# Re-export for convenient import in routes
__all__ = ["get_db"]
