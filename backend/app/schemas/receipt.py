"""Structured schema for documents classified as ``receipt``."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReceiptItem(BaseModel):
    name: str = ""
    quantity: float | None = None
    price: float | None = None


class ReceiptData(BaseModel):
    merchant_name: str = Field(default="", description="Store / merchant name")
    transaction_date: str | None = None
    transaction_time: str | None = None
    payment_method: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    items: list[ReceiptItem] = Field(default_factory=list)
