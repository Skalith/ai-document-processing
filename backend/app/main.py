"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

Wires together:
  - CORS middleware (so the React frontend on a different port can call the API)
  - Global exception handling for our custom AppException hierarchy
  - The upload and extract routers
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_settings
from app.core.exceptions import AppException
from app.routers import extract, upload

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for uploading documents, running OCR "
    "(Tesseract / EasyOCR / PaddleOCR / Docling), and exporting "
    "results as Markdown, HTML, or JSON.",
    version="1.0.0",
    debug=settings.debug,
)

# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Global exception handling
# --------------------------------------------------------------------------

@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """
    Converts any custom AppException raised deep in the service layer into
    a clean, predictable JSON error response instead of a raw 500 trace.
    """
    logger.warning(f"AppException on {request.url.path}: {exc.message}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler so unexpected errors never leak stack traces."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500, content={"detail": "An unexpected server error occurred."}
    )


# --------------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------------

app.include_router(upload.router, prefix=settings.api_prefix)
app.include_router(extract.router, prefix=settings.api_prefix)


# --------------------------------------------------------------------------
# Health check
# --------------------------------------------------------------------------

@app.get("/health", tags=["Health"], summary="Simple liveness check")
async def health_check():
    return {"status": "ok", "app": settings.app_name}
