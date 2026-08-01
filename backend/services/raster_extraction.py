"""
raster_extraction.py
---------------------
Extracts the same 12 model input features as feature_extraction.py, but
from a raster blueprint image (PNG/JPG/JPEG) instead of a tagged SVG.
Also used by pdf_extraction.py, which rasterizes a PDF page and hands the
resulting image straight to `extract_features_from_image()` below.

CONTRACT: this returns the exact same `ExtractionResult` shape as the SVG
extractor (feature dict keyed by MODEL_FEATURE_ORDER, plus detected_objects
and warnings). predictor.py and explainer.py are format-agnostic and never
need to change -- app.py just picks which extractor to call based on the
uploaded file's extension.

DESIGN NOTE (read this before treating this as production-grade):
Reliably detecting real architectural symbols (doors, windows, toilets,
sinks, ...) in a raster image is an object-detection problem that really
wants a model trained on labeled floor-plan symbols (e.g. a YOLO detector
fine-tuned on a floor-plan dataset). Building/training that is out of
scope for this pass. Instead, this MVP uses classical OpenCV contour
analysis + geometric heuristics (size, aspect ratio, circularity, relative
to the detected building footprint) to bucket shapes into the 12 feature
categories, so the endpoint works end-to-end today without a labeled
symbol dataset. Treat the resulting counts as directional, not exact.

Swap this module out for a trained detector later without touching
predictor.py, explainer.py, or app.py -- only `extract_features_from_image()`'s
return shape is a contract.
"""

from __future__ import annotations

import io
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from services.feature_extraction import ExtractionResult, MODEL_FEATURE_ORDER

# ---------------------------------------------------------------------------
# Configuration -- tune these against your own blueprint dataset.
# ---------------------------------------------------------------------------

# MVP scale assumption: with no calibration reference on the page, we treat
# the image's embedded DPI (or this default if none is present) as if
# 1 printed inch of blueprint ≈ 1 real-world foot. This is a common
# shorthand for uncalibrated scans, not a real architectural scale
# conversion -- override by passing an explicit `dpi` to
# `extract_features_from_image()` once you know your source's true scale.
DEFAULT_DPI = 96.0

# Contours smaller than this fraction of the image area are treated as
# noise (stray pixels, dashed-line fragments, text glyphs) and dropped.
MIN_CONTOUR_AREA_FRACTION = 0.0004

# The building footprint candidate must cover at least this fraction of
# the image; the largest contour clearing this bar is treated as the
# outer wall / footprint outline.
FOOTPRINT_AREA_FRACTION_MIN = 0.12

# A contour classified as "outdoor" (patio/balcony/yard) must sit mostly
# outside the footprint's bounding box and clear this area fraction.
OUTDOOR_AREA_FRACTION_MIN = 0.02


def _load_pil_image(image: Union[bytes, np.ndarray, Image.Image]) -> Image.Image:
    if isinstance(image, Image.Image):
        return image
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(image))
    if isinstance(image, np.ndarray):
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    raise TypeError(f"Unsupported image input type: {type(image)}")


def _effective_dpi(pil_image: Image.Image, dpi_hint: Optional[float]) -> float:
    if dpi_hint:
        return float(dpi_hint)
    dpi_info = pil_image.info.get("dpi")
    if dpi_info and dpi_info[0]:
        return float(dpi_info[0])
    return DEFAULT_DPI


def _to_gray_cv2(pil_image: Image.Image) -> np.ndarray:
    rgb = np.array(pil_image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def _binarize(gray: np.ndarray) -> np.ndarray:
    # Blueprints are clean, uniformly-lit line art (vector-rendered PDFs/SVGs
    # rasterized, or flat scans) rather than photos with uneven lighting, so
    # a single global Otsu threshold is both simpler and more robust than
    # adaptive thresholding here. (Adaptive thresholding was tried first but
    # its local-window comparison fabricates a spurious second "ghost ring"
    # contour around sharp-edged filled shapes -- a phantom duplicate fixture
    # for every real one. If you later need to support photographed
    # blueprints with real lighting gradients, reintroduce adaptive
    # thresholding but pair it with stricter duplicate-contour merging.)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Close small gaps in wall/fixture outlines so contours stay connected.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)


def _contour_metrics(contour: np.ndarray) -> dict:
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    x, y, w, h = cv2.boundingRect(contour)
    circularity = (4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0.0
    aspect_ratio = max(w, h) / max(min(w, h), 1)
    return {
        "area": area,
        "perimeter": perimeter,
        "bbox": (x, y, w, h),
        "circularity": circularity,
        "aspect_ratio": aspect_ratio,
        "centroid": (x + w / 2, y + h / 2),
    }


def _classify_fixture(metrics: dict, unit: float, pixels_per_foot: float) -> Optional[str]:
    """Buckets a single fixture-candidate contour into one of the 12 model
    features using shape descriptors normalized by `unit` (a characteristic
    length derived from the footprint size, so this scales across image
    resolutions). This is the heuristic rule table referenced in the
    module docstring -- retune freely."""
    area = metrics["area"]
    size = area / (unit ** 2) if unit else 0.0
    circularity = metrics["circularity"]
    aspect_ratio = metrics["aspect_ratio"]
    _, _, w, h = metrics["bbox"]

    # Round fixtures: sinks, toilets, showers (smallest to largest).
    # NOTE: a filled square scores ~0.785 on this circularity metric
    # (4*pi*Area/Perimeter^2), so the cutoff must sit clearly above that --
    # true circles come in around 0.85+ once pixelation is accounted for.
    if circularity >= 0.83:
        if size < 1.2:
            return "Sink"
        if size < 3.0:
            return "Toilet"
        return "Shower"

    # Thin, elongated shapes read as wall openings -- doors or windows,
    # distinguished by real-world width once converted via pixels_per_foot.
    if aspect_ratio >= 3.2 and min(w, h) < 0.6 * unit:
        width_ft = max(w, h) / pixels_per_foot if pixels_per_foot else 0
        return "Doors" if width_ft >= 2.5 else "Windows"

    # Remaining rectangular blobs, bucketed by relative size.
    if size < 1.5:
        return "Dishwasher"
    if size < 2.5:
        return "Stove"
    if size < 4.0:
        return "Cabinet"
    if size < 6.0:
        return "Closet"
    if size < 10.0:
        return "Refrigerator"
    return None  # too large to be a fixture; likely a room outline or noise


def _bbox_containment(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    """Fraction of the smaller box's area that overlaps the larger box.
    Unlike IoU, this correctly flags concentric duplicates even when the
    two traced rings differ noticeably in size (a thin inner "ghost" ring
    a few pixels smaller than the true outline still scores ~1.0 here,
    where IoU would under-count it)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    smaller_area = min(aw * ah, bw * bh)
    return inter / smaller_area if smaller_area > 0 else 0.0


def _drop_duplicate_contours(
    contours: List[np.ndarray], containment_threshold: float = 0.9, size_ratio_threshold: float = 0.75
) -> List[np.ndarray]:
    """Adaptive thresholding + anti-aliasing occasionally traces a single
    solid shape twice (its true outline plus a thin ghost ring a few pixels
    in or out) -- left alone, that becomes a phantom second fixture.

    IMPORTANT: a fixture legitimately sitting inside the building footprint
    also has a bounding box "contained" by the footprint's, so containment
    alone can't distinguish a real duplicate from a real nested fixture.
    A duplicate additionally has near-equal *area* to what it's contained
    by; a fixture nested inside a much bigger room outline does not. Only
    drop when both conditions hold, largest contour wins in each cluster.
    """
    boxed = sorted(contours, key=cv2.contourArea, reverse=True)
    kept: List[np.ndarray] = []
    kept_boxes: List[Tuple[int, int, int, int]] = []
    kept_areas: List[float] = []
    for c in boxed:
        box = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        is_duplicate = any(
            _bbox_containment(box, kb) >= containment_threshold
            and (area / ka if ka > 0 else 0) >= size_ratio_threshold
            for kb, ka in zip(kept_boxes, kept_areas)
        )
        if is_duplicate:
            continue
        kept.append(c)
        kept_boxes.append(box)
        kept_areas.append(area)
    return kept


def extract_features_from_image(
    image: Union[bytes, np.ndarray, Image.Image], dpi: Optional[float] = None
) -> ExtractionResult:
    pil_image = _load_pil_image(image)
    effective_dpi = _effective_dpi(pil_image, dpi)
    pixels_per_foot = effective_dpi  # see DEFAULT_DPI note above

    gray = _to_gray_cv2(pil_image)
    img_h, img_w = gray.shape
    img_area = img_h * img_w

    binary = _binarize(gray)
    # RETR_LIST (every contour, at every nesting depth) is required here --
    # fixtures drawn inside the footprint's outer boundary are topologically
    # "nested" (they sit inside the hole enclosed by the wall outline), and
    # RETR_EXTERNAL would silently drop anything nested that deep.
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    min_area = MIN_CONTOUR_AREA_FRACTION * img_area
    candidates = [c for c in contours if cv2.contourArea(c) >= min_area]
    candidates = _drop_duplicate_contours(candidates)

    warnings: List[str] = []
    if not candidates:
        raise ValueError(
            "No usable shapes were detected in this image -- it may be blank, "
            "too low-resolution, or not a line-drawing blueprint."
        )

    metrics_list = [_contour_metrics(c) for c in candidates]

    # The largest sufficiently-large contour is treated as the building
    # footprint / outer wall outline.
    footprint_candidates = [
        m for m in metrics_list if m["area"] >= FOOTPRINT_AREA_FRACTION_MIN * img_area
    ]
    if footprint_candidates:
        footprint = max(footprint_candidates, key=lambda m: m["area"])
    else:
        footprint = max(metrics_list, key=lambda m: m["area"])
        warnings.append(
            "Could not confidently isolate a building footprint outline; "
            "used the largest detected shape instead, so Builtup_Area may be inaccurate."
        )

    fx, fy, fw, fh = footprint["bbox"]
    builtup_area_px = footprint["area"]
    builtup_area_sqft = builtup_area_px / (pixels_per_foot ** 2) if pixels_per_foot else 0.0

    # Characteristic length for normalizing fixture-size thresholds --
    # derived from the footprint so classification scales with image
    # resolution and building size rather than using fixed pixel counts.
    unit = np.sqrt(builtup_area_px) / 20.0 if builtup_area_px > 0 else 1.0

    counts = {k: 0 for k in ["Outdoor", "Doors", "Windows", "Refrigerator", "Cabinet", "Sink",
                              "Dishwasher", "Stove", "Closet", "Toilet", "Shower"]}
    detected_objects: List[dict] = []

    for idx, m in enumerate(metrics_list):
        if m is footprint:
            continue

        cx, cy = m["centroid"]
        outside_footprint = not (fx <= cx <= fx + fw and fy <= cy <= fy + fh)

        if outside_footprint and m["area"] >= OUTDOOR_AREA_FRACTION_MIN * img_area:
            counts["Outdoor"] += 1
            detected_objects.append({"feature": "Outdoor", "element_id": f"contour-{idx}"})
            continue
        if outside_footprint:
            continue  # small noise outside the footprint

        label = _classify_fixture(m, unit, pixels_per_foot)
        if label:
            counts[label] += 1
            detected_objects.append({"feature": label, "element_id": f"contour-{idx}"})

    if not detected_objects:
        warnings.append(
            "No fixtures were classified inside the detected footprint. "
            "This heuristic pipeline works best on clean, high-contrast line-art blueprints."
        )

    if builtup_area_sqft <= 0:
        warnings.append("Builtup_Area resolved to 0 -- prediction may be unreliable.")

    features = {**{k: float(v) for k, v in counts.items()}, "Builtup_Area": round(builtup_area_sqft, 2)}
    ordered_features = {k: features[k] for k in MODEL_FEATURE_ORDER}

    return ExtractionResult(
        features=ordered_features,
        detected_objects=detected_objects,
        warnings=warnings,
        units_per_foot=pixels_per_foot,
    )
