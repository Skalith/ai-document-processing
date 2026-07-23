"""
Centralised application configuration.

All environment-driven settings live here so the rest of the codebase
never touches os.environ directly. Values are loaded from a `.env` file
(see .env.example) or from real environment variables at runtime.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "Document Processing API"
    debug: bool = True
    api_prefix: str = "/api"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # --- Storage paths (relative to the backend/ directory) ---
    upload_dir: str = "storage/uploads"
    output_dir: str = "storage/outputs"
    max_upload_size_mb: int = 25

    # --- OCR engine configuration ---
    tesseract_cmd: str | None = None
    easyocr_languages: str = "en"
    paddleocr_lang: str = "en"
    docling_artifacts_path: str | None = None

    # --- Hybrid page-type detection (PyMuPDF) ---
    # A page is treated as "machine-readable" (text extracted directly,
    # no OCR needed) when PyMuPDF pulls out at least this many
    # non-whitespace characters of native text from it. Below this
    # threshold the page is treated as scanned/image-only and routed
    # through the selected OCR engine instead.
    min_native_text_chars: int = 20

    # --- LLM configuration (document classification + structured extraction) ---
    # Read from the ANTHROPIC_API_KEY environment variable by the Anthropic
    # SDK automatically; kept here too so the rest of the app can check
    # `settings.llm_enabled` without importing the SDK directly.
    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-4-5"
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_path(self) -> Path:
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def llm_enabled(self) -> bool:
        """
        Whether the LLM classification/structured-extraction pipeline can
        run at all. If no API key is configured, the extract pipeline
        fails soft and falls back to the original OCR-only formatted
        output - the app stays fully runnable without an LLM key.
        """
        import os

        return bool(self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"))


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor - avoids re-parsing .env on every call."""
    return Settings()
