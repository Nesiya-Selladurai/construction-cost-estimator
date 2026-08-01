"""
feature_extraction.py
----------------------
Extracts the 12 model input features directly from an uploaded SVG
architectural blueprint.

DESIGN NOTE (read this before wiring in a production extractor):
This MVP extractor is intentionally simple and rule-based so the rest of
the pipeline (prediction + SHAP + UI) can be built and tested end-to-end
right now. It works by scanning every element in the SVG for an
identifying string (its `id`, `class`, `data-name`, `inkscape:label`, or
inline `<title>`/`<desc>`) and matching it against a keyword table for
each feature. Swap this module out for a real CV/vector-parsing extractor
later without touching app.py, predictor.py, or the frontend -- the only
contract that matters is the return shape of `extract_features()`.

Expected SVG authoring convention for best results:
    <rect id="door-1" .../>          -> counts toward "Doors"
    <path class="window" .../>       -> counts toward "Windows"
    <g id="builtup-area" ...>         -> its bounding box is used for
                                         Builtup_Area (in the SVG's
                                         user units, converted to sq ft
                                         via SCALE_UNITS_TO_SQFT)

If no element matches a keyword, the extractor falls back sensibly
(counts of 0, and Builtup_Area from the overall viewBox) rather than
raising -- a blueprint chatbot should never hard-fail a demo upload.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lxml import etree

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Floor-plan-editor exports (Floorplanner and similar tools) commonly use
# centimeters as the base SVG unit -- confirmed by cross-checking a real
# sample file's polygon coordinates against its own printed room dimension
# labels (a 533x289-unit room polygon labeled "5.33m x 2.89m"). 1 foot =
# 30.48 cm. This is overridable via a `data-scale` attribute on the <svg>
# root for files that use a different convention (e.g. 12 for inches).
DEFAULT_UNITS_PER_FOOT = 30.48

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

# Keyword table: model feature name -> substrings we look for (lowercased)
# in id/class/data-name/label/title/desc of every element.
FEATURE_KEYWORDS: Dict[str, List[str]] = {
    "Outdoor": ["outdoor", "patio", "balcony", "garden", "terrace", "yard"],
    "Doors": ["door"],
    "Windows": ["window"],
    "Refrigerator": ["refrigerator", "fridge"],
    "Cabinet": ["cabinet"],
    "Sink": ["sink", "basin"],
    "Dishwasher": ["dishwasher"],
    "Stove": ["stove", "range", "cooktop", "oven"],
    "Closet": ["closet", "wardrobe"],
    "Toilet": ["toilet", "wc", "water-closet", "water_closet"],
    "Shower": ["shower"],
}

BUILTUP_KEYWORDS = ["builtup", "built-up", "built_up", "floorplan", "floor-plan", "plan-outline", "footprint"]

# Model feature order -- must match model.feature_names_in_
MODEL_FEATURE_ORDER = [
    "Outdoor",
    "Doors",
    "Windows",
    "Refrigerator",
    "Cabinet",
    "Sink",
    "Dishwasher",
    "Stove",
    "Closet",
    "Toilet",
    "Shower",
    "Builtup_Area",
]


@dataclass
class ExtractionResult:
    features: Dict[str, float]
    detected_objects: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    units_per_foot: float = DEFAULT_UNITS_PER_FOOT


def _identifying_strings(el: etree._Element) -> str:
    """Collects every human-authored label on an element into one lowercase
    string we can substring-match against."""
    parts = []
    for attr in ("id", "class"):
        v = el.get(attr)
        if v:
            parts.append(v)
    for attr, val in el.attrib.items():
        if attr.endswith("}label") or attr.endswith("data-name") or "label" in attr.lower():
            parts.append(val)
    # <title> / <desc> children (common in Inkscape / Illustrator exports)
    for tag in ("title", "desc"):
        child = el.find(f"svg:{tag}", namespaces=SVG_NS)
        if child is not None and child.text:
            parts.append(child.text)
    return " ".join(parts).lower()


def _local_tag(el: etree._Element) -> str:
    return etree.QName(el).localname if el.tag is not etree.Comment else "comment"


def _parse_float(value: Optional[str], default: float = 0.0) -> float:
    if not value:
        return default
    match = re.search(r"-?\d+(\.\d+)?", value)
    return float(match.group()) if match else default


def _polygon_area(points_attr: str) -> float:
    """Shoelace formula over an SVG `points="x1,y1 x2,y2 ..."` attribute."""
    nums = [float(n) for n in _NUMBER_RE.findall(points_attr)]
    pts = list(zip(nums[0::2], nums[1::2]))
    if len(pts) < 3:
        return 0.0
    area = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _sum_of_room_polygons(root: etree._Element) -> Optional[float]:
    """Many professional floor-plan editors (Floorplanner and similar tools)
    export each room as its own group with a class like "Space Room" /
    "Space Kitchen" / "Space Bath", each containing a <polygon> of that
    room's real footprint. Summing those polygons is far more accurate
    than any bounding box (which would also cover walls, margins, and
    dimension-label text), so when this pattern is present we prefer it
    over every other Builtup_Area source. "Outdoor"-classed spaces are
    excluded since Outdoor is already tracked as a separate feature."""
    total = 0.0
    found_any = False
    for el in root.iter():
        if not isinstance(el.tag, str) or _local_tag(el) != "g":
            continue
        cls = (el.get("class") or "")
        if "Space" not in cls or "Outdoor" in cls:
            continue
        poly = el.find("svg:polygon", namespaces=SVG_NS)
        if poly is None:
            continue
        area = _polygon_area(poly.get("points", ""))
        if area > 0:
            total += area
            found_any = True
    return total if found_any else None


def _bbox_area_units(el: etree._Element) -> float:
    """Bounding-box area estimate for an explicitly builtup-tagged element.
    Handles simple primitives directly, and falls back to the union of
    every descendant shape's points for anything else (groups, polygons,
    paths) -- a tagged wrapper like <g class="Floorplan Floor-1"> has no
    width/height/r of its own, so without this recursive fallback the
    area silently came out as 0 even though a "match" was found."""
    tag = _local_tag(el)
    if tag == "rect":
        w = _parse_float(el.get("width"))
        h = _parse_float(el.get("height"))
        return w * h
    if tag == "circle":
        r = _parse_float(el.get("r"))
        return 3.14159 * r * r
    if tag == "ellipse":
        rx = _parse_float(el.get("rx"))
        ry = _parse_float(el.get("ry"))
        return 3.14159 * rx * ry

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    found_any = False
    for descendant in el.iter():
        if not isinstance(descendant.tag, str):
            continue
        for x, y in _element_points(descendant):
            found_any = True
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
    if not found_any or max_x <= min_x or max_y <= min_y:
        return 0.0
    return (max_x - min_x) * (max_y - min_y)


_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _element_points(el: etree._Element) -> List[tuple]:
    """Extracts a rough set of (x, y) points an element occupies, covering
    the common shape primitives plus a crude numeric-pair scan of path
    `d` strings (good enough for a bounding-box estimate; it does not
    resolve curves precisely, but every curve's control/end points are
    still included, so the resulting box is a safe overestimate at worst)."""
    tag = _local_tag(el)
    pts: List[tuple] = []

    if tag == "rect":
        x, y = _parse_float(el.get("x")), _parse_float(el.get("y"))
        w, h = _parse_float(el.get("width")), _parse_float(el.get("height"))
        pts = [(x, y), (x + w, y + h)]
    elif tag == "circle":
        cx, cy, r = _parse_float(el.get("cx")), _parse_float(el.get("cy")), _parse_float(el.get("r"))
        pts = [(cx - r, cy - r), (cx + r, cy + r)]
    elif tag == "ellipse":
        cx, cy = _parse_float(el.get("cx")), _parse_float(el.get("cy"))
        rx, ry = _parse_float(el.get("rx")), _parse_float(el.get("ry"))
        pts = [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    elif tag == "line":
        pts = [
            (_parse_float(el.get("x1")), _parse_float(el.get("y1"))),
            (_parse_float(el.get("x2")), _parse_float(el.get("y2"))),
        ]
    elif tag in ("polygon", "polyline"):
        raw = el.get("points", "")
        nums = [float(n) for n in _NUMBER_RE.findall(raw)]
        pts = list(zip(nums[0::2], nums[1::2]))
    elif tag == "path":
        raw = el.get("d", "")
        nums = [float(n) for n in _NUMBER_RE.findall(raw)]
        pts = list(zip(nums[0::2], nums[1::2]))

    return pts


def _geometry_bounding_box(root: etree._Element) -> Optional[tuple]:
    """Last-resort footprint fallback: unions the bounding box of every
    drawable element in the document. This covers files that have no
    `viewBox` and no `width`/`height` on the root -- common when an SVG
    is hand-authored or exported from certain design tools -- which
    otherwise made Builtup_Area silently resolve to 0."""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    found_any = False

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for x, y in _element_points(el):
            found_any = True
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)

    if not found_any or max_x <= min_x or max_y <= min_y:
        return None
    return (min_x, min_y, max_x, max_y)


def extract_features(svg_bytes: bytes) -> ExtractionResult:
    warnings: List[str] = []
    try:
        parser = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
        root = etree.fromstring(svg_bytes, parser=parser)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not parse SVG file: {exc}") from exc

    units_per_foot = _parse_float(root.get("data-scale"), DEFAULT_UNITS_PER_FOOT) or DEFAULT_UNITS_PER_FOOT

    counts: Dict[str, int] = {k: 0 for k in FEATURE_KEYWORDS}
    detected_objects: List[Dict[str, str]] = []
    builtup_area_units = 0.0
    builtup_found = False

    # Priority 1: sum of individually labeled room/space polygons -- see
    # _sum_of_room_polygons for why this beats every other source when present.
    room_polygon_sum = _sum_of_room_polygons(root)
    if room_polygon_sum:
        builtup_area_units = room_polygon_sum
        builtup_found = True

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue  # skip comments/PIs
        ident = _identifying_strings(el)
        if not ident:
            continue

        # Priority 2: an explicitly built-up/footprint-tagged element --
        # only used if we didn't already get a room-polygon sum above.
        if not room_polygon_sum and any(kw in ident for kw in BUILTUP_KEYWORDS):
            builtup_area_units += _bbox_area_units(el)
            builtup_found = True
            continue

        for feature, keywords in FEATURE_KEYWORDS.items():
            if any(kw in ident for kw in keywords):
                counts[feature] += 1
                detected_objects.append({"feature": feature, "element_id": el.get("id") or ident.strip()})
                break

    if not builtup_found:
        # Fall back through progressively less-authoritative sources:
        # explicit viewBox -> explicit width/height -> computed geometry
        # bounding box (union of every shape in the file). Only if all
        # three come up empty do we actually resolve to 0.
        vb = root.get("viewBox")
        w_attr = _parse_float(root.get("width"))
        h_attr = _parse_float(root.get("height"))

        if vb:
            parts = vb.replace(",", " ").split()
            if len(parts) == 4:
                builtup_area_units = abs(float(parts[2])) * abs(float(parts[3]))
            source = "the SVG's viewBox"
        elif w_attr > 0 and h_attr > 0:
            builtup_area_units = w_attr * h_attr
            source = "the SVG's width/height attributes"
        else:
            bbox = _geometry_bounding_box(root)
            if bbox:
                min_x, min_y, max_x, max_y = bbox
                builtup_area_units = (max_x - min_x) * (max_y - min_y)
                source = "the combined bounding box of all shapes in the file"
            else:
                builtup_area_units = 0.0
                source = None

        if source:
            warnings.append(
                "No element tagged with a built-up-area label, and no labeled room/space "
                f"polygons, were found; estimated Builtup_Area from {source} instead."
            )

    builtup_area_sqft = builtup_area_units / (units_per_foot ** 2) if units_per_foot else builtup_area_units

    if builtup_area_sqft <= 0:
        warnings.append(
            "Builtup_Area resolved to 0. This blueprint has no built-up-area tag, no viewBox, "
            "no width/height on the <svg> root, and no shapes we could measure a bounding box "
            "from. Tag the floor outline with id=\"builtup-area\" (recommended), or add a "
            "viewBox/width+height to the <svg> root, so the estimate isn't based on a 0 sq ft area."
        )

    features = {**{k: float(v) for k, v in counts.items()}, "Builtup_Area": round(builtup_area_sqft, 2)}

    if not detected_objects:
        warnings.append(
            "No labeled fixtures (doors, windows, etc.) were detected. "
            "The extractor matches element id/class/label text against known keywords -- "
            "make sure blueprint elements are tagged (e.g. id=\"door-1\")."
        )

    # Reorder to match model input exactly.
    ordered_features = {k: features[k] for k in MODEL_FEATURE_ORDER}

    return ExtractionResult(
        features=ordered_features,
        detected_objects=detected_objects,
        warnings=warnings,
        units_per_foot=units_per_foot,
    )