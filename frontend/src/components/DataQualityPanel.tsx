import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { CleaningSummary, ValidationReport } from "@/lib/types";

function Stat({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className="rounded-xl border border-surface-border bg-stone-900/[0.015] px-3.5 py-3">
      <p className="text-[11px] uppercase tracking-wide text-stone-400">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${warn && value > 0 ? "text-accent-amber" : "text-stone-800"}`}>{value.toLocaleString()}</p>
    </div>
  );
}

export function DataQualityPanel({ validation, cleaning }: { validation: ValidationReport; cleaning: CleaningSummary }) {
  const totalIssues =
    validation.invalid_date_rows + validation.duplicate_rows + validation.missing_value_rows + validation.negative_value_rows;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {totalIssues === 0 ? (
          <CheckCircle2 size={16} className="text-accent-emerald" />
        ) : (
          <AlertTriangle size={16} className="text-accent-amber" />
        )}
        <p className="text-sm text-stone-600">
          {totalIssues === 0
            ? "No data-quality issues detected in the source file."
            : `${totalIssues.toLocaleString()} data-quality issue(s) detected and handled automatically.`}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <Stat label="Invalid dates" value={validation.invalid_date_rows} warn />
        <Stat label="Duplicates" value={validation.duplicate_rows} warn />
        <Stat label="Missing values" value={validation.missing_value_rows} warn />
        <Stat label="Negative values" value={validation.negative_value_rows} warn />
      </div>

      <div className="rounded-xl border border-surface-border bg-stone-900/[0.015] p-4">
        <p className="mb-3 text-xs font-medium text-stone-500">Cleaning pipeline result</p>
        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-stone-400">Input rows </span>
            <span className="font-medium text-stone-700">{cleaning.input_rows.toLocaleString()}</span>
          </div>
          <span className="text-stone-300">→</span>
          <div>
            <span className="text-stone-400">Clean rows </span>
            <span className="font-medium text-accent-emerald">{cleaning.output_rows.toLocaleString()}</span>
          </div>
        </div>
        <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-stone-400">
          <li>Dropped invalid dates: <span className="text-stone-700">{cleaning.dropped_invalid_dates}</span></li>
          <li>Dropped duplicates: <span className="text-stone-700">{cleaning.dropped_duplicates}</span></li>
          <li>Dropped negative values: <span className="text-stone-700">{cleaning.dropped_negative_values}</span></li>
          <li>Dropped missing required: <span className="text-stone-700">{cleaning.dropped_missing_required}</span></li>
          <li>Imputed unit price: <span className="text-stone-700">{cleaning.imputed_unit_price}</span></li>
          <li>Clipped outliers: <span className="text-stone-700">{cleaning.clipped_outliers}</span></li>
        </ul>
      </div>

      {validation.warnings.length > 0 && (
        <div className="rounded-xl border border-accent-amber/20 bg-accent-amber/[0.06] p-3.5">
          <p className="mb-1.5 text-xs font-medium text-accent-amber">Warnings</p>
          <ul className="space-y-1 text-xs text-stone-500">
            {validation.warnings.map((w, i) => (
              <li key={i}>• {w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
