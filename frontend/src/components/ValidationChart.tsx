"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ModelResult } from "@/lib/types";

export function ValidationChart({ result }: { result: ModelResult }) {
  const data = result.dates.map((date, i) => ({
    date,
    actual: result.actuals[i],
    predicted: result.predictions[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={30} />
        <YAxis tickLine={false} axisLine={false} width={40} />
        <Tooltip contentStyle={{ background: "#141a29", border: "1px solid #232a3d", borderRadius: 10 }} />
        <Legend wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
        <Line type="monotone" dataKey="actual" name="Actual" stroke="#9ca3af" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="predicted" name="Predicted" stroke="#818cf8" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
