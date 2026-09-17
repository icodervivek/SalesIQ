"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { LayoutDashboard, UploadCloud, TrendingUp, Sparkles } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/upload", label: "Upload Data", icon: UploadCloud },
  { href: "/forecast", label: "Forecasting", icon: TrendingUp },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex lg:w-64 lg:flex-col border-r border-surface-border bg-white/85 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-6 h-16 border-b border-surface-border">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient shadow-glow">
          <Sparkles className="text-white" size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight text-stone-900">SalesIQ</p>
          <p className="text-[10px] uppercase tracking-widest text-stone-400">Analytics &amp; Forecasting</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-6 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-brand-500/10 text-brand-700 shadow-[inset_0_0_0_1px_rgba(79,70,229,0.18)]"
                  : "text-stone-500 hover:bg-stone-900/[0.04] hover:text-stone-800"
              )}
            >
              <Icon size={17} className={clsx(active ? "text-brand-600" : "text-stone-400 group-hover:text-stone-600")} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 pb-5">
        <div className="glass-card rounded-2xl p-4">
          <p className="text-xs font-semibold text-stone-800">Model coverage</p>
          <p className="mt-1 text-[11px] leading-relaxed text-stone-500">
            Baseline · SARIMA · XGBoost — evaluated with chronological validation on every training run.
          </p>
        </div>
      </div>
    </aside>
  );
}
