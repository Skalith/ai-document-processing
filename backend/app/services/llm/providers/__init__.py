"""
LLM provider abstraction.

Mirrors the OCR engine factory pattern (services/ocr_service.py): every
provider implements `LLMProvider`, and `get_provider_chain()` builds the
ordered dispatch chain from whatever API keys are configured.

Priority order (first available = tried first):
    omniroute -> gemini -> groq -> nvidia -> anthropic

Failover is handled by the caller (llm_client.call_llm_for_json): each
provider is tried in order and the first that returns valid JSON wins.
OmniRoute is the primary gateway; the others act as fallbacks.
"""

from __future__ import annotations

from app.services.llm.providers.anthropic_provider import AnthropicProvider
from app.services.llm.providers.base import LLMProvider, LLMResult
from app.services.llm.providers.factory import get_provider_chain
from app.services.llm.providers.gemini_provider import GeminiProvider
from app.services.llm.providers.groq_provider import GroqProvider
from app.services.llm.providers.nvidia_provider import NvidiaProvider
from app.services.llm.providers.omniroute_provider import OmnirouteProvider

__all__ = [
    "LLMProvider",
    "LLMResult",
    "get_provider_chain",
    "GeminiProvider",
    "GroqProvider",
    "NvidiaProvider",
    "OmnirouteProvider",
    "AnthropicProvider",
]