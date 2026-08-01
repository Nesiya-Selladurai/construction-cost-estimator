const STACK = [
  { group: "Frontend", items: ["React.js (Vite)", "Tailwind CSS", "Axios", "React Router", "Recharts"] },
  { group: "Backend", items: ["Python", "Flask", "Flask-CORS", "Pandas / NumPy"] },
  { group: "Machine Learning", items: ["HistGradientBoostingRegressor (scikit-learn)", "SHAP", "lxml (SVG parsing)"] },
];

export default function About() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="font-display text-3xl font-semibold text-blueprint-ink">About this project</h1>
      <p className="mt-4 leading-relaxed text-blueprint-graphite/80">
        BluePrintCost is an AI-powered construction cost estimator. It reads a labeled SVG blueprint, extracts
        structural and fixture features (doors, windows, toilets, closets, built-up area, and more), and feeds
        them into a trained regression model to produce an instant, explainable cost estimate.
      </p>
      <p className="mt-4 leading-relaxed text-blueprint-graphite/80">
        Every prediction ships with a SHAP explanation, so instead of a single opaque number, you see exactly
        which features pushed the estimate up or down &mdash; and by how much.
      </p>

      <h2 className="mt-10 font-display text-xl font-semibold text-blueprint-ink">Current scope (MVP)</h2>
      <p className="mt-3 leading-relaxed text-blueprint-graphite/80">
        This build focuses on the core estimation loop: upload &rarr; extract &rarr; predict &rarr; explain.
        Authentication, saved history, the full chatbot, and PDF reports are intentionally out of scope for this
        pass and are designed to slot into the same architecture later.
      </p>

      <h2 className="mt-10 font-display text-xl font-semibold text-blueprint-ink">Tech stack</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {STACK.map((s) => (
          <div key={s.group} className="rounded-xl border border-blueprint-line bg-white p-4 shadow-card">
            <p className="font-display text-sm font-semibold text-blueprint-ink">{s.group}</p>
            <ul className="mt-2 space-y-1">
              {s.items.map((item) => (
                <li key={item} className="text-sm text-blueprint-graphite/70">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
