"""
Docling engine implementation.

Docling (open-sourced by IBM Research) is a layout-aware document
converter: instead of returning flat text, it understands headings,
paragraphs, tables, and lists. We capture that structure in
`OCRPage.elements` so the formatter service can produce much richer
Markdown/HTML/JSON output than a plain-text OCR engine could.

Docling parses PDFs natively (no pdf2image conversion needed) and can
also OCR scanned/image-only pages internally.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.exceptions import OCRProcessingError
from app.services.engines.base import BaseOCREngine, OCRDocument, OCRPage

_converter = None  # lazily-initialised singleton, see _get_converter()


def _get_converter():
    """Lazily imports and constructs the Docling DocumentConverter (heavy import)."""
    global _converter
    if _converter is None:
        from docling.document_converter import DocumentConverter  # deferred import

        _converter = DocumentConverter()
    return _converter


# Maps Docling's internal item labels to the simplified element types
# our formatter service understands.
_LABEL_TO_ELEMENT_TYPE = {
    "title": "heading",
    "section_header": "heading",
    "text": "paragraph",
    "paragraph": "paragraph",
    "list_item": "list_item",
    "table": "table",
    "caption": "caption",
    "footnote": "footnote",
}


class DoclingEngine(BaseOCREngine):
    name = "docling"

    async def extract(self, file_path: Path) -> OCRDocument:
        try:
            pages = await asyncio.to_thread(self._process_document, file_path)
            return OCRDocument(pages=pages, engine_name=self.name)
        except Exception as exc:  # noqa: BLE001
            raise OCRProcessingError(self.name, str(exc)) from exc

    @staticmethod
    def _process_document(file_path: Path) -> list[OCRPage]:
        converter = _get_converter()
        result = converter.convert(str(file_path))
        document = result.document

        # Group extracted items by page number so we can build one
        # OCRPage per physical page, each with its own ordered elements.
        pages_map: dict[int, list[dict]] = {}

        for item, _level in document.iterate_items():
            page_no = _first_page_number(item)
            element_type = _LABEL_TO_ELEMENT_TYPE.get(getattr(item, "label", ""), "paragraph")
            text = getattr(item, "text", "") or ""

            if not text.strip():
                continue

            pages_map.setdefault(page_no, []).append({"type": element_type, "text": text.strip()})

        if not pages_map:
            # Fall back to a single empty page rather than an empty document,
            # keeping the response shape consistent for the frontend.
            pages_map[1] = []

        pages: list[OCRPage] = []
        for page_number in sorted(pages_map.keys()):
            elements = pages_map[page_number]
            full_text = "\n\n".join(el["text"] for el in elements)
            pages.append(
                OCRPage(
                    page_number=page_number,
                    text=full_text,
                    confidence=None,  # Docling does not expose a single confidence score
                    elements=elements,
                )
            )
        return pages


def _first_page_number(item) -> int:
    """
    Best-effort extraction of the 1-indexed page number an item belongs to.
    Docling attaches provenance info (`prov`) with page references; we
    default to page 1 if that information is unavailable for some item.
    """
    prov = getattr(item, "prov", None)
    if prov:
        try:
            return int(prov[0].page_no)
        except (IndexError, AttributeError, ValueError, TypeError):
            pass
    return 1
