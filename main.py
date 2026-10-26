"""Root FastAPI entrypoint for Vercel multi-service deployment."""

from backend.api.main import app

__all__ = ["app"]
