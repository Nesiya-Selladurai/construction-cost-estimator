const STYLES = {
  High: "bg-green-50 text-signal-success border-signal-success/30",
  Medium: "bg-amber-50 text-signal-warning border-signal-warning/30",
  Low: "bg-red-50 text-signal-error border-signal-error/30",
};

export default function ConfidenceBadge({ confidence }) {
  if (!confidence) return null;
  const style = STYLES[confidence.label] || STYLES.Medium;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${style}`}
      title="Heuristic confidence banding, not a statistical prediction interval"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {confidence.label} confidence &middot; {confidence.score}%
    </span>
  );
}
