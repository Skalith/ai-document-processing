"""
Provider chain factory.

Picks which LLM backends are usable based on configured API keys and
returns them in the canonical priority order. Providers are instantiated
once and reused (mirrors the OCR _ENGINE_REGISTRY pattern).
"""

from __future__ import annotations

from app.services.llm.providers.anthropic_provider import AnthropicProvider
from app.services.llm.providers.base import LLMProvider
from app.services.llm.providers.gemini_provider import GeminiProvider
from app.services.llm.providers.groq_provider import GroqProvider
from app.services.llm.providers.nvidia_provider import NvidiaProvider
from app.services.llm.providers.omniroute_provider import OmnirouteProvider

# Priority order: OmniRoute is the primary gateway for all AI calls; the
# remaining providers are fallbacks if OmniRoute is unconfigured/failing.
_PROVIDER_CLASSES: list[type[LLMProvider]] = [
    OmnirouteProvider,
    GeminiProvider,
    GroqProvider,
    NvidiaProvider,
    AnthropicProvider,
]

_chain: list[LLMProvider] | None = None


def get_provider_chain() -> list[LLMProvider]:
    """
    Returns the configured providers in priority order (gemini first,
    anthropic last). Providers without an API key are skipped, so an empty
    list means no LLM at all (caller should fall back to plain OCR).
    """
    global _chain

    if _chain is None:
        _chain = [provider for provider in (cls() for cls in _PROVIDER_CLASSES) if provider.available()]

    return list(_chain)