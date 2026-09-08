"""
LLM dispatch facade with multi-provider failover and Langfuse tracing.

Single entry point used by the rest of the pipeline is
`call_llm_for_json(system_prompt, user_prompt, stage=...)`. Internally it:

  1. Builds the provider chain via the factory (priority order:
     omniroute -> gemini -> groq -> nvidia -> anthropic). Providers
     without a configured API key are skipped.
  2. Tries each provider in turn. The first one that returns parseable
     JSON wins; any failure (network, auth, rate-limit, malformed JSON)
     moves on to the next provider.
  3. If every provider fails, raises LLMServiceError so the extract
     router can fall back to the plain OCR-formatted output.

Provider calls are synchronous SDK calls, so each is offloaded to a
worker thread via `asyncio.to_thread` to avoid blocking the event loop.

Observability: every invocation becomes a Langfuse `span`; each provider
attempt is a nested `generation` carrying the provider, model, prompt,
reply, and token usage. Without Langfuse keys the decorators are no-ops.
"""

from __future__ import annotations

import asyncio
import json
import os
import re

from loguru import logger

from app.config import get_settings
from app.core.exceptions import LLMServiceError
from app.services.llm.providers.base import LLMProvider, LLMResult
from app.services.llm.providers.factory import get_provider_chain

settings = get_settings()


# --------------------------------------------------------------------------
# Langfuse (optional). Everything here is lazy and exception-free: the app
# runs and traces exactly as well without Langfuse keys as with them.
# --------------------------------------------------------------------------

def _langfuse_observe(**kwargs):
    """
    No-op-safe stand-in for langfuse's `@observe` decorator.

    Returns a pass-through decorator when langfuse is not installed, so
    the LLM client keeps working even in minimal installs.
    """
    try:
        from langfuse import observe
    except ImportError:  # pragma: no cover - exercised only on minimal installs
        def _passthrough(func):
            return func

        return _passthrough
    return observe(**kwargs)


def _mirror_langfuse_env() -> None:
    """
    Expose the Langfuse settings from backend/.env to the Langfuse SDK.

    Our config loads the values into Settings from .env, but the SDK reads
    LANGFUSE_* straight from os.environ. Mirror them so `get_client()` and
    the `@observe` decorator resolve the same project.
    """
    if settings.langfuse_public_key:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    if settings.langfuse_secret_key:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    if settings.langfuse_base_url:
        os.environ.setdefault("LANGFUSE_BASE_URL", settings.langfuse_base_url)


_mirror_langfuse_env()


def _langfuse():
    """
    The enabled Langfuse client, or None when tracing is off.

    Never raises: a broken/missing client just disables tracing.
    """
    if not settings.langfuse_enabled:
        return None
    _mirror_langfuse_env()
    try:
        from langfuse import get_client
    except ImportError:  # pragma: no cover - exercised only on minimal installs
        return None
    return get_client()


# --------------------------------------------------------------------------
# Base LLM call from a single provider
# --------------------------------------------------------------------------

@_langfuse_observe(as_type="generation", name="llm-provider-call")
def _call_provider(
    provider: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    *,
    stage: str,
    max_tokens: int,
    temperature: float,
) -> LLMResult:
    """
    Synchronous call to one provider. This is the Langfuse `generation`
    observation: the provider, model, prompt/reply, and token usage are
    attached to the enclosing trace afterwards.

    Runs inside `asyncio.to_thread`, so it is plain blocking SDK code.
    """
    result = provider.generate(
        system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature
    )

    # Best-effort telemetry: tracing mistakes must never fail the LLM call.
    try:
        langfuse = _langfuse()
        if langfuse is not None:
            langfuse.update_current_generation(
                name=f"{provider.name}.generate",
                input=user_prompt,
                output=result.text,
                model=result.model,
                model_parameters={"temperature": temperature, "max_tokens": max_tokens},
                usage_details=result.usage or {},
                metadata={"stage": stage, "provider": provider.name, "system_prompt": system_prompt},
            )
    except Exception:  # noqa: BLE001 - telemetry is best-effort by design
        logger.debug("Langfuse tracing skipped during {}", stage)

    return result


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


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------

@_langfuse_observe(as_type="span", name="call_llm_for_json")
async def call_llm_for_json(system_prompt: str, user_prompt: str, *, stage: str) -> dict:
    """
    Sends a single-turn prompt through the provider chain and parses the
    reply as a JSON object.

    Each invocation is a Langfuse `span`; the individual provider attempts
    nest under it as `generation` observations (contextvars propagate
    automatically through asyncio.to_thread).

    Raises LLMServiceError (never a raw exception) once every provider has
    failed, so callers can catch one exception type and fail soft to the
    OCR-only output.
    """
    chain = get_provider_chain()
    if not chain:
        raise LLMServiceError(
            stage,
            "no LLM API key is configured (gemini / groq / nvidia / omniroute / anthropic)",
        )

    failures: list[str] = []
    for provider in chain:
        try:
            result = await asyncio.to_thread(
                _call_provider,
                provider,
                system_prompt,
                user_prompt,
                stage=stage,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )
            return _extract_json_object(result.text)
        except Exception as exc:  # noqa: BLE001 - provider failover, see module docstring
            failures.append(f"{provider.name}: {exc}")
            logger.warning(
                "LLM provider {} failed during {} ({}); trying next provider.",
                provider.name,
                stage,
                exc,
            )

    detail = "; ".join(failures)
    raise LLMServiceError(stage, f"all LLM providers failed [{detail}]")