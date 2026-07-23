"""
Upload router.

Handles receiving the original file from the frontend, validating it,
persisting it to disk, and returning metadata (including a URL the
frontend can use to render the original document alongside the OCR
output on the results page).
"""

from __future__ import annotations

import mimetypes
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.config import get_settings
from app.models.schemas import UploadResponse
from app.utils.file_utils import is_pdf, resolve_uploaded_file, save_upload_file

router = APIRouter(prefix="/upload", tags=["Upload"])
settings = get_settings()


@router.post("", response_model=UploadResponse, summary="Upload a document for OCR processing")
async def upload_file(file: UploadFile = File(..., description="PDF or image file to process")):
    """
    Accepts a single PDF or image file via multipart/form-data, validates
    its type and size, stores it under a generated unique id, and returns
    metadata the frontend needs to move on to the extraction step.
    """
    file_id, stored_filename, destination, size_bytes = await save_upload_file(file)

    page_count = None
    if is_pdf(destination):
        page_count = _count_pdf_pages(destination)

    return UploadResponse(
        file_id=file_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        page_count=page_count,
        file_url=f"{settings.api_prefix}/upload/file/{file_id}",
        uploaded_at=datetime.now(timezone.utc),
    )


@router.get("/file/{file_id}", summary="Serve the original uploaded file")
async def get_original_file(file_id: str):
    """
    Streams the originally uploaded file back to the client. Used by the
    results page to render the source document next to the OCR output.

    NOTE: FileResponse defaults `content_disposition_type` to "attachment",
    which tells the browser to download the file instead of rendering it.
    That's exactly why the PDF split-screen viewer previously only ever
    showed the file name: the <iframe> would hit a forced download instead
    of an inline-renderable response. Setting an explicit media_type +
    `content_disposition_type="inline"` lets the browser's native PDF
    viewer render the file directly inside the iframe on the frontend.
    """
    file_path = resolve_uploaded_file(file_id)
    media_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type or "application/octet-stream",
        content_disposition_type="inline",
    )


def _count_pdf_pages(pdf_path) -> int | None:
    """Best-effort page count using pypdf-free lightweight parsing via pdf2image info."""
    try:
        from pdf2image.pdf2image import pdfinfo_from_path

        info = pdfinfo_from_path(str(pdf_path))
        return int(info.get("Pages", 0)) or None
    except Exception:  # noqa: BLE001 - page count is a nice-to-have, never fatal
        return None
