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

    # --- LLM configuration (classification + structured extraction) ---
    # Providers are tried in priority order: omniroute -> gemini -> groq ->
    # nvidia -> anthropic. A provider is only used when its API key is
    # set; if a call fails the next configured provider takes over, and if
    # all providers fail the extract router falls back to plain OCR.
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.0

    # Gemini (Google)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"

    # Groq (OpenAI-compatible endpoint)
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"

    # NVIDIA NIM / build API (OpenAI-compatible endpoint)
    nvidia_api_key: str | None = None
    nvidia_model: str = "meta/llama-3.3-70b-instruct"

    # Omniroute (OpenAI-compatible gateway/router; `auto` = zero-config routing)
    omniroute_api_key: str | None = None
    omniroute_model: str = "auto"
    omniroute_base_url: str = "http://localhost:20128/v1"

    # Anthropic (Claude)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    # --- Langfuse observability (optional LLM tracing) ---
    # Traces model + token usage for every LLM call to a Langfuse instance.
    # Tracing is a no-op until both keys are set. The mirror fields map
    # 1:1 onto the SDK's LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY /
    # LANGFUSE_BASE_URL environment variables.
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"

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
        Whether any LLM provider (gemini, groq, nvidia, omniroute,
        anthropic) is configured. If no API key is configured at all, the
        extract pipeline fails soft and falls back to the original
        OCR-only formatted output - the app stays fully runnable without
        any LLM key.
        """
        import os

        provider_keys = [
            self.anthropic_api_key,
            self.gemini_api_key,
            self.groq_api_key,
            self.nvidia_api_key,
            self.omniroute_api_key,
        ]
        if any(provider_keys):
            return True

        env_keys = [
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "NVIDIA_API_KEY",
            "OMNIROUTE_API_KEY",
        ]
        return any(os.environ.get(key) for key in env_keys)

    @property
    def langfuse_enabled(self) -> bool:
        """Whether Langfuse tracing is active (requires both public+secret key)."""
        import os

        return bool(
            (self.langfuse_public_key or os.environ.get("LANGFUSE_PUBLIC_KEY"))
            and (self.langfuse_secret_key or os.environ.get("LANGFUSE_SECRET_KEY"))
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor - avoids re-parsing .env on every call."""
    return Settings()
