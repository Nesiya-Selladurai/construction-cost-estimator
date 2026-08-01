import ConfidenceBadge from "./ConfidenceBadge.jsx";

function formatINR(value) {
  return `\u20B9${Number(value).toLocaleString("en-IN")}`;
}

export default function SummaryCards({ result }) {
  const { predicted_cost, cost_per_sqft, prediction_confidence, features } = result;

  const cards = [
    { label: "Estimated Construction Cost", value: formatINR(predicted_cost), emphasis: true },
    { label: "Built-up Area", value: `${features.Builtup_Area.toLocaleString()} sq ft` },
    { label: "Cost per Sq Ft", value: cost_per_sqft ? formatINR(cost_per_sqft) : "\u2014" },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {cards.map((c) => (
        <div
          key={c.label}
          className={`rounded-xl border p-5 shadow-card ${
            c.emphasis ? "border-blueprint-ink bg-blueprint-ink text-white" : "border-blueprint-line bg-white"
          }`}
        >
          <p className={`text-xs font-medium uppercase tracking-wide ${c.emphasis ? "text-white/70" : "text-blueprint-graphite/60"}`}>
            {c.label}
          </p>
          <p className={`mt-2 font-display text-2xl font-semibold ${c.emphasis ? "text-white" : "text-blueprint-ink"}`}>
            {c.value}
          </p>
          {c.emphasis && (
            <div className="mt-3">
              <ConfidenceBadge confidence={prediction_confidence} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
