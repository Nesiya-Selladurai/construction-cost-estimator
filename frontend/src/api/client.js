import axios from "axios";

// In dev, Vite proxies /api -> http://localhost:5000 (see vite.config.js).
// In production, set VITE_API_BASE_URL to your deployed backend origin.
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

export const api = axios.create({ baseURL, timeout: 30000 });

/**
 * Uploads a blueprint SVG and returns the full prediction payload:
 * { predicted_cost, cost_per_sqft, prediction_confidence, features,
 *   detected_objects, cost_breakdown, shap_values, feature_importance,
 *   shap_base_value, explanation_text, warnings }
 */
export async function predictFromBlueprint(file, onUploadProgress) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onUploadProgress && evt.total) {
        onUploadProgress(Math.round((evt.loaded * 100) / evt.total));
      }
    },
  });
  return data;
}

export async function checkHealth() {
  const { data } = await api.get("/health");
  return data;
}
