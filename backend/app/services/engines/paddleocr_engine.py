"""
PaddleOCR engine implementation.

PaddleOCR (from Baidu's PaddlePaddle framework) offers strong multilingual
support and a good accuracy/speed trade-off, particularly for East Asian
scripts. Like EasyOCR, its model is heavy to load, so we lazily initialise
a module-level singleton.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.core.exceptions import OCRProcessingError
from app.services.engines.base import BaseOCREngine, OCRDocument, OCRPage
from app.services.engines.image_loader import load_pages_as_images
from app.services.layout_service import get_ordered_crops

settings = get_settings()

_ocr_instance = None  # lazily-initialised singleton, see _get_ocr()


def _get_ocr():
    """Lazily imports and constructs the PaddleOCR instance (heavy import)."""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR  # deferred import

        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang=settings.paddleocr_lang,
            show_log=False,
        )
    return _ocr_instance


class PaddleOCREngine(BaseOCREngine):
    name = "paddleocr"

    async def extract(self, file_path: Path) -> OCRDocument:
        try:
            images = load_pages_as_images(file_path)
            pages = await asyncio.to_thread(self._process_all_pages, images)
            return OCRDocument(pages=pages, engine_name=self.name)
        except Exception as exc:  # noqa: BLE001
            raise OCRProcessingError(self.name, str(exc)) from exc

    async def extract_from_images(self, images: list) -> list[OCRPage]:
        """
        Runs OCR on an already-loaded list of PIL images. Used by the
        hybrid page-type-aware extraction pipeline (see
        app/services/pdf/hybrid_extraction_service.py) to OCR only the
        specific pages PyMuPDF flagged as scanned.
        """
        try:
            return await asyncio.to_thread(self._process_all_pages, images)
        except Exception as exc:  # noqa: BLE001
            raise OCRProcessingError(self.name, str(exc)) from exc

    @staticmethod
    def _process_all_pages(images) -> list[OCRPage]:
        ocr = _get_ocr()
        pages: list[OCRPage] = []

        for index, image in enumerate(images, start=1):
            # Layout-aware path: OCR each detected region separately, in
            # column-by-column reading order, instead of the raw full page.
            ordered_crops = get_ordered_crops(image)

            if ordered_crops:
                region_texts: list[str] = []
                confidences: list[float] = []
                for crop in ordered_crops:
                    result = ocr.ocr(np.array(crop), cls=True)
                    lines: list[str] = []
                    for line in result[0] or []:
                        _bbox, (text, confidence) = line
                        lines.append(text)
                        confidences.append(confidence)
                    if lines:
                        region_texts.append("\n".join(lines))

                text = "\n\n".join(region_texts)
                avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else None
            else:
                # Original whole-page behaviour, unchanged.
                result = ocr.ocr(np.array(image), cls=True)

                lines = []
                confidences = []

                # PaddleOCR returns a nested list: one entry per detected line,
                # each shaped like [bbox, (text, confidence)].
                for line in result[0] or []:
                    _bbox, (text, confidence) = line
                    lines.append(text)
                    confidences.append(confidence)

                text = "\n".join(lines)
                avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else None

            pages.append(
                OCRPage(
                    page_number=index,
                    text=text.strip(),
                    confidence=avg_confidence,
                )
            )
        return pages
