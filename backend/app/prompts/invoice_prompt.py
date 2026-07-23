"""Prompt template for Step 6: structured extraction of invoice documents."""

from __future__ import annotations

EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured data from raw document text and respond with "
    "ONLY a single valid JSON object matching the requested shape - no "
    "prose, no markdown code fences, no explanations. If a field isn't "
    "present in the text, use null (or an empty list/string as "
    "appropriate) instead of guessing."
)

_INVOICE_JSON_SHAPE = """{
  "invoice_number": "",
  "vendor_name": "",
  "customer_name": null,
  "invoice_date": null,
  "due_date": null,
  "currency": null,
  "subtotal": null,
  "tax_amount": null,
  "total_amount": null,
  "line_items": [
    {"description": "", "quantity": null, "unit_price": null, "amount": null}
  ],
  "billing_address": null,
  "notes": null
}"""


def build_invoice_extraction_prompt(raw_text: str) -> str:
    return (
        "Extract the invoice details from the following document text into "
        "this exact JSON shape (fill in real values, keep the same keys):\n\n"
        f"{_INVOICE_JSON_SHAPE}\n\n"
        "Document text:\n"
        "---\n"
        f"{raw_text.strip()}\n"
        "---\n\n"
        "Respond with ONLY the JSON object."
    )
