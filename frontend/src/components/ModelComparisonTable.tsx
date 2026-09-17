import { clsx } from "clsx";
import { Trophy } from "lucide-react";
import type { ModelResult } from "@/lib/types";

export function ModelComparisonTable({ results, bestModel }: { results: ModelResult[]; bestModel: string }) {
  const valid = results.filter((r) => r.metrics && Object.keys(r.metrics).length > 0);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-border text-left text-[11px] uppercase tracking-wide text-stone-400">
            <th className="py-2.5 pr-4 font-medium">Model</th>
            <th className="py-2.5 px-4 font-medium">MAE</th>
            <th className="py-2.5 px-4 font-medium">RMSE</th>
            <th className="py-2.5 px-4 font-medium">MAPE</th>
            <th className="py-2.5 pl-4 font-medium">R²</th>
          </tr>
        </thead>
        <tbody>
          {valid.map((r) => {
            const isBest = r.name === bestModel;
            return (
              <tr key={r.name} className={clsx("border-b border-surface-border/60 last:border-0", isBest && "bg-brand-500/[0.05]")}>
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    {isBest && <Trophy size={14} className="text-accent-amber" />}
                    <span className={clsx("font-medium", isBest ? "text-stone-900" : "text-stone-600")}>{r.name}</span>
                  </div>
                </td>
                <td className="px-4 text-stone-600">{r.metrics.mae?.toFixed(2)}</td>
                <td className="px-4 text-stone-600">{r.metrics.rmse?.toFixed(2)}</td>
                <td className="px-4 text-stone-600">{r.metrics.mape?.toFixed(2)}%</td>
                <td className="pl-4 text-stone-600">{r.metrics.r2?.toFixed(3)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {results.length > valid.length && (
        <p className="mt-3 text-xs text-stone-400">
          {results.length - valid.length} model(s) could not be evaluated (see training run details).
        </p>
      )}
    </div>
  );
}
