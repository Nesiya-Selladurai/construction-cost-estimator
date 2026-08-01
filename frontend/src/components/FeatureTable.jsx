const LABELS = {
  Outdoor: "Outdoor Space",
  Doors: "Number of Doors",
  Windows: "Number of Windows",
  Refrigerator: "Refrigerator",
  Cabinet: "Cabinets",
  Sink: "Sinks",
  Dishwasher: "Dishwasher",
  Stove: "Stove / Cooktop",
  Closet: "Closets",
  Toilet: "Toilets",
  Shower: "Showers",
  Builtup_Area: "Built-up Area (sq ft)",
};

export default function FeatureTable({ features, warnings, sourceFormat }) {
  if (!features) return null;
  const entries = Object.entries(features);

  return (
    <div className="rounded-xl border border-blueprint-line bg-white shadow-card">
      <div className="flex items-center justify-between border-b border-blueprint-line px-5 py-3">
        <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-blueprint-ink">
          Extracted Features
        </h3>
        {sourceFormat && (
          <span className="rounded-full bg-blueprint-tint px-2.5 py-0.5 font-mono text-[11px] font-medium uppercase text-blueprint-ink">
            {sourceFormat}
          </span>
        )}
      </div>
      <table className="w-full text-sm">
        <tbody>
          {entries.map(([key, value], i) => (
            <tr key={key} className={i % 2 === 0 ? "bg-white" : "bg-blueprint-tint/30"}>
              <td className="px-5 py-2.5 text-blueprint-graphite/80">{LABELS[key] || key}</td>
              <td className="px-5 py-2.5 text-right font-mono font-medium text-blueprint-ink">
                {key === "Builtup_Area" ? value.toLocaleString() : value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {warnings && warnings.length > 0 && (
        <div className="border-t border-blueprint-line bg-amber-50 px-5 py-3">
          {warnings.map((w, i) => (
            <p key={i} className="flex gap-2 text-xs text-signal-warning">
              <span aria-hidden="true">&#9888;</span>
              {w}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
