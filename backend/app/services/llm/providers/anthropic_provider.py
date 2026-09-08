"""Anthropic (Claude) provider — official Anthropic Messages SDK."""

from __future__ import annotations

from app.config import get_settings
from app.services.llm.providers.base import LLMProvider, LLMResult

settings = get_settings()


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self) -> None:
        self.model = settings.anthropic_model
        self._client = None  # lazily initialised, see _client_instance()

    def available(self) -> bool:
        return bool(settings.anthropic_api_key)

    def _client_instance(self):
        if self._client is None:
            import anthropic  # deferred import: avoids the cost if unused

            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        temperature: float,
    ) -> LLMResult:
        response = self._client_instance().messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )

        usage_details = None
        usage = getattr(response, "usage", None)
        if usage is not None:
            usage_details = {
                "input": getattr(usage, "input_tokens", 0) or 0,
                "output": getattr(usage, "output_tokens", 0) or 0,
            }

        return LLMResult(text=text, model=self.model, usage=usage_details)