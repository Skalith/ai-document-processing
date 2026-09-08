"""
Shared implementation for OpenAI-compatible Chat Completions providers
(Groq, NVIDIA NIM, Omniroute). Each provider only has to declare its
config field names and base URL; the call + usage-normalisation logic
lives here once.
"""

from __future__ import annotations

from openai import OpenAI

from app.config import get_settings
from app.services.llm.providers.base import LLMProvider, LLMResult

settings = get_settings()


class OpenAICompatibleProvider(LLMProvider):
    """Parameterised OpenAI-compatible backend (Chat Completions)."""

    name: str = ""
    api_key_field: str = ""
    model_field: str = ""
    base_url: str = ""

    def __init__(self) -> None:
        self.model = getattr(settings, self.model_field)
        self._client: OpenAI | None = None

    def available(self) -> bool:
        return bool(getattr(settings, self.api_key_field, None))

    def _api_key(self) -> str:
        return getattr(settings, self.api_key_field)

    def _client_instance(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self._api_key(), base_url=self.base_url)
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        temperature: float,
    ) -> LLMResult:
        response = self._client_instance().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = (response.choices[0].message.content or "") if response.choices else ""

        usage = getattr(response, "usage", None)
        usage_details = None
        if usage:
            usage_details = {
                "input": getattr(usage, "prompt_tokens", 0) or 0,
                "output": getattr(usage, "completion_tokens", 0) or 0,
            }

        return LLMResult(text=text, model=self.model, usage=usage_details)