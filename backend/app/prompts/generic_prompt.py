"""
Prompt template for Step 6 when the classifier returns ``other``. Not in
the original suggested file list, but follows the same pattern as
invoice/resume/receipt so "other" documents still get a structured (if
loose) extraction instead of being skipped entirely.
"""

from __future__ import annotations

_GENERIC_JSON_SHAPE = """{
  "title": null,
  "summary": "",
  "key_value_pairs": {}
}"""


def build_generic_extraction_prompt(raw_text: str) -> str:
    return (
        "This document didn't match a known category. Summarize it and "
        "pull out any clearly-labeled fields into this exact JSON shape:\n\n"
        f"{_GENERIC_JSON_SHAPE}\n\n"
        "Document text:\n"
        "---\n"
        f"{raw_text.strip()}\n"
        "---\n\n"
        "Respond with ONLY the JSON object."
    )
