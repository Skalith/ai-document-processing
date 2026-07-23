"""
Shared helper that converts an input file (single image or multi-page PDF)
into a list of in-memory PIL Images, one per page.

Every pixel-based OCR engine (Tesseract, EasyOCR, PaddleOCR) needs this;
Docling is the exception since it parses PDFs natively.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pdf2image import convert_from_path

# 200 DPI is a good default balance between OCR accuracy and processing speed.
DEFAULT_PDF_DPI = 200


def load_pages_as_images(file_path: Path) -> list[Image.Image]:
    """
    Returns a list of PIL Images representing each page of the input file.
    A plain image file yields a single-element list.
    """
    if file_path.suffix.lower() == ".pdf":
        return convert_from_path(str(file_path), dpi=DEFAULT_PDF_DPI)

    with Image.open(file_path) as img:
        # Ensure the image is fully loaded into memory before the file
        # handle closes, and normalise to RGB for consistent OCR behaviour.
        return [img.convert("RGB")]
