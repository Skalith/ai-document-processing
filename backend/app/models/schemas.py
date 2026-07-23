"""
Pydantic models (schemas) shared between routers and services.

These define the exact shape of every request body and JSON response the
API produces, giving automatic validation + OpenAPI docs for free.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Enums - keep these in sync with the frontend's dropdown / radio options
# --------------------------------------------------------------------------

class OCREngineType(str, Enum):
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"
    DOCLING = "docling"


class OutputFormatType(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """
    Document categories the LLM classifier can assign. ``OTHER`` is the
    catch-all fallback whenever the classifier is unavailable, unsure, or
    returns something outside this list.
    """

    INVOICE = "invoice"
    RESUME = "resume"
    RECEIPT = "receipt"
    OTHER = "other"


# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------

class UploadResponse(BaseModel):
    file_id: str = Field(..., description="Unique id referencing the stored file")
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    page_count: int | None = Field(
        default=None, description="Number of pages, if the file is a PDF"
    )
    file_url: str = Field(..., description="URL from which the original file can be viewed")
    uploaded_at: datetime


# --------------------------------------------------------------------------
# Extraction request / response
# --------------------------------------------------------------------------

class ExtractRequest(BaseModel):
    file_id: str = Field(..., description="The id returned by /api/upload")
    ocr_engine: OCREngineType = Field(..., description="Which OCR engine to run")
    output_format: OutputFormatType = Field(..., description="Desired output format")


class PageResult(BaseModel):
    page_number: int
    text: str
    confidence: float | None = Field(
        default=None, description="Average OCR confidence (0-100) for this page, if available"
    )


class ExtractResponse(BaseModel):
    result_id: str
    file_id: str
    ocr_engine: OCREngineType
    output_format: OutputFormatType
    status: ProcessingStatus
    pages: list[PageResult]
    formatted_output: str = Field(
        ..., description="The final rendered output in the requested format"
    )
    download_url: str
    processing_time_seconds: float
    created_at: datetime

    # --- LLM classification + structured extraction (additive) ---
    document_type: DocumentType | None = Field(
        default=None,
        description="LLM-classified document type. Null if classification "
        "was unavailable/failed and the pipeline fell back to plain OCR output.",
    )
    structured_data: dict | None = Field(
        default=None,
        description="Validated, schema-typed structured data extracted by the "
        "LLM for the classified document type. Null on fallback.",
    )
    used_structured_extraction: bool = Field(
        default=False,
        description="True if formatted_output was rendered from validated "
        "structured_data rather than the raw OCR text.",
    )


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
