"""
Dynamic schema selection - Step 5 of the pipeline.

Given a classified `DocumentType`, returns the matching Pydantic model
class and its prompt-builder function. Adding a new document type is a
three-step, fully additive change:
  1. Add the value to DocumentType (app/models/schemas.py)
  2. Add a Pydantic schema under app/schemas/
  3. Add a prompt builder under app/prompts/ and register both below
"""

from __future__ import annotations

from typing import Callable, NamedTuple

from pydantic import BaseModel

from app.models.schemas import DocumentType
from app.prompts.generic_prompt import build_generic_extraction_prompt
from app.prompts.invoice_prompt import build_invoice_extraction_prompt
from app.prompts.receipt_prompt import build_receipt_extraction_prompt
from app.prompts.resume_prompt import build_resume_extraction_prompt
from app.schemas.generic import GenericDocumentData
from app.schemas.invoice import InvoiceData
from app.schemas.receipt import ReceiptData
from app.schemas.resume import ResumeData


class SchemaBinding(NamedTuple):
    model: type[BaseModel]
    build_prompt: Callable[[str], str]


_SCHEMA_REGISTRY: dict[DocumentType, SchemaBinding] = {
    DocumentType.INVOICE: SchemaBinding(InvoiceData, build_invoice_extraction_prompt),
    DocumentType.RESUME: SchemaBinding(ResumeData, build_resume_extraction_prompt),
    DocumentType.RECEIPT: SchemaBinding(ReceiptData, build_receipt_extraction_prompt),
    DocumentType.OTHER: SchemaBinding(GenericDocumentData, build_generic_extraction_prompt),
}


def get_schema_binding(document_type: DocumentType) -> SchemaBinding:
    """Returns the (schema, prompt_builder) pair for a document type, defaulting to generic."""
    return _SCHEMA_REGISTRY.get(document_type, _SCHEMA_REGISTRY[DocumentType.OTHER])
