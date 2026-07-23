"""
Tesseract OCR engine implementation.

Tesseract is fast and lightweight, making it a good default choice for
clean, high-contrast scanned documents. It runs synchronously under the
hood (pytesseract shells out to the tesseract binary), so we offload the
blocking work to a thread via asyncio.to_thread to avoid stalling the
FastAPI event loop.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytesseract
from pytesseract import Output

from app.config import get_settings
from app.core.exceptions import OCRProcessingError
from app.services.engines.base import BaseOCREngine, OCRDocument, OCRPage
from app.services.engines.image_loader import load_pages_as_images
from app.services.layout_service import get_ordered_crops

settings = get_settings()

if settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


class TesseractEngine(BaseOCREngine):
    name = "tesseract"

    async def extract(self, file_path: Path) -> OCRDocument:
        try:
            images = load_pages_as_images(file_path)
            pages = await asyncio.to_thread(self._process_all_pages, images)
            return OCRDocument(pages=pages, engine_name=self.name)
        except Exception as exc:  # noqa: BLE001 - surfaced as a clean API error
            raise OCRProcessingError(self.name, str(exc)) from exc

    async def extract_from_images(self, images: list) -> list[OCRPage]:
        """
        Runs OCR on an already-loaded list of PIL images (no file/PDF
        involved). Used by the hybrid page-type-aware extraction pipeline
        to OCR only the specific pages PyMuPDF flagged as scanned, instead
        of re-running OCR over an entire document that may be mostly
        machine-readable text.
        """
        try:
            return await asyncio.to_thread(self._process_all_pages, images)
        except Exception as exc:  # noqa: BLE001
            raise OCRProcessingError(self.name, str(exc)) from exc

    @staticmethod
    def _process_all_pages(images) -> list[OCRPage]:
        pages: list[OCRPage] = []
        for index, image in enumerate(images, start=1):
            # Layout-aware path: if layoutparser can detect column/text
            # regions on this page, OCR each region separately and
            # concatenate them in column-by-column reading order instead
            # of running OCR on the raw, unordered full page.
            ordered_crops = get_ordered_crops(image)

            if ordered_crops:
                texts: list[str] = []
                confidences: list[int] = []
                for crop in ordered_crops:
                    crop_data = pytesseract.image_to_data(crop, output_type=Output.DICT)
                    crop_text = pytesseract.image_to_string(crop).strip()
                    if crop_text:
                        texts.append(crop_text)
                    confidences.extend(
                        int(c) for c in crop_data.get("conf", []) if str(c).isdigit() and int(c) >= 0
                    )

                text = "\n\n".join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else None
            else:
                # Original whole-page behaviour, unchanged - used whenever
                # layout detection is unavailable or finds nothing useful.
                data = pytesseract.image_to_data(image, output_type=Output.DICT)
                text = pytesseract.image_to_string(image).strip()

                confidences = [
                    int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0
                ]
                avg_confidence = sum(confidences) / len(confidences) if confidences else None

            pages.append(
                OCRPage(page_number=index, text=text.strip(), confidence=avg_confidence)
            )
        return pages
