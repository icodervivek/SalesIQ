"use client";

import {
  Area,
  ComposedChart,
  CartesianGrid,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ChartPoint {
  date: string;
  historical?: number;
  forecast?: number;
  lower_bound?: number;
  upper_bound?: number;
}

export function ForecastChart({ points, splitDate }: { points: ChartPoint[]; splitDate: string | null }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={points} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={40} />
        <YAxis tickLine={false} axisLine={false} width={56} />
        <Tooltip
          contentStyle={{ background: "#141a29", border: "1px solid #232a3d", borderRadius: 10 }}
          labelStyle={{ color: "#9ca3af" }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "#9ca3af" }} />

        <Area dataKey="upper_bound" name="Upper bound" stroke="none" fill="#6366f1" fillOpacity={0.14} isAnimationActive={false} />
        <Area dataKey="lower_bound" name="Lower bound" stroke="none" fill="#0b0e17" fillOpacity={1} isAnimationActive={false} legendType="none" />

        {splitDate && <ReferenceLine x={splitDate} stroke="#374151" strokeDasharray="4 4" />}

        <Line type="monotone" dataKey="historical" name="Historical" stroke="#9ca3af" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line
          type="monotone"
          dataKey="forecast"
          name="Forecast"
          stroke="#2dd4bf"
          strokeWidth={2.5}
          strokeDasharray="0"
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
