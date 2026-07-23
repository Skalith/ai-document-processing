"""
OCR service layer.

Exposes a single `run_ocr()` entry point that the router calls. Internally
it resolves the requested engine name to a concrete engine implementation
via a factory, so adding a new OCR engine in the future only requires:
  1. Implementing BaseOCREngine in services/engines/
  2. Registering it in the _ENGINE_REGISTRY below
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import OCREngineNotSupportedError
from app.models.schemas import OCREngineType
from app.services.engines.base import BaseOCREngine, OCRDocument
from app.services.engines.docling_engine import DoclingEngine
from app.services.engines.easyocr_engine import EasyOCREngine
from app.services.engines.paddleocr_engine import PaddleOCREngine
from app.services.engines.tesseract_engine import TesseractEngine

# Engines are instantiated once and reused across requests. Each engine
# class is responsible for its own internal lazy-loading of heavy models.
_ENGINE_REGISTRY: dict[str, BaseOCREngine] = {
    OCREngineType.TESSERACT.value: TesseractEngine(),
    OCREngineType.EASYOCR.value: EasyOCREngine(),
    OCREngineType.PADDLEOCR.value: PaddleOCREngine(),
    OCREngineType.DOCLING.value: DoclingEngine(),
}


def get_engine(engine_name: str) -> BaseOCREngine:
    engine = _ENGINE_REGISTRY.get(engine_name)
    if engine is None:
        raise OCREngineNotSupportedError(engine_name)
    return engine


async def run_ocr(file_path: Path, engine_name: str) -> OCRDocument:
    """Runs the requested OCR engine against the given file."""
    engine = get_engine(engine_name)
    return await engine.extract(file_path)
