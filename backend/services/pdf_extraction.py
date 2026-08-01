"""
pdf_extraction.py
------------------
Converts an uploaded PDF blueprint into an image and hands it to the same
raster feature extractor used for PNG/JPG uploads (`raster_extraction.py`),
so SVG, PNG/JPG, and PDF all end up producing the exact same
`ExtractionResult` shape that predictor.py/explainer.py already consume
unchanged.

Requires poppler to be installed on the system (pdf2image shells out to
`pdftoppm`/`pdftocairo`). See README.md for install instructions per OS.
"""

from __future__ import annotations

from typing import List

from pdf2image import convert_from_bytes

from services.feature_extraction import ExtractionResult
from services.raster_extraction import extract_features_from_image

# Render at a higher DPI than a typical screen so fine blueprint linework
# (thin door/window strokes) survives rasterization well enough for the
# contour-based heuristics in raster_extraction.py to pick it up.
PDF_RENDER_DPI = 200.0


def extract_features_from_pdf(pdf_bytes: bytes, dpi: float = PDF_RENDER_DPI) -> ExtractionResult:
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=dpi)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            f"Could not render this PDF (is poppler installed on this system?): {exc}"
        ) from exc

    if not pages:
        raise ValueError("This PDF has no renderable pages.")

    # MVP: analyze the first page only. If real submissions bundle multiple
    # sheets (floor plan, elevation, site plan, ...), a production version
    # should let the user pick a page, or score each page by "how much
    # line-art it contains" and auto-select the most plan-like one.
    page_image = pages[0]
    result = extract_features_from_image(page_image, dpi=dpi)

    extra_warnings: List[str] = []
    if len(pages) > 1:
        extra_warnings.append(
            f"This PDF has {len(pages)} pages; only page 1 was analyzed. "
            "Upload a single-page export of the floor plan for best results."
        )
    result.warnings = [*result.warnings, *extra_warnings]
    return result
