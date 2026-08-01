"""
app.py
------
Flask backend for the Construction Cost Estimation Chatbot MVP.

Endpoints:
    GET  /api/health   -> liveness check
    POST /api/predict  -> upload a blueprint (SVG, PNG, JPG/JPEG, or PDF),
                           get back extracted features, predicted cost,
                           cost breakdown, and SHAP explainability

Run:
    python app.py
    (defaults to http://localhost:5000)
"""

from __future__ import annotations

import logging
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

from services.explainer import Explainer
from services.extractor_router import SUPPORTED_EXTENSIONS, extract_features_for_file
from services.predictor import get_predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("construction-cost-api")

app = Flask(__name__)
CORS(app)  # MVP: allow all origins. Restrict this before deploying beyond localhost.

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload cap

ALLOWED_EXTENSIONS = SUPPORTED_EXTENSIONS

predictor = get_predictor()
explainer = Explainer(predictor.model)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model_loaded": predictor.model is not None})


@app.post("/api/predict")
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request. Attach it under the 'file' field."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return (
            jsonify(
                {
                    "error": f"Unsupported file type. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
                }
            ),
            400,
        )

    try:
        file_bytes = file.read()
        extraction = extract_features_for_file(file_bytes, file.filename)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception:  # noqa: BLE001
        logger.error("Feature extraction failed:\n%s", traceback.format_exc())
        return jsonify({"error": "Could not extract features from this blueprint file."}), 422

    try:
        df = predictor.features_to_dataframe(extraction.features)
        prediction = predictor.predict(extraction.features)
        explanation = explainer.explain(df)
    except Exception:  # noqa: BLE001
        logger.error("Prediction/explanation failed:\n%s", traceback.format_exc())
        return jsonify({"error": "Prediction failed. Please check the uploaded blueprint and try again."}), 500

    response = {
        "filename": file.filename,
        "source_format": file.filename.rsplit(".", 1)[-1].lower(),
        "predicted_cost": prediction["predicted_cost"],
        "cost_per_sqft": prediction["cost_per_sqft"],
        "prediction_confidence": prediction["prediction_confidence"],
        "features": extraction.features,
        "detected_objects": extraction.detected_objects,
        "cost_breakdown": prediction["cost_breakdown"],
        "shap_values": explanation["shap_values"],
        "feature_importance": explanation["feature_importance"],
        "shap_base_value": explanation["base_value"],
        "explanation_text": explanation["explanation_text"],
        "warnings": extraction.warnings,
    }
    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
