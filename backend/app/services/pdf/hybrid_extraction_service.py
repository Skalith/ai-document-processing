"""
Hybrid extraction orchestrator - Steps 2 and 3 of the pipeline.

For a PDF, this decides per-page whether to pull text directly (machine-
readable pages, via PyMuPDF) or run the user's selected OCR engine
(scanned pages, via pdf2image + the engine registry), then merges both
into one OCRDocument the rest of the pipeline (formatter, classifier,
LLM extraction) already knows how to consume.

Design notes
------------
- Entirely additive and fail-soft, matching layout_service.py's pattern:
  if the input isn't a PDF, PyMuPDF can't open it, or the selected engine
  doesn't support per-image OCR (e.g. Docling, which parses PDFs
  natively), this falls back to the original whole-document
  `ocr_service.run_ocr()` behaviour untouched.
- Docling is intentionally excluded from the per-page hybrid path: it
  already parses native PDF text and OCRs scanned regions internally in
  one pass, so re-deriving that here would duplicate work for no benefit.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.services.engines.base import OCRDocument, OCRPage
from app.services.engines.docling_engine import DoclingEngine
from app.services.ocr_service import get_engine, run_ocr
from app.services.pdf.page_detector import classify_pdf_pages
from app.utils.file_utils import is_pdf


async def extract_hybrid(file_path: Path, engine_name: str) -> OCRDocument:
    """
    Returns a normalised OCRDocument for `file_path`, using PyMuPDF for
    machine-readable pages and the selected OCR engine only for scanned
    pages. Falls back to the original whole-document OCR path whenever
    the hybrid approach isn't applicable or fails for any reason.
    """
    engine = get_engine(engine_name)

    if not is_pdf(file_path) or isinstance(engine, DoclingEngine):
        # Non-PDF images have exactly one "page" with no native text layer
        # to speak of, and Docling already does its own hybrid handling.
        return await run_ocr(file_path, engine_name)

    try:
        classifications = classify_pdf_pages(file_path)
    except Exception as exc:  # noqa: BLE001 - fail soft, exactly like layout_service
        logger.warning(
            "Page-type detection failed for '{}' ({}); falling back to "
            "whole-document OCR.",
            file_path.name,
            exc,
        )
        return await run_ocr(file_path, engine_name)

    scanned_page_numbers = [c.page_number for c in classifications if not c.is_machine_readable]

    if scanned_page_numbers:
        try:
            scanned_pages = await _ocr_scanned_pages(file_path, engine, scanned_page_numbers)
        except NotImplementedError:
            # Selected engine can't OCR individual images (shouldn't happen
            # for tesseract/easyocr/paddleocr, but guards future engines) -
            # fall back to the original whole-document behaviour.
            logger.warning(
                "Engine '{}' does not support per-image OCR; falling back "
                "to whole-document OCR for '{}'.",
                engine_name,
                file_path.name,
            )
            return await run_ocr(file_path, engine_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Hybrid OCR of scanned pages failed for '{}' ({}); falling "
                "back to whole-document OCR.",
                file_path.name,
                exc,
            )
            return await run_ocr(file_path, engine_name)
    else:
        scanned_pages = {}

    pages: list[OCRPage] = []
    for classification in classifications:
        if classification.is_machine_readable:
            pages.append(
                OCRPage(
                    page_number=classification.page_number,
                    text=classification.native_text,
                    confidence=None,  # native text has no OCR confidence score
                    page_type="machine",
                )
            )
        else:
            ocr_page = scanned_pages[classification.page_number]
            ocr_page.page_type = "scanned"
            pages.append(ocr_page)

    return OCRDocument(pages=pages, engine_name=engine_name)


async def _ocr_scanned_pages(
    file_path: Path, engine, scanned_page_numbers: list[int]
) -> dict[int, OCRPage]:
    """
    Rasterizes only the given (1-indexed) scanned pages and OCRs them via
    the selected engine, returning a {page_number: OCRPage} map with
    page_number re-stamped to match the original document (since we only
    rasterize a subset of pages).
    """
    from pdf2image import convert_from_path

    images = []
    for page_number in scanned_page_numbers:
        rasterized = convert_from_path(
            str(file_path), dpi=200, first_page=page_number, last_page=page_number
        )
        images.append(rasterized[0])

    ocr_pages = await engine.extract_from_images(images)

    result: dict[int, OCRPage] = {}
    for page_number, ocr_page in zip(scanned_page_numbers, ocr_pages):
        ocr_page.page_number = page_number
        result[page_number] = ocr_page
    return result
