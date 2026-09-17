"use client";

import { Database, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useDatasetContext } from "@/lib/dataset-context";
import { clsx } from "clsx";

export function Topbar() {
  const { datasets, activeDatasetId, setActiveDatasetId, loading } = useDatasetContext();
  const [open, setOpen] = useState(false);
  const active = datasets.find((d) => d.id === activeDatasetId);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(e: PointerEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <header className="flex h-16 items-center justify-between border-b border-surface-border bg-white/75 backdrop-blur-xl px-4 lg:px-8">
      <div>
        <h1 className="text-sm font-semibold text-stone-900 lg:hidden">SalesIQ</h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setOpen((v) => !v)}
            className="flex items-center gap-2 rounded-xl border border-surface-border bg-surface-card px-3.5 py-2 text-sm text-stone-700 hover:border-brand-500/50 transition-colors"
          >
            <Database size={15} className="text-brand-500" />
            <span className="max-w-[180px] truncate">
              {loading ? "Loading…" : active ? active.filename : "No dataset uploaded"}
            </span>
            <ChevronDown size={14} className="text-stone-400" />
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
                    "flex w-full flex-col items-start gap-0.5 px-4 py-2.5 text-left text-sm hover:bg-stone-900/[0.03]",
                    d.id === activeDatasetId && "bg-brand-500/[0.06]"
                  )}
                >
                  <span className="truncate text-stone-800">{d.filename}</span>
                  <span className="text-[11px] text-stone-400">
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
