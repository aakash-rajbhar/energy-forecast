"""FastAPI application entrypoint with middleware and routes."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import router as api_router

app = FastAPI(
    title="UK Wind Forecast Accuracy API",
    description="Elexon BMRS day-ahead wind generation forecast accuracy analysis for UK power buyers.",
    version="1.0.0",
)

# Configure CORS for local development and deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app.include_router(api_router, prefix="/api")

# Mount frontend build if directory exists (for Docker and unified container deploy)
# On Vercel, static frontend is served by the Vercel frontend service
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if STATIC_DIR.is_dir() and not os.environ.get("VERCEL"):
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static_frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "UK Wind Forecast Accuracy Analysis API",
            "docs": "/docs",
            "health": "/api/health",
        }


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
