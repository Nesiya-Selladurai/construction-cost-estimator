"""
explainer.py
------------
Produces SHAP-based explainability for a single prediction:
  - per-feature SHAP values (signed contribution, in currency units)
  - a feature-importance ranking (by absolute contribution)
  - a short natural-language summary the chatbot/UI can show directly

We try shap.TreeExplainer first (fast, exact for tree ensembles like
HistGradientBoostingRegressor). If that's unavailable for any reason
(e.g. a future model swap to a non-tree estimator), we transparently
fall back to the model-agnostic shap.Explainer(model.predict, ...),
so this module keeps working regardless of what's inside model.pkl.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
import shap

from services.feature_extraction import MODEL_FEATURE_ORDER

# Small synthetic background reference set used only as a "typical home"
# baseline for the model-agnostic fallback explainer and for the
# TreeExplainer's expected-value baseline. Values are rough Indian
# residential mid-range defaults for a modest home.
BACKGROUND_ROW = {
    "Outdoor": 1,
    "Doors": 6,
    "Windows": 8,
    "Refrigerator": 1,
    "Cabinet": 6,
    "Sink": 2,
    "Dishwasher": 0,
    "Stove": 1,
    "Closet": 3,
    "Toilet": 2,
    "Shower": 2,
    "Builtup_Area": 1200,
}

FRIENDLY_NAMES = {
    "Outdoor": "outdoor space",
    "Doors": "number of doors",
    "Windows": "number of windows",
    "Refrigerator": "refrigerator fixtures",
    "Cabinet": "cabinets",
    "Sink": "sinks",
    "Dishwasher": "dishwashers",
    "Stove": "stove/cooktop fixtures",
    "Closet": "closets",
    "Toilet": "toilets",
    "Shower": "showers",
    "Builtup_Area": "built-up area",
}


class Explainer:
    def __init__(self, model):
        self.model = model
        self._background = pd.DataFrame([BACKGROUND_ROW], columns=MODEL_FEATURE_ORDER)
        self._tree_explainer = None
        self._fallback_explainer = None
        try:
            self._tree_explainer = shap.TreeExplainer(model)
        except Exception:
            self._tree_explainer = None

    def _get_fallback(self):
        if self._fallback_explainer is None:
            self._fallback_explainer = shap.Explainer(self.model.predict, self._background)
        return self._fallback_explainer

    def explain(self, df: pd.DataFrame) -> Dict:
        values: np.ndarray
        base_value: float

        if self._tree_explainer is not None:
            try:
                raw = self._tree_explainer.shap_values(df)
                values = np.array(raw)[0]
                base_value = float(np.atleast_1d(self._tree_explainer.expected_value)[0])
            except Exception:
                self._tree_explainer = None  # don't retry a broken explainer

        if self._tree_explainer is None:
            explanation = self._get_fallback()(df)
            values = np.array(explanation.values[0])
            base_value = float(np.atleast_1d(explanation.base_values)[0])

        shap_values: List[Dict] = []
        for feature, val in zip(MODEL_FEATURE_ORDER, values):
            shap_values.append(
                {
                    "feature": feature,
                    "value": round(float(val), 2),
                    "input_value": float(df[feature].iloc[0]),
                }
            )

        feature_importance = sorted(
            [{"feature": s["feature"], "importance": abs(s["value"])} for s in shap_values],
            key=lambda x: x["importance"],
            reverse=True,
        )

        explanation_text = self._to_natural_language(shap_values)

        return {
            "base_value": round(base_value, 2),
            "shap_values": shap_values,
            "feature_importance": feature_importance,
            "explanation_text": explanation_text,
        }

    def _to_natural_language(self, shap_values: List[Dict]) -> str:
        positive = sorted(
            [s for s in shap_values if s["value"] > 0], key=lambda x: x["value"], reverse=True
        )[:3]
        negative = sorted([s for s in shap_values if s["value"] < 0], key=lambda x: x["value"])[:2]

        if not positive and not negative:
            return "This prediction is close to the baseline estimate for a typical home of this size."

        parts = []
        if positive:
            names = ", ".join(FRIENDLY_NAMES.get(s["feature"], s["feature"]) for s in positive)
            parts.append(f"driven up mainly by the {names}")
        if negative:
            names = ", ".join(FRIENDLY_NAMES.get(s["feature"], s["feature"]) for s in negative)
            parts.append(f"brought down somewhat by the {names}")

        return "The estimated cost is " + " and ".join(parts) + " relative to a typical home."
