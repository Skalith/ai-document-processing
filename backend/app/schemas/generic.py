"""
Fallback schema used whenever the classifier assigns ``other`` - i.e. the
document doesn't fit invoice / resume / receipt. Keeps a free-form
key/value bag plus a short summary so the pipeline still returns something
structured rather than nothing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenericDocumentData(BaseModel):
    title: str | None = None
    summary: str = Field(default="", description="Short summary of the document's content")
    key_value_pairs: dict[str, str] = Field(
        default_factory=dict,
        description="Any clearly-labeled fields the LLM could confidently pull out",
    )
