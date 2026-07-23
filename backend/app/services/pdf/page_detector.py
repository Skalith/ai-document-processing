"""
Page-type detection - Step 2 of the pipeline.

For each page of a PDF, decides whether it's "machine-readable" (has real,
selectable text embedded - e.g. a native PDF export) or "scanned"
(image-only, e.g. a photographed/scanned page with no text layer).

Uses PyMuPDF (`fitz`), which is fast and dependency-light compared to
running OCR just to find out a page didn't need it. This module is
additive and fails soft: if PyMuPDF can't open the file for any reason
(not a PDF, corrupt file, etc.), callers should catch the exception and
fall back to treating the whole document as scanned (i.e. run OCR on
every page, exactly like the original pipeline did).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings

settings = get_settings()


@dataclass
class PageClassification:
    page_number: int  # 1-indexed
    is_machine_readable: bool
    native_text: str  # only populated when is_machine_readable is True


def classify_pdf_pages(file_path: Path) -> list[PageClassification]:
    """
    Opens `file_path` with PyMuPDF and classifies every page.

    Raises whatever PyMuPDF raises on an unreadable/non-PDF file - the
    caller (hybrid_extraction_service) is responsible for the fallback.
    """
    import fitz  # PyMuPDF - imported lazily to keep it optional at app startup

    classifications: list[PageClassification] = []
    with fitz.open(str(file_path)) as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            is_machine_readable = len(text) >= settings.min_native_text_chars
            classifications.append(
                PageClassification(
                    page_number=index,
                    is_machine_readable=is_machine_readable,
                    native_text=text if is_machine_readable else "",
                )
            )
    return classifications
