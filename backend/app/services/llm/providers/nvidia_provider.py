"""NVIDIA NIM / build API provider — OpenAI-compatible endpoint."""

from __future__ import annotations

from app.services.llm.providers.openai_compat import OpenAICompatibleProvider


class NvidiaProvider(OpenAICompatibleProvider):
    name = "nvidia"
    api_key_field = "nvidia_api_key"
    model_field = "nvidia_model"
    base_url = "https://integrate.api.nvidia.com/v1"