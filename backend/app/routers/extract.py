"""
Extract router.

This is the core "Extract Action" endpoint: given a previously uploaded
file_id plus the user's chosen OCR engine and output format, it now runs
the full pipeline:

  1. Resolve the stored file from file_id
  2/3. Hybrid text extraction: PyMuPDF for machine-readable PDF pages,
       the selected OCR engine for scanned pages (services/pdf)
  4. LLM document classification (services/llm/classifier_service.py)
  5. Dynamic schema selection based on the classified type
     (services/llm/schema_selector.py)
  6/7. LLM structured extraction + Pydantic validation
       (services/llm/extraction_service.py)
  8. Convert the validated structured data into the requested output
     format (services/llm/structured_output_formatter.py)

Every LLM-dependent step is wrapped so that any failure (no API key
configured, network error, validation failure) falls back to the
original OCR-only formatted_output - the endpoint's response shape never
changes and the existing result page never breaks, it just won't have
document_type/structured_data populated when the LLM stage is
unavailable.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.config import get_settings
from app.core.exceptions import LLMServiceError, SchemaValidationError
from app.models.schemas import (
    DocumentType,
    ExtractRequest,
    ExtractResponse,
    PageResult,
    ProcessingStatus,
)
from app.services.formatter_service import format_document
from app.services.llm.classifier_service import classify_document
from app.services.llm.extraction_service import extract_structured_data
from app.services.llm.structured_output_formatter import format_structured_output
from app.services.pdf.hybrid_extraction_service import extract_hybrid
from app.utils.file_utils import build_output_filename, resolve_uploaded_file

router = APIRouter(prefix="/extract", tags=["Extract"])
settings = get_settings()


@router.post("", response_model=ExtractResponse, summary="Run OCR extraction on an uploaded file")
async def extract_document(payload: ExtractRequest):
    start_time = time.perf_counter()

    file_path = resolve_uploaded_file(payload.file_id)

    # Steps 2-3: hybrid (PyMuPDF + OCR) text extraction, in place of the
    # old whole-document-only OCR call. Falls back internally to
    # whole-document OCR when hybrid extraction isn't applicable.
    ocr_document = await extract_hybrid(file_path, payload.ocr_engine.value)
    raw_text = ocr_document.full_text

    # Steps 4-8: LLM classification + dynamic schema extraction. This
    # whole block is best-effort: any failure here (no API key, network
    # error, the LLM's JSON not validating against the schema) falls back
    # to the plain OCR-formatted output rather than breaking the request.
    document_type: DocumentType | None = None
    structured_data: dict | None = None
    used_structured_extraction = False
    formatted_output: str

    try:
        document_type = await classify_document(raw_text)
        structured_data = await extract_structured_data(raw_text, document_type)
        formatted_output = format_structured_output(
            document_type, structured_data, payload.output_format
        )
        used_structured_extraction = True
    except (LLMServiceError, SchemaValidationError) as exc:
        logger.warning(
            "LLM classification/extraction unavailable for file_id={} ({}); "
            "falling back to plain OCR-formatted output.",
            payload.file_id,
            exc.message,
        )
        document_type = None
        structured_data = None
        formatted_output = format_document(ocr_document, payload.output_format)

    result_id = uuid.uuid4().hex
    output_filename = build_output_filename(result_id, payload.output_format.value)
    output_path = settings.output_path / output_filename

    async with aiofiles.open(output_path, "w", encoding="utf-8") as out_file:
        await out_file.write(formatted_output)

    elapsed_seconds = round(time.perf_counter() - start_time, 3)

    return ExtractResponse(
        result_id=result_id,
        file_id=payload.file_id,
        ocr_engine=payload.ocr_engine,
        output_format=payload.output_format,
        status=ProcessingStatus.COMPLETED,
        pages=[
            PageResult(page_number=p.page_number, text=p.text, confidence=p.confidence)
            for p in ocr_document.pages
        ],
        formatted_output=formatted_output,
        download_url=f"{settings.api_prefix}/extract/download/{output_filename}",
        processing_time_seconds=elapsed_seconds,
        created_at=datetime.now(timezone.utc),
        document_type=document_type,
        structured_data=structured_data,
        used_structured_extraction=used_structured_extraction,
    )


@router.get("/download/{output_filename}", summary="Download a previously generated output file")
async def download_output(output_filename: str):
    """Streams a previously generated formatted output file back to the client."""
    output_path = settings.output_path / output_filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail=f"Output file '{output_filename}' not found.")
    return FileResponse(path=output_path, filename=output_filename)
