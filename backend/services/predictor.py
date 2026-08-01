"""
predictor.py
------------
Loads the trained HistGradientBoostingRegressor (model.pkl) and turns a
feature dict into a predicted construction cost + a category-wise cost
breakdown.

The 12 model features (in required order) are:
    Outdoor, Doors, Windows, Refrigerator, Cabinet, Sink, Dishwasher,
    Stove, Closet, Toilet, Shower, Builtup_Area
"""

from __future__ import annotations

import os
from typing import Dict

import joblib
import pandas as pd

from services.feature_extraction import MODEL_FEATURE_ORDER

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model.pkl")

# Category-wise cost split. These percentages are an MVP heuristic derived
# from typical Indian residential construction cost distributions (and
# match the example breakdown in the product spec, which sums to 100%).
# Swap this for a second trained sub-model per category later if needed --
# nothing else in the pipeline depends on how this dict is produced.
COST_BREAKDOWN_PERCENTAGES: Dict[str, float] = {
    "Foundation": 0.1618,
    "Walls": 0.2521,
    "Roofing": 0.1397,
    "Flooring": 0.1090,
    "Doors": 0.0409,
    "Windows": 0.0358,
    "Plumbing": 0.0716,
    "Electrical": 0.0784,
    "Painting": 0.0630,
    "Miscellaneous": 0.0477,
}


class Predictor:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model = joblib.load(model_path)

    def features_to_dataframe(self, features: Dict[str, float]) -> pd.DataFrame:
        ordered = {k: [features[k]] for k in MODEL_FEATURE_ORDER}
        return pd.DataFrame(ordered, columns=MODEL_FEATURE_ORDER)

    def predict(self, features: Dict[str, float]) -> Dict:
        df = self.features_to_dataframe(features)
        predicted_cost = float(self.model.predict(df)[0])
        predicted_cost = max(predicted_cost, 0.0)

        builtup_area = float(features.get("Builtup_Area", 0) or 0)
        cost_per_sqft = predicted_cost / builtup_area if builtup_area > 0 else None

        breakdown = {
            category: round(predicted_cost * pct, 2)
            for category, pct in COST_BREAKDOWN_PERCENTAGES.items()
        }

        confidence = self._estimate_confidence(df)

        return {
            "predicted_cost": round(predicted_cost, 2),
            "builtup_area_sqft": builtup_area,
            "cost_per_sqft": round(cost_per_sqft, 2) if cost_per_sqft is not None else None,
            "cost_breakdown": breakdown,
            "prediction_confidence": confidence,
        }

    def _estimate_confidence(self, df: pd.DataFrame) -> Dict:
        """HistGradientBoostingRegressor has no native predict_proba /
        interval. As an MVP confidence proxy we use the spread across the
        model's staged predictions (train_score_/validation behaviour isn't
        exposed per-sample either) -- so instead we report a qualitative
        confidence banding based on how far inputs sit from typical ranges
        the model was likely trained on (0 counts / very large areas widen
        the interval). This is a heuristic, not a statistical interval;
        replace with quantile regression or bootstrapped intervals for a
        production-grade confidence score.
        """
        area = float(df["Builtup_Area"].iloc[0])
        fixture_total = float(df.drop(columns=["Builtup_Area"]).sum(axis=1).iloc[0])

        score = 100.0
        if area <= 0:
            score -= 40
        elif area < 200 or area > 10000:
            score -= 15
        if fixture_total == 0:
            score -= 20
        score = max(5.0, min(score, 97.0))

        if score >= 80:
            label = "High"
        elif score >= 55:
            label = "Medium"
        else:
            label = "Low"

        return {"score": round(score, 1), "label": label}


_predictor_singleton: Predictor | None = None


def get_predictor() -> Predictor:
    global _predictor_singleton
    if _predictor_singleton is None:
        _predictor_singleton = Predictor()
    return _predictor_singleton
