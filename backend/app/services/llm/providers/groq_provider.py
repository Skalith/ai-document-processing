"""Groq provider — OpenAI-compatible endpoint."""

from __future__ import annotations

from app.services.llm.providers.openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"
    api_key_field = "groq_api_key"
    model_field = "groq_model"
    base_url = "https://api.groq.com/openai/v1"