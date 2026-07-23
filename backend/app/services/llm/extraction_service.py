"""
Structured extraction + validation - Steps 6 and 7 of the pipeline.

Flow: raw text -> schema-specific prompt -> LLM -> raw JSON -> Pydantic
validation -> a plain dict the router/formatter can use.

Validation errors are not silently swallowed here (the router decides the
fallback policy); this module's job is just: call the LLM, validate
strictly, and raise a clear, typed error if either step fails.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.core.exceptions import LLMServiceError, SchemaValidationError
from app.models.schemas import DocumentType
from app.services.llm.llm_client import call_llm_for_json
from app.services.llm.schema_selector import get_schema_binding

_EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured data from raw document text and respond with "
    "ONLY a single valid JSON object matching the requested shape - no "
    "prose, no markdown code fences, no explanations. If a field isn't "
    "present in the text, use null (or an empty list/string as "
    "appropriate) instead of guessing."
)


async def extract_structured_data(raw_text: str, document_type: DocumentType) -> dict:
    """
    Runs schema-aware LLM extraction for `raw_text` and returns a
    validated, JSON-serialisable dict shaped like the schema registered
    for `document_type`.

    Raises:
        LLMServiceError: the LLM call itself failed (network, no API key, ...)
        SchemaValidationError: the LLM responded, but its JSON didn't fit
            the schema even after Pydantic's normal coercion.
    """
    schema_model, build_prompt = get_schema_binding(document_type)

    prompt = build_prompt(raw_text)
    raw_json = await call_llm_for_json(
        _EXTRACTION_SYSTEM_PROMPT, prompt, stage=f"{document_type.value} extraction"
    )

    try:
        validated = schema_model.model_validate(raw_json)
    except ValidationError as exc:
        raise SchemaValidationError(document_type.value, str(exc)) from exc

    return validated.model_dump(mode="json")


__all__ = ["extract_structured_data", "LLMServiceError", "SchemaValidationError"]
