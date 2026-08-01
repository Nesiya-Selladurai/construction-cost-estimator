import { useEffect, useRef, useState } from "react";
import { predictFromBlueprint } from "../api/client.js";
import UploadCard from "../components/UploadCard.jsx";
import Loader from "../components/Loader.jsx";
import SummaryCards from "../components/SummaryCards.jsx";
import FeatureTable from "../components/FeatureTable.jsx";
import CostBreakdown from "../components/CostBreakdown.jsx";
import ShapChart from "../components/ShapChart.jsx";
import Notification from "../components/Notification.jsx";

export default function Predict() {
  const [fileName, setFileName] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [notification, setNotification] = useState(null);
  const resultRef = useRef(null);

  useEffect(() => {
    if (result && !isAnalyzing && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      resultRef.current.focus({ preventScroll: true });
    }
  }, [result, isAnalyzing]);

  const handleFileReady = async (file) => {
    setFileName(file.name);
    setResult(null);
    setUploadProgress(0);
    setIsAnalyzing(false);

    try {
      const data = await predictFromBlueprint(file, (pct) => {
        setUploadProgress(pct);
        if (pct === 100) setIsAnalyzing(true);
      });
      setResult(data);
      setNotification({ type: "success", message: "Blueprint analyzed and cost estimated successfully." });
    } catch (err) {
      const message =
        err?.response?.data?.error || "Something went wrong while analyzing the blueprint. Please try again.";
      setNotification({ type: "error", message });
    } finally {
      setUploadProgress(null);
      setIsAnalyzing(false);
    }
  };

  const busy = uploadProgress !== null || isAnalyzing;

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-semibold text-blueprint-ink">Estimate Construction Cost</h1>
        <p className="mt-2 text-blueprint-graphite/70">
          Upload a blueprint as SVG, PNG, JPG/JPEG, or PDF. We&rsquo;ll extract its features and run them through
          the trained cost model.
        </p>
      </div>

      <UploadCard
        onFileReady={handleFileReady}
        uploadProgress={uploadProgress}
        fileName={fileName}
        disabled={busy}
      />

      {isAnalyzing && <Loader label="Extracting features and predicting cost..." />}

      {result && !busy && (
        <div ref={resultRef} tabIndex={-1} className="mt-8 space-y-6 outline-none">
          <SummaryCards result={result} />

          <div className="grid gap-6 lg:grid-cols-2">
            <FeatureTable
              features={result.features}
              warnings={result.warnings}
              sourceFormat={result.source_format}
            />
            <div>
              <div className="rounded-xl border border-blueprint-line bg-white p-5 shadow-card">
                <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-blueprint-ink">
                  Detected Objects
                </h3>
                {result.detected_objects.length === 0 ? (
                  <p className="mt-3 text-sm text-blueprint-graphite/60">
                    No individually labeled fixtures were detected on this blueprint.
                  </p>
                ) : (
                  <ul className="mt-3 flex flex-wrap gap-2">
                    {result.detected_objects.map((obj, i) => (
                      <li
                        key={i}
                        className="rounded-full border border-blueprint-line bg-blueprint-tint/40 px-3 py-1 font-mono text-xs text-blueprint-ink"
                      >
                        {obj.element_id}
                        <span className="ml-1.5 text-blueprint-graphite/50">&middot; {obj.feature}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>

          <CostBreakdown breakdown={result.cost_breakdown} totalCost={result.predicted_cost} />

          <ShapChart shapValues={result.shap_values} explanationText={result.explanation_text} />
        </div>
      )}

      <Notification notification={notification} onDismiss={() => setNotification(null)} />
    </div>
  );
}
