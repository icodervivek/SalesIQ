"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryPerf, RegionPerf } from "@/lib/types";

const PALETTE = ["#818cf8", "#2dd4bf", "#a78bfa", "#fbbf24", "#fb7185", "#34d399"];

function formatCompact(value: number) {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return `${value}`;
}

export function RegionBarChart({ data }: { data: (RegionPerf | CategoryPerf)[] }) {
  const key = "region" in (data[0] || {}) ? "region" : "category";
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={formatCompact} />
        <YAxis dataKey={key} type="category" tickLine={false} axisLine={false} width={80} />
        <Tooltip
          contentStyle={{ background: "#141a29", border: "1px solid #232a3d", borderRadius: 10 }}
          formatter={(value: number) => [`₹${value.toLocaleString()}`, "Revenue"]}
        />
        <Bar dataKey="revenue" radius={[0, 6, 6, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
