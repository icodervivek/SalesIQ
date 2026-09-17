"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryPerf, RegionPerf } from "@/lib/types";

const PALETTE = ["#4f46e5", "#0d9488", "#7c3aed", "#b45309", "#e11d48", "#059669"];

function formatCompact(value: number) {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return `${value}`;
}

function BarTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-surface-border bg-surface-card px-3.5 py-2.5 text-xs shadow-card">
      <p className="mb-1 font-medium text-stone-800">{label}</p>
      <p className="text-stone-500">
        Revenue: <span className="font-medium text-stone-900">₹{Number(payload[0].value).toLocaleString()}</span>
      </p>
    </div>
  );
}

export function RegionBarChart({ data }: { data: (RegionPerf | CategoryPerf)[] }) {
  const key = "region" in (data[0] || {}) ? "region" : "category";
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={formatCompact} />
        <YAxis dataKey={key} type="category" tickLine={false} axisLine={false} width={80} />
        <Tooltip content={<BarTooltip />} cursor={{ fill: "rgba(24,20,14,0.035)" }} />
        <Bar dataKey="revenue" radius={[0, 6, 6, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
