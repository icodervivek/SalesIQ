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

function ForecastTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const point: ChartPoint = payload[0]?.payload ?? {};

  return (
    <div className="rounded-lg border border-surface-border bg-surface-card px-3.5 py-2.5 text-xs shadow-card">
      <p className="mb-1.5 font-medium text-stone-600">{label}</p>
      {point.historical !== undefined && (
        <p className="text-stone-500">
          Historical: <span className="font-medium text-stone-800">{Math.round(point.historical).toLocaleString()}</span>
        </p>
      )}
      {point.forecast !== undefined && (
        <p className="text-accent-teal">
          Forecast: <span className="font-medium">{Math.round(point.forecast).toLocaleString()}</span>
        </p>
      )}
      {point.lower_bound !== undefined && point.upper_bound !== undefined && (
        <p className="text-brand-600">
          Range: <span className="font-medium">{Math.round(point.lower_bound).toLocaleString()} – {Math.round(point.upper_bound).toLocaleString()}</span>
        </p>
      )}
    </div>
  );
}

export function ForecastChart({ points, splitDate }: { points: ChartPoint[]; splitDate: string | null }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={points} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={40} />
        <YAxis tickLine={false} axisLine={false} width={56} />
        <Tooltip content={<ForecastTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12, color: "#78716c" }} />

        <Area dataKey="upper_bound" name="Upper bound" stroke="none" fill="#4f46e5" fillOpacity={0.1} isAnimationActive={false} />
        <Area dataKey="lower_bound" name="Lower bound" stroke="none" fill="#ffffff" fillOpacity={1} isAnimationActive={false} legendType="none" />

        {splitDate && <ReferenceLine x={splitDate} stroke="#d8cdb4" strokeDasharray="4 4" />}

        <Line type="monotone" dataKey="historical" name="Historical" stroke="#a39a89" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line
          type="monotone"
          dataKey="forecast"
          name="Forecast"
          stroke="#0d9488"
          strokeWidth={2.5}
          strokeDasharray="0"
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
