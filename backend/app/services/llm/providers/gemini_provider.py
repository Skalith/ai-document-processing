"""Gemini provider — via the official google-genai SDK."""

from __future__ import annotations

from google import genai
from google.genai import types

from app.config import get_settings
from app.services.llm.providers.base import LLMProvider, LLMResult

settings = get_settings()


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.model = settings.gemini_model
        self._client: genai.Client | None = None

    def available(self) -> bool:
        return bool(settings.gemini_api_key)

    def _client_instance(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int,
        temperature: float,
    ) -> LLMResult:
        response = self._client_instance().models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        text = response.text or ""

        usage_details = None
        meta = getattr(response, "usage_metadata", None)
        if meta is not None:
            usage_details = {
                "input": getattr(meta, "prompt_token_count", 0) or 0,
                "output": getattr(meta, "candidates_token_count", 0) or 0,
            }

        return LLMResult(text=text, model=self.model, usage=usage_details)