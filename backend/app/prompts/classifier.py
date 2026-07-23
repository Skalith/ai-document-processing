"""Prompt template for Step 4: LLM-based document classification."""

from __future__ import annotations

# Keep this in sync with app.models.schemas.DocumentType.
CLASSIFIER_SYSTEM_PROMPT = (
    "You classify raw text extracted from a scanned or digital document into "
    "exactly one category. Respond with ONLY a single JSON object of the "
    'shape {"document_type": "<category>"} and nothing else - no prose, no '
    "markdown code fences."
)

_MAX_CHARS_FOR_CLASSIFICATION = 6000


def build_classification_prompt(raw_text: str) -> str:
    """
    Builds the user-turn prompt for document-type classification.

    Truncates very long documents since classification only needs enough
    of the document to recognise its type, not the full text.
    """
    excerpt = raw_text.strip()[:_MAX_CHARS_FOR_CLASSIFICATION]

    return (
        "Classify the following document text into exactly one of these "
        "categories: invoice, resume, receipt, other.\n\n"
        "Guidelines:\n"
        "- invoice: a bill for goods/services, has line items and an amount due\n"
        "- resume: a CV/curriculum vitae listing a person's work experience, "
        "education, and skills\n"
        "- receipt: proof of a completed purchase/payment, usually short, "
        "from a store or vendor\n"
        "- other: anything that doesn't clearly fit the above\n\n"
        "Document text:\n"
        "---\n"
        f"{excerpt}\n"
        "---\n\n"
        'Respond with ONLY: {"document_type": "<category>"}'
    )
