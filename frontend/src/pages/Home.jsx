import { Link } from "react-router-dom";

const STEPS = [
  {
    n: "01",
    title: "Upload your blueprint",
    body: "Drop in a floor plan as SVG, PNG, JPG, or PDF. We read the doors, windows, fixtures, and footprint straight off the drawing.",
  },
  {
    n: "02",
    title: "AI extracts & predicts",
    body: "A trained HistGradientBoosting model turns those features into a construction cost estimate in ₹.",
  },
  {
    n: "03",
    title: "See why, not just what",
    body: "SHAP explainability shows exactly which features pushed your estimate up or down.",
  },
];

export default function Home() {
  return (
    <div>
      <section className="relative overflow-hidden border-b border-blueprint-line bg-grid">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-blueprint-line bg-white px-3 py-1 text-xs font-medium text-blueprint-ink shadow-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-blueprint-accent" />
              Blueprint-to-cost, explained by AI
            </span>
            <h1 className="mt-5 font-display text-4xl font-semibold leading-tight tracking-tight text-blueprint-ink sm:text-5xl">
              Turn a floor plan into a construction cost estimate&mdash; and understand every rupee of it.
            </h1>
            <p className="mt-5 text-lg leading-relaxed text-blueprint-graphite/75">
              Upload an SVG blueprint and get an instant, explainable construction cost estimate: extracted
              features, a category-wise cost breakdown, and SHAP-powered reasoning behind the number.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/predict"
                className="rounded-lg bg-blueprint-ink px-6 py-3 text-sm font-semibold text-white shadow-card transition-transform hover:-translate-y-0.5"
              >
                Estimate my construction cost
              </Link>
              <Link
                to="/about"
                className="rounded-lg border border-blueprint-line bg-white px-6 py-3 text-sm font-semibold text-blueprint-ink transition-colors hover:bg-blueprint-tint"
              >
                How it works
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <h2 className="font-display text-2xl font-semibold text-blueprint-ink">From sheet to estimate in three steps</h2>
        <div className="mt-8 grid gap-6 sm:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-xl border border-blueprint-line bg-white p-6 shadow-card">
              <span className="font-mono text-sm text-blueprint-accent">{s.n}</span>
              <h3 className="mt-2 font-display text-lg font-semibold text-blueprint-ink">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-blueprint-graphite/70">{s.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
