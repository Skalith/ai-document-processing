"""
EasyOCR engine implementation.

EasyOCR uses a deep-learning (CRAFT + CRNN) pipeline and tends to perform
better than Tesseract on noisy backgrounds, handwriting-adjacent fonts,
and non-Latin scripts, at the cost of being slower and more memory-hungry.

The Reader object loads model weights on first use, so we lazily
instantiate and cache it as a module-level singleton to avoid re-loading
the model on every request.
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

_reader = None  # lazily-initialised singleton, see _get_reader()


def _get_reader():
    """Lazily imports and constructs the EasyOCR Reader (heavy import)."""
    global _reader
    if _reader is None:
        import easyocr  # deferred import: avoids the cost at app startup

        languages = [lang.strip() for lang in settings.easyocr_languages.split(",")]
        _reader = easyocr.Reader(languages, gpu=False)
    return _reader


class EasyOCREngine(BaseOCREngine):
    name = "easyocr"

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
        reader = _get_reader()
        pages: list[OCRPage] = []

        for index, image in enumerate(images, start=1):
            # Layout-aware path: OCR each detected region separately, in
            # column-by-column reading order, instead of the raw full page.
            ordered_crops = get_ordered_crops(image)

            if ordered_crops:
                region_texts: list[str] = []
                confidences: list[float] = []
                for crop in ordered_crops:
                    results = reader.readtext(np.array(crop))
                    lines = [text for (_bbox, text, _conf) in results]
                    if lines:
                        region_texts.append("\n".join(lines))
                    confidences.extend(conf for (_bbox, _text, conf) in results if conf is not None)

                text = "\n\n".join(region_texts)
                avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else None
            else:
                # Original whole-page behaviour, unchanged.
                results = reader.readtext(np.array(image))

                lines = [text for (_bbox, text, _conf) in results]
                confidences = [conf for (_bbox, _text, conf) in results if conf is not None]

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
