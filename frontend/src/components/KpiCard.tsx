import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  accent?: "brand" | "teal" | "violet" | "amber";
  delta?: number;
  deltaLabel?: string;
}

const ACCENTS: Record<string, string> = {
  brand: "from-brand-500/20 to-brand-500/5 text-brand-300",
  teal: "from-accent-teal/20 to-accent-teal/5 text-accent-teal",
  violet: "from-accent-violet/20 to-accent-violet/5 text-accent-violet",
  amber: "from-accent-amber/20 to-accent-amber/5 text-accent-amber",
};

export function KpiCard({ label, value, icon: Icon, accent = "brand", delta, deltaLabel }: KpiCardProps) {
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="glass-card rounded-2xl p-5 shadow-card transition-transform hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{label}</p>
        <div className={clsx("flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br", ACCENTS[accent])}>
          <Icon size={16} />
        </div>
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-white">{value}</p>
      {delta !== undefined && (
        <div className="mt-2 flex items-center gap-1 text-xs">
          <span className={clsx("flex items-center gap-0.5 font-medium", positive ? "text-accent-emerald" : "text-accent-rose")}>
            {positive ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
            {Math.abs(delta).toFixed(1)}%
          </span>
          <span className="text-gray-500">{deltaLabel}</span>
        </div>
      )}
    </div>
  );
}
