"""
Layout-aware reading-order service.

Problem this solves
--------------------
Tesseract / EasyOCR / PaddleOCR all OCR a page as one flat image and return
text roughly top-to-bottom, left-to-right *in raster order*. On a
multi-column page (newsletters, research papers, forms with side-by-side
fields) that scrambles the reading order: a line from the left column gets
glued to a line from the right column just because they sit at the same
height on the page.

This module uses `layoutparser` (a Detectron2-based pretrained PubLayNet
model) to first detect the page's layout regions (text blocks, titles,
lists, tables, figures), then applies a geometric "column-by-column" sort
over those regions, so callers can OCR each region individually, in the
correct human reading order, and concatenate the results.

Design notes
------------
- This module is entirely additive/opt-in. It does not touch any existing
  OCR engine's core recognition code - it only decides HOW an image should
  be *segmented and ordered* before recognition runs.
- Detectron2 / layoutparser / torch are heavy, sometimes tricky-to-install
  dependencies. If they aren't available, or the model fails to load or
  run for any reason (no internet to fetch weights, no GPU, etc.), every
  public function here fails soft and returns None so callers can fall
  back to their original whole-page OCR behaviour with zero errors.
"""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from PIL import Image

# Standard pretrained PubLayNet layout model shipped with layoutparser's
# Detectron2 backend. Detects 5 region types: text, title, list, table, figure.
LAYOUT_MODEL_CONFIG = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config"
LAYOUT_LABEL_MAP = {0: "text", 1: "title", 2: "list", 3: "table", 4: "figure"}

# Region types we want OCR'd as "reading" text, in reading order.
_TEXT_LIKE_LABELS = {"text", "title", "list"}

_layout_model = None
_layout_unavailable = False  # sticky flag: don't retry a broken load on every page


@dataclass
class TextRegion:
    """A single detected layout region, in page-pixel coordinates."""

    x_1: float
    y_1: float
    x_2: float
    y_2: float
    label: str


def _get_layout_model():
    """Lazily imports and constructs the layoutparser Detectron2 model."""
    global _layout_model, _layout_unavailable

    if _layout_unavailable:
        return None

    if _layout_model is None:
        try:
            import layoutparser as lp

            _layout_model = lp.Detectron2LayoutModel(
                config_path=LAYOUT_MODEL_CONFIG,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.6],
                label_map=LAYOUT_LABEL_MAP,
            )
        except Exception as exc:  # noqa: BLE001 - any failure here is non-fatal
            logger.warning(
                "layoutparser layout model unavailable ({}); OCR engines will "
                "fall back to whole-page extraction without layout ordering.",
                exc,
            )
            _layout_unavailable = True
            return None

    return _layout_model


def _sort_reading_order(blocks: list, page_width: float) -> list:
    """
    Groups detected blocks into left-to-right "column bands" based on their
    actual detected horizontal extents (not a hardcoded 2-column split, so
    it generalises to single-column, 2-column, or N-column pages), then
    sorts each column top-to-bottom. Returns blocks concatenated column by
    column: entire left column first, then the next column, and so on -
    which is how a human reads a multi-column page.
    """
    if not blocks:
        return []

    # Merge horizontal spans of all blocks into a small number of column
    # "bands". A tiny tolerance (1% of page width) absorbs near-touching
    # edges so two blocks in the same visual column don't get split apart.
    tolerance = page_width * 0.01
    spans = sorted((b.block.x_1, b.block.x_2) for b in blocks)

    bands: list[list[float]] = []
    for start, end in spans:
        if bands and start <= bands[-1][1] + tolerance:
            bands[-1][1] = max(bands[-1][1], end)
        else:
            bands.append([start, end])

    columns: list[list] = [[] for _ in bands]
    for block in blocks:
        center_x = (block.block.x_1 + block.block.x_2) / 2
        # Assign to the band whose range contains this block's center;
        # default to the last band as a safe fallback.
        band_idx = len(bands) - 1
        for i, (start, end) in enumerate(bands):
            if start <= center_x <= end:
                band_idx = i
                break
        columns[band_idx].append(block)

    ordered: list = []
    for column in columns:
        column.sort(key=lambda b: b.block.y_1)
        ordered.extend(column)
    return ordered


def get_ordered_text_regions(image: Image.Image) -> list[TextRegion] | None:
    """
    Runs layout detection on `image` and returns its text-like regions
    (text/title/list blocks) in column-by-column reading order.

    Returns None (never raises) if layout detection isn't available or
    fails for any reason, so callers can cleanly fall back to their
    original whole-page OCR path.
    """
    model = _get_layout_model()
    if model is None:
        return None

    try:
        import numpy as np

        layout = model.detect(np.array(image.convert("RGB")))
        text_blocks = [b for b in layout if b.type in _TEXT_LIKE_LABELS]
        if not text_blocks:
            return None

        ordered = _sort_reading_order(text_blocks, image.width)
        return [
            TextRegion(
                x_1=max(0, b.block.x_1),
                y_1=max(0, b.block.y_1),
                x_2=min(image.width, b.block.x_2),
                y_2=min(image.height, b.block.y_2),
                label=b.type,
            )
            for b in ordered
        ]
    except Exception as exc:  # noqa: BLE001 - fail soft, never break the OCR pipeline
        logger.warning(
            "layoutparser detection failed ({}); falling back to whole-page extraction.",
            exc,
        )
        return None


def get_ordered_crops(image: Image.Image) -> list[Image.Image] | None:
    """
    Convenience wrapper: returns the page's regions already cropped out as
    individual PIL images, in reading order - ready to hand one-by-one to
    any OCR engine. Returns None if layout ordering isn't available.
    """
    regions = get_ordered_text_regions(image)
    if not regions:
        return None
    return [image.crop((r.x_1, r.y_1, r.x_2, r.y_2)) for r in regions]
