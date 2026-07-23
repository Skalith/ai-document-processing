"""
Thin wrapper around the Anthropic Messages API.

Kept in one place so classifier_service and extraction_service don't each
duplicate SDK setup, error handling, and JSON-parsing boilerplate. The
Anthropic Python SDK is synchronous, so calls are offloaded to a thread
via `asyncio.to_thread` to avoid blocking the FastAPI event loop.
"""

from __future__ import annotations

import asyncio
import json
import re

from loguru import logger

from app.config import get_settings
from app.core.exceptions import LLMServiceError

settings = get_settings()

_client = None  # lazily-initialised singleton, see _get_client()


def _get_client():
    global _client
    if _client is None:
        import anthropic  # deferred import: avoids the cost if LLM features go unused

        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _extract_json_object(raw_response_text: str) -> dict:
    """
    Best-effort extraction of a single JSON object from the model's reply.
    Models occasionally wrap JSON in markdown code fences despite being
    asked not to, so this strips those before parsing.
    """
    text = raw_response_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: grab the first {...} block in case the model added
        # any stray commentary around the JSON.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


async def call_llm_for_json(system_prompt: str, user_prompt: str, *, stage: str) -> dict:
    """
    Sends a single-turn prompt to the configured Claude model and parses
    the reply as a JSON object.

    Raises LLMServiceError (never a raw exception) on any failure, so
    callers can catch one exception type and fail soft.
    """
    if not settings.llm_enabled:
        raise LLMServiceError(stage, "no ANTHROPIC_API_KEY is configured")

    def _run_sync() -> str:
        client = _get_client()
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )

    try:
        raw_text = await asyncio.to_thread(_run_sync)
        return _extract_json_object(raw_text)
    except LLMServiceError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalise every failure mode
        logger.warning("LLM call failed during {}: {}", stage, exc)
        raise LLMServiceError(stage, str(exc)) from exc
