"""
Extract router.

Orchestrates the full extraction pipeline, now asynchronously:

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
original OCR-only formatted_output - the pipeline's response shape never
changes and the existing result page never breaks, it just won't have
document_type/structured_data populated when the LLM stage is
unavailable.

Job lifecycle
-------------
Pipelines now run as background tasks so the user can watch progress and
stop a long job:

  - POST /extract              -> 202 { ExtractJobResponse }  (job created)
  - GET /extract/jobs/{id}     -> ExtractJobResponse           (poll)
  - POST /extract/jobs/{id}/cancel -> ExtractJobResponse       (stop)

The job snapshot exposes a 0-100 `progress` and a human-readable `stage`
label; cancelling sets an asyncio.Event that the pipeline honours
between pipeline stages and between OCR pages.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.config import get_settings
from app.core.exceptions import (
    AppException,
    LLMServiceError,
    SchemaValidationError,
)
from app.models.schemas import (
    DocumentType,
    ExtractJobResponse,
    ExtractRequest,
    ExtractResponse,
    JobStatus,
    OCREngineType,
    OutputFormatType,
    PageResult,
    ProcessingStatus,
)
from app.services.formatter_service import format_document
from app.services.jobs import ExtractionJob, JobCancelledError, job_manager
from app.services.llm.classifier_service import classify_document
from app.services.llm.extraction_service import extract_structured_data
from app.services.llm.structured_output_formatter import format_structured_output
from app.services.pdf.hybrid_extraction_service import extract_hybrid
from app.utils.file_utils import build_output_filename, resolve_uploaded_file

router = APIRouter(prefix="/extract", tags=["Extract"])
settings = get_settings()


def _check_cancelled(job: ExtractionJob) -> None:
    if job.check_cancelled():
        raise JobCancelledError()


async def run_extraction_job(job: ExtractionJob) -> None:
    """Executes the whole pipeline for `job`, updating progress as it goes."""
    start_time = time.perf_counter()

    # Honour a cancel that arrived before the task actually started.
    if job.check_cancelled():
        job.status = JobStatus.CANCELLED
        job.stage = "Cancelled"
        return

    job.status = JobStatus.PROCESSING
    job.update(2, "Starting extraction…")

    document_type: DocumentType | None = None
    structured_data: dict | None = None
    used_structured_extraction = False

    try:
        # Step 1: resolve the previously uploaded file.
        job.update(5, "Resolving document…")
        file_path = resolve_uploaded_file(job.file_id)
        _check_cancelled(job)

        # Steps 2-3: hybrid (PyMuPDF + OCR) text extraction. Reports
        # per-page OCR progress and honours cancellation between pages.
        ocr_document = await extract_hybrid(
            file_path,
            job.ocr_engine,
            progress=job.update,
            cancel_event=job.cancel_event,
        )
        raw_text = ocr_document.full_text
        job.update(72, "Finalizing document text…")
        _check_cancelled(job)

        # Steps 4-8: LLM classification + dynamic schema extraction. This
        # whole block is best-effort: any failure here (no API key, network
        # error, the LLM's JSON not validating against the schema) falls back
        # to the plain OCR-formatted output rather than breaking the job.
        try:
            job.update(75, "Classifying document (LLM)…")
            document_type = await classify_document(raw_text)
            _check_cancelled(job)
            job.update(80, "Extracting structured data (LLM)…")
            structured_data = await extract_structured_data(raw_text, document_type)
            _check_cancelled(job)
            formatted_output = format_structured_output(
                document_type, structured_data, OutputFormatType(job.output_format)
            )
            used_structured_extraction = True
        except (LLMServiceError, SchemaValidationError) as exc:
            logger.warning(
                "LLM classification/extraction unavailable for file_id={} ({}); "
                "falling back to plain OCR-formatted output.",
                job.file_id,
                exc.message,
            )
            _check_cancelled(job)
            document_type = None
            structured_data = None
            formatted_output = format_document(
                ocr_document, OutputFormatType(job.output_format)
            )

        job.update(92, "Writing output file…")
        _check_cancelled(job)

        result_id = uuid.uuid4().hex
        output_filename = build_output_filename(result_id, job.output_format)
        output_path = settings.output_path / output_filename

        async with aiofiles.open(output_path, "w", encoding="utf-8") as out_file:
            await out_file.write(formatted_output)

        elapsed_seconds = round(time.perf_counter() - start_time, 3)

        response = ExtractResponse(
            result_id=result_id,
            file_id=job.file_id,
            ocr_engine=OCREngineType(job.ocr_engine),
            output_format=OutputFormatType(job.output_format),
            status=ProcessingStatus.COMPLETED,
            pages=[
                PageResult(
                    page_number=p.page_number, text=p.text, confidence=p.confidence
                )
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

        job.update(100, "Completed")
        # Final guard: a cancel that arrived right at the tail wins over
        # the job being marked completed.
        _check_cancelled(job)
        job.result = response.model_dump(mode="json")
        job.status = JobStatus.COMPLETED
    except JobCancelledError:
        logger.info("Extraction job {} cancelled by user.", job.job_id)
        job.status = JobStatus.CANCELLED
        job.stage = "Cancelled"
    except AppException as exc:
        logger.warning("Extraction job {} failed: {}", job.job_id, exc.message)
        job.status = JobStatus.FAILED
        job.stage = "Failed"
        job.error = exc.message
    except Exception:  # noqa: BLE001 - never leak traces via the job snapshot
        logger.exception("Extraction job {} failed unexpectedly.", job.job_id)
        job.status = JobStatus.FAILED
        job.stage = "Failed"
        job.error = "An unexpected server error occurred."


# --------------------------------------------------------------------------
# Job endpoints
# --------------------------------------------------------------------------

@router.post(
    "",
    response_model=ExtractJobResponse,
    status_code=202,
    summary="Start OCR extraction on an uploaded file (async, returns a job id)",
)
async def extract_document(payload: ExtractRequest):
    """Validates the request, then runs the pipeline in the background."""
    resolve_uploaded_file(payload.file_id)

    job = job_manager.create(
        file_id=payload.file_id,
        ocr_engine=payload.ocr_engine.value,
        output_format=payload.output_format.value,
    )
    task = asyncio.create_task(run_extraction_job(job))
    job_manager.attach(job, task)

    return ExtractJobResponse(**job.to_response())


@router.get(
    "/jobs/{job_id}",
    response_model=ExtractJobResponse,
    summary="Get a job's current progress / stage / result",
)
async def get_job(job_id: str):
    """Returns the living snapshot of an extraction job (poll this endpoint)."""
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return ExtractJobResponse(**job.to_response())


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=ExtractJobResponse,
    summary="Request cancellation of a running extraction job",
)
async def cancel_job(job_id: str):
    """Signals the running pipeline to stop; the job stops at its next checkpoint."""
    job = job_manager.cancel(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return ExtractJobResponse(**job.to_response())


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

@router.get("/download/{output_filename}", summary="Download a previously generated output file")
async def download_output(output_filename: str):
    """Streams a previously generated formatted output file back to the client."""
    output_path = settings.output_path / output_filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail=f"Output file '{output_filename}' not found.")
    return FileResponse(path=output_path, filename=output_filename)