import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function ShapChart({ shapValues, explanationText }) {
  if (!shapValues || shapValues.length === 0) return null;

  const data = [...shapValues]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .map((s) => ({ feature: s.feature, value: s.value }));

  return (
    <div className="rounded-xl border border-blueprint-line bg-white p-5 shadow-card">
      <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-blueprint-ink">
        Explainable AI &mdash; SHAP Feature Impact
      </h3>
      <p className="mt-1 text-sm text-blueprint-graphite/70">
        Positive bars push the estimate up; negative bars pull it down, relative to a typical home.
      </p>

      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 24, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#C7D8F5" />
            <XAxis type="number" tickFormatter={(v) => `\u20B9${Math.round(v / 1000)}k`} fontSize={12} />
            <YAxis type="category" dataKey="feature" width={100} fontSize={12} />
            <Tooltip formatter={(v) => `\u20B9${Number(v).toLocaleString("en-IN")}`} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={d.value >= 0 ? "#2F6FED" : "#DC2626"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {explanationText && (
        <div className="mt-4 rounded-lg bg-blueprint-tint/50 p-4 text-sm leading-relaxed text-blueprint-graphite">
          <span className="mr-1.5 font-semibold text-blueprint-ink">AI summary:</span>
          {explanationText}
        </div>
      )}
    </div>
  );
}
