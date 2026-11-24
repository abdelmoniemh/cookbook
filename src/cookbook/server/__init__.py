"""FastAPI web server: JSON API (docs/API.md), recipe photos and the built web UI."""
from .app import create_app

__all__ = ["create_app"]
