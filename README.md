# BluePrintCost &mdash; AI Construction Cost Estimator (MVP)

Upload a blueprint (SVG, PNG, JPG/JPEG, or PDF) &rarr; extract features &rarr; predict construction
cost with a trained `HistGradientBoostingRegressor` &rarr; explain the prediction with SHAP.

This is the MVP slice only, as scoped: **no auth, no database, no chatbot, no PDF *report* export
yet** (PDF *upload* of blueprints is supported). The code is structured so the rest can be added
later without reworking what's here.

```
construction-cost-estimator/
├── backend/
│   ├── app.py                     Flask app, POST /api/predict (routes by file extension)
│   ├── model.pkl                  your trained model (copied in, never modified)
│   ├── requirements.txt
│   ├── sample_data/
│   │   ├── sample_blueprint.svg   tagged demo SVG
│   │   ├── sample_blueprint.png   demo raster blueprint
│   │   └── sample_blueprint.pdf   demo single-page PDF blueprint
│   └── services/
│       ├── extractor_router.py    picks the right extractor by file extension
│       ├── feature_extraction.py  SVG -> 12 model features (also defines the
│       │                          shared ExtractionResult / MODEL_FEATURE_ORDER)
│       ├── raster_extraction.py   PNG/JPG/JPEG -> 12 model features (OpenCV)
│       ├── pdf_extraction.py      PDF -> image (pdf2image) -> raster_extraction
│       ├── predictor.py           model.pkl -> predicted cost + breakdown (format-agnostic, untouched)
│       └── explainer.py           SHAP values + natural-language summary (format-agnostic, untouched)
└── frontend/
    ├── src/
    │   ├── pages/                 Home, Predict, About
    │   ├── components/            UploadCard, FeatureTable, CostBreakdown,
    │   │                          ShapChart, SummaryCards, Notification, ...
    │   └── api/client.js          axios wrapper around /api/predict
    └── (Vite + React + Tailwind + Recharts)
```

**Architecture note:** every extractor (SVG, raster, PDF) returns the exact same
`ExtractionResult` shape -- a 12-key feature dict in `MODEL_FEATURE_ORDER`, plus
`detected_objects` and `warnings`. `predictor.py` and `explainer.py` only ever see that shape,
never the original file, so the prediction/SHAP pipeline is completely unaware of upload format
and didn't need to change to add PNG/JPG/PDF support.

## 1. Backend setup

**System dependency for PDF uploads:** PDF support uses `pdf2image`, which shells out to
**poppler**. Install it before testing PDF uploads (SVG/PNG/JPG work without it):

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Download poppler binaries and add the `bin/` folder to PATH:
# https://github.com/oschwartz10612/poppler-windows/releases
```

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                     # runs on http://localhost:5000
```

Verify it's alive:

```bash
curl http://localhost:5000/api/health
```

Test a prediction against the bundled sample blueprints (same endpoint, any supported format):

```bash
curl -F "file=@sample_data/sample_blueprint.svg" http://localhost:5000/api/predict
curl -F "file=@sample_data/sample_blueprint.png" http://localhost:5000/api/predict
curl -F "file=@sample_data/sample_blueprint.pdf" http://localhost:5000/api/predict
```

**Note on scikit-learn version:** your `model.pkl` was trained with scikit-learn 1.6.1.
`requirements.txt` pins that version to avoid `InconsistentVersionWarning` / silent
behavior drift. If you retrain on a newer scikit-learn, bump the pin to match.

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev                       # runs on http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:5000` (see `vite.config.js`), so no
`.env` is needed locally. For a production deploy where frontend and backend live on
different origins, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

## 3. API contract

`POST /api/predict` &mdash; multipart form, field name `file`. Accepts `.svg`, `.png`, `.jpg`,
`.jpeg`, or `.pdf`. The response shape is identical regardless of which format was uploaded.

```json
{
  "filename": "sample_blueprint.svg",
  "source_format": "svg",
  "predicted_cost": 3277875.17,
  "cost_per_sqft": 2731.56,
  "prediction_confidence": { "score": 97.0, "label": "High" },
  "features": {
    "Outdoor": 1, "Doors": 3, "Windows": 4, "Refrigerator": 1, "Cabinet": 1,
    "Sink": 2, "Dishwasher": 1, "Stove": 1, "Closet": 2, "Toilet": 2,
    "Shower": 1, "Builtup_Area": 1200
  },
  "detected_objects": [{ "feature": "Doors", "element_id": "door-1" }, "..."],
  "cost_breakdown": {
    "Foundation": 530360.2, "Walls": 826352.33, "Roofing": 457919.16,
    "Flooring": 357288.39, "Doors": 134065.09, "Windows": 117347.93,
    "Plumbing": 234695.86, "Electrical": 256985.41, "Painting": 206506.14,
    "Miscellaneous": 156354.65
  },
  "shap_values": [{ "feature": "Builtup_Area", "value": 812340.5, "input_value": 1200 }, "..."],
  "feature_importance": [{ "feature": "Builtup_Area", "importance": 812340.5 }, "..."],
  "shap_base_value": 1850000.0,
  "explanation_text": "The estimated cost is driven up mainly by the built-up area...",
  "warnings": []
}
```

## 4. Important assumptions to review (read before demoing)

These were made to get a working MVP end-to-end without your original SVG extraction /
SHAP code, since it wasn't provided in this pass. Swap any of them out independently &mdash;
nothing else depends on the internals of these modules.

- **`services/feature_extraction.py`** matches blueprint elements by keyword against each
  element's `id` / `class` / `<title>` / `<desc>` (e.g. `id="door-1"` &rarr; counts toward
  `Doors`). It assumes an element tagged with `builtup`/`floor-plan`/etc. marks the
  footprint; if none is found, it falls back to the SVG's overall `viewBox` area. Unit
  scale defaults to **12 SVG units = 1 ft**, overridable via a `data-scale` attribute on
  the `<svg>` root. **If your real blueprints use a different tagging/scale convention,
  update `FEATURE_KEYWORDS` / `DEFAULT_UNITS_PER_FOOT` accordingly** &mdash; this is the one
  module most likely to need replacing with your actual extraction logic.
- **`prediction_confidence`** is a heuristic 0&ndash;100 banding based on how far the inputs
  sit from typical ranges (e.g. zero built-up area lowers it a lot). `HistGradientBoostingRegressor`
  has no native prediction interval, so this is *not* a statistical confidence interval.
  For a rigorous version, consider quantile regression or bootstrapped intervals.
- **`cost_breakdown` percentages** (Foundation 16.2%, Walls 25.2%, etc.) are a fixed
  category split applied to the total predicted cost, derived from the example numbers
  in the product spec. They're not learned from data. A more accurate version would
  train a small per-category allocation model.
- **SHAP explainer** tries `shap.TreeExplainer` first (fast, exact for tree ensembles)
  and transparently falls back to the model-agnostic `shap.Explainer(model.predict, ...)`
  if that fails for any reason &mdash; so this keeps working even if you swap in a different
  model type later.
- **`services/raster_extraction.py`** (PNG/JPG/JPEG, and PDF pages via `pdf_extraction.py`)
  detects the building footprint as the largest closed contour, then classifies every other
  contour into one of the 12 features using classical shape descriptors &mdash; circularity
  (round fixtures: sink/toilet/shower, smallest to largest), aspect ratio (thin elongated
  shapes: doors/windows), and relative size (remaining rectangular blobs: dishwasher/stove/
  cabinet/closet/refrigerator, smallest to largest). **This is a genuinely different
  reliability tier than the SVG extractor**: the SVG path reads authored labels (ground
  truth), while the raster path is *guessing* object identity from geometry alone with no
  labeled floor-plan symbol dataset behind it. Treat raster/PDF feature counts as directional,
  not exact &mdash; accurate production use really wants a detector trained on labeled
  floor-plan symbols (e.g. a fine-tuned YOLO model). Swapping that in only requires matching
  `extract_features_from_image()`'s return shape; nothing downstream changes.
- **Raster/PDF scale assumption:** with no scale bar or calibration reference on the page,
  the extractor assumes the image's embedded DPI (or 96 DPI if none is present) as
  "1 printed inch &asymp; 1 real-world foot." This is a common shorthand for uncalibrated
  scans, not a true architectural scale conversion &mdash; pass an explicit `dpi` to
  `extract_features_from_image()` once you know a source's real scale. PDF pages are
  rasterized at 200 DPI before extraction (`PDF_RENDER_DPI` in `pdf_extraction.py`); only
  the first page is analyzed, with a warning surfaced if the PDF has more than one page.

## 5. Deferred by design (per MVP scope)

Auth, database-backed history, the full chatbot, and PDF report generation are not built
in this pass. The service layer (`predictor.py`, `explainer.py`, `feature_extraction.py`)
and the `/api/predict` response shape are deliberately decoupled from routing/UI, so:

- **Auth** can wrap `/api/predict` with a JWT check without touching `services/`.
- **History/DB** can persist the JSON response from `/api/predict` as-is.
- **Chatbot** can call the same `services/` functions directly, or read a stored
  prediction + ask follow-up questions against `explanation_text` / `shap_values`.
- **PDF reports** can render the same fields already returned by `/api/predict`.

Also natural next steps for the upload pipeline specifically: multi-page PDF support (currently
only page 1 is analyzed), a page/scale calibration step for raster uploads, and replacing the
OpenCV heuristic classifier with a floor-plan-symbol detector trained on labeled data.
