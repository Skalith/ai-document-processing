"""
Common interface that every OCR engine implementation must follow.

Using an abstract base class means the rest of the application (the
service layer, routers) never needs to know which concrete engine is
running - it just calls `.extract(path)` and gets back a normalised
`OCRDocument`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OCRPage:
    """Normalised OCR result for a single page/image."""

    page_number: int
    text: str
    confidence: float | None = None
    # Optional structured elements (used by Docling for layout-aware output).
    # Each element looks like: {"type": "heading|paragraph|table|list", "text": "..."}
    elements: list[dict] = field(default_factory=list)
    # "machine" | "scanned" | None. Set by the hybrid extraction pipeline
    # (services/pdf/hybrid_extraction_service.py) to record how each page's
    # text was obtained; None for engines/paths that don't distinguish.
    page_type: str | None = None


@dataclass
class OCRDocument:
    """Normalised OCR result for an entire document (all pages)."""

    pages: list[OCRPage]
    engine_name: str

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)


class BaseOCREngine(ABC):
    """Abstract base class all concrete OCR engines implement."""

    name: str = "base"

    @abstractmethod
    async def extract(self, file_path: Path) -> OCRDocument:
        """
        Run OCR on the given file (image or PDF) and return a normalised
        OCRDocument. Implementations are responsible for handling
        multi-page PDFs internally.
        """
        raise NotImplementedError

    async def extract_from_images(self, images: list) -> list[OCRPage]:
        """
        Optional capability: run OCR on a list of already-loaded PIL
        images (no file/PDF involved) and return one OCRPage per image,
        in order. Used by the hybrid, page-type-aware extraction pipeline
        (services/pdf/hybrid_extraction_service.py) to OCR only the
        specific pages flagged as scanned rather than a whole document.

        Not every engine needs to support this (e.g. Docling parses whole
        PDFs natively), so the default raises NotImplementedError and
        callers should catch that and fall back to whole-document OCR.
        """
        raise NotImplementedError(f"{self.name} does not support per-image OCR")
