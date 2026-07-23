"""
Structured schema for documents classified as ``invoice``.

Every field except ``invoice_number`` is optional because real-world
invoices vary wildly in what they include - the goal is graceful partial
extraction, not an all-or-nothing failure when one field is missing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class InvoiceLineItem(BaseModel):
    description: str = ""
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class InvoiceData(BaseModel):
    invoice_number: str = Field(default="", description="Invoice / bill number")
    vendor_name: str = Field(default="", description="The company issuing the invoice")
    customer_name: str | None = None
    invoice_date: str | None = Field(default=None, description="Date issued, as printed")
    due_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    billing_address: str | None = None
    notes: str | None = None
