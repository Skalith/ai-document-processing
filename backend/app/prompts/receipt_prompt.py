"""Prompt template for Step 6: structured extraction of receipt documents."""

from __future__ import annotations

_RECEIPT_JSON_SHAPE = """{
  "merchant_name": "",
  "transaction_date": null,
  "transaction_time": null,
  "payment_method": null,
  "currency": null,
  "subtotal": null,
  "tax_amount": null,
  "total_amount": null,
  "items": [
    {"name": "", "quantity": null, "price": null}
  ]
}"""


def build_receipt_extraction_prompt(raw_text: str) -> str:
    return (
        "Extract the receipt details from the following document text into "
        "this exact JSON shape (fill in real values, keep the same keys):\n\n"
        f"{_RECEIPT_JSON_SHAPE}\n\n"
        "Document text:\n"
        "---\n"
        f"{raw_text.strip()}\n"
        "---\n\n"
        "Respond with ONLY the JSON object."
    )
