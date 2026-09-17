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
    <aside className="hidden lg:flex lg:w-64 lg:flex-col border-r border-surface-border bg-[#0d1120]/80 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-6 h-16 border-b border-surface-border">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient shadow-glow">
          <Sparkles className="text-white" size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight text-white">SalesIQ</p>
          <p className="text-[10px] uppercase tracking-widest text-gray-500">Analytics &amp; Forecasting</p>
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
                  ? "bg-brand-600/15 text-brand-200 shadow-[inset_0_0_0_1px_rgba(99,102,241,0.35)]"
                  : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
              )}
            >
              <Icon size={17} className={clsx(active ? "text-brand-300" : "text-gray-500 group-hover:text-gray-300")} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 pb-5">
        <div className="glass-card rounded-2xl p-4">
          <p className="text-xs font-semibold text-gray-200">Model coverage</p>
          <p className="mt-1 text-[11px] leading-relaxed text-gray-500">
            Baseline · SARIMA · XGBoost — evaluated with chronological validation on every training run.
          </p>
        </div>
      </div>
    </aside>
  );
}
