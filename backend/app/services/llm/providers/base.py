"""
Shared provider abstractions.

`LLMProvider` is the interface every LLM backend implements so the caller
(code in llm_client.py) never needs to know which vendor answered. A
provider is *available* only when its API key is configured, and its
`generate()` is a plain synchronous LLM call (executed off the event loop
via asyncio.to_thread).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResult:
    """Normalised output of a single LLM provider call."""

    text: str
    model: str
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Contract implemented by every supported LLM backend."""

    name: str
    """Stable identifier (gemini, groq, nvidia, omniroute, anthropic)."""

    @abstractmethod
    def available(self) -> bool:
        """True when this provider's API key is configured."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        temperature: float,
    ) -> LLMResult:
        """Synchronous single-turn completion. May raise on call failure."""