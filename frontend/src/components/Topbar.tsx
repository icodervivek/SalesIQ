"use client";

import { Database, ChevronDown } from "lucide-react";
import { useState } from "react";
import { useDatasetContext } from "@/lib/dataset-context";
import { clsx } from "clsx";

export function Topbar() {
  const { datasets, activeDatasetId, setActiveDatasetId, loading } = useDatasetContext();
  const [open, setOpen] = useState(false);
  const active = datasets.find((d) => d.id === activeDatasetId);

  return (
    <header className="flex h-16 items-center justify-between border-b border-surface-border bg-[#0d1120]/70 backdrop-blur-xl px-4 lg:px-8">
      <div>
        <h1 className="text-sm font-semibold text-white lg:hidden">SalesIQ</h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative">
          <button
            onClick={() => setOpen((v) => !v)}
            className="flex items-center gap-2 rounded-xl border border-surface-border bg-surface-card px-3.5 py-2 text-sm text-gray-200 hover:border-brand-500/50 transition-colors"
          >
            <Database size={15} className="text-brand-400" />
            <span className="max-w-[180px] truncate">
              {loading ? "Loading…" : active ? active.filename : "No dataset uploaded"}
            </span>
            <ChevronDown size={14} className="text-gray-500" />
          </button>

          {open && datasets.length > 0 && (
            <div className="absolute right-0 z-20 mt-2 w-72 overflow-hidden rounded-xl border border-surface-border bg-surface-card shadow-card animate-fade-in">
              {datasets.map((d) => (
                <button
                  key={d.id}
                  onClick={() => {
                    setActiveDatasetId(d.id);
                    setOpen(false);
                  }}
                  className={clsx(
                    "flex w-full flex-col items-start gap-0.5 px-4 py-2.5 text-left text-sm hover:bg-white/5",
                    d.id === activeDatasetId && "bg-brand-600/10"
                  )}
                >
                  <span className="truncate text-gray-100">{d.filename}</span>
                  <span className="text-[11px] text-gray-500">
                    {d.cleaned_row_count.toLocaleString()} clean rows · {new Date(d.uploaded_at).toLocaleDateString()}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
