"""
extractor_router.py
--------------------
Single entry point the API route calls: pick the right feature extractor
for the uploaded file's format and return the shared `ExtractionResult`.

This is the only place that needs to know "which extension maps to which
extractor." app.py, predictor.py, and explainer.py stay format-agnostic.
"""

from __future__ import annotations

from services.feature_extraction import ExtractionResult, extract_features as extract_features_svg
from services.pdf_extraction import extract_features_from_pdf
from services.raster_extraction import extract_features_from_image

SUPPORTED_EXTENSIONS = {"svg", "png", "jpg", "jpeg", "pdf"}


def extract_features_for_file(file_bytes: bytes, filename: str) -> ExtractionResult:
    """Dispatches on the file's extension. Raises ValueError for anything
    unsupported or unparsable -- callers (app.py) turn that into a 4xx."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "svg":
        return extract_features_svg(file_bytes)
    if ext in ("png", "jpg", "jpeg"):
        return extract_features_from_image(file_bytes)
    if ext == "pdf":
        return extract_features_from_pdf(file_bytes)

    raise ValueError(
        f"Unsupported file type '.{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
    )
