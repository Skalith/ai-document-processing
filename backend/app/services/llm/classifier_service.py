"""
Classification service - Step 4 of the pipeline.

Sends the combined raw text to the LLM and maps its answer onto
`DocumentType`. Anything unrecognised (including a malformed/missing
response) resolves to DocumentType.OTHER rather than raising, since
classification failure shouldn't be fatal to the extract endpoint - the
router decides whether to fall back further from there.
"""

from __future__ import annotations

from loguru import logger

from app.core.exceptions import LLMServiceError
from app.models.schemas import DocumentType
from app.prompts.classifier import CLASSIFIER_SYSTEM_PROMPT, build_classification_prompt
from app.services.llm.llm_client import call_llm_for_json

_VALID_TYPES = {member.value for member in DocumentType}


async def classify_document(raw_text: str) -> DocumentType:
    """
    Classifies `raw_text` into one of DocumentType's categories.

    Raises LLMServiceError only when the LLM call itself fails (no API
    key, network error, etc.) - so the caller can distinguish "LLM is
    unavailable, fall back to plain OCR" from "LLM ran and said `other`".
    """
    if not raw_text or not raw_text.strip():
        return DocumentType.OTHER

    prompt = build_classification_prompt(raw_text)
    result = await call_llm_for_json(
        CLASSIFIER_SYSTEM_PROMPT, prompt, stage="document classification"
    )

    document_type = str(result.get("document_type", "")).strip().lower()
    if document_type not in _VALID_TYPES:
        logger.warning(
            "Classifier returned unrecognised document_type '{}'; defaulting to 'other'.",
            document_type,
        )
        return DocumentType.OTHER

    return DocumentType(document_type)


__all__ = ["classify_document", "LLMServiceError"]
