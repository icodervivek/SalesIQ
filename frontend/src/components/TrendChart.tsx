"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TrendPoint } from "@/lib/types";

function formatCompact(value: number) {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return `${value}`;
}

export function TrendChart({ data, metric }: { data: TrendPoint[]; metric: "revenue" | "units_sold" }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={40} />
        <YAxis tickLine={false} axisLine={false} tickFormatter={formatCompact} width={56} />
        <Tooltip
          contentStyle={{ background: "#141a29", border: "1px solid #232a3d", borderRadius: 10 }}
          labelStyle={{ color: "#9ca3af" }}
          formatter={(value: number) => [metric === "revenue" ? `₹${formatCompact(value)}` : formatCompact(value), metric === "revenue" ? "Revenue" : "Units Sold"]}
        />
        <Area type="monotone" dataKey={metric} stroke="#818cf8" strokeWidth={2} fill="url(#trendFill)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
