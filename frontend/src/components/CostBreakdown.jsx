import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = [
  "#0B3D91",
  "#2F6FED",
  "#5B8DEF",
  "#8FB4F5",
  "#1E5AC4",
  "#4381E8",
  "#3A6ED6",
  "#6FA1F2",
  "#1447A0",
  "#82A6E5",
];

function formatINR(value) {
  return `\u20B9${Number(value).toLocaleString("en-IN")}`;
}

export default function CostBreakdown({ breakdown, totalCost }) {
  if (!breakdown) return null;
  const data = Object.entries(breakdown).map(([name, value]) => ({ name, value }));

  return (
    <div className="rounded-xl border border-blueprint-line bg-white p-5 shadow-card">
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-blueprint-ink">
          Cost Breakdown
        </h3>
        <p className="font-mono text-lg font-semibold text-blueprint-ink">{formatINR(totalCost)}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={1.5}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => formatINR(v)} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <ul className="space-y-2 self-center">
          {data.map((item, i) => (
            <li key={item.name} className="flex items-center justify-between gap-3 text-sm">
              <span className="flex items-center gap-2 text-blueprint-graphite/80">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                {item.name}
              </span>
              <span className="font-mono font-medium text-blueprint-ink">{formatINR(item.value)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
