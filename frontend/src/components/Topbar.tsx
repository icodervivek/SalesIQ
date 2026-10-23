"use client";

import { Database, ChevronDown, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useDatasetContext } from "@/lib/dataset-context";
import { api, ApiError } from "@/lib/api";
import { clsx } from "clsx";

export function Topbar() {
  const { datasets, activeDatasetId, setActiveDatasetId, loading, refreshDatasets } = useDatasetContext();
  const [open, setOpen] = useState(false);
  const [deletingDatasetId, setDeletingDatasetId] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const active = datasets.find((d) => d.id === activeDatasetId);
  const menuRef = useRef<HTMLDivElement>(null);

  async function handleDelete(datasetId: number, filename: string, duplicateCount: number) {
    const copies =
      duplicateCount > 1
        ? ` This will also remove ${duplicateCount - 1} other upload(s) with identical cleaned data.`
        : "";
    const confirmed = window.confirm(
      `Delete "${filename}"?${copies} Its associated training runs and forecasts will also be deleted.`
    );
    if (!confirmed) return;

    setDeletingDatasetId(datasetId);
    setDeleteError(null);
    try {
      await api.deleteDataset(datasetId);
      await refreshDatasets();
      setOpen(false);
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : "Could not delete the dataset.");
    } finally {
      setDeletingDatasetId(null);
    }
  }

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
            <div className="absolute right-0 z-20 mt-2 w-80 overflow-hidden rounded-xl border border-surface-border bg-surface-card shadow-card animate-fade-in">
              {deleteError && (
                <p role="alert" className="border-b border-surface-border px-4 py-2 text-xs text-red-600">
                  {deleteError}
                </p>
              )}
              {datasets.map((d) => (
                <div
                  key={d.id}
                  className={clsx(
                    "flex items-center gap-2 border-b border-surface-border/60 px-2 last:border-0",
                    d.id === activeDatasetId && "bg-brand-500/[0.06]"
                  )}
                >
                  <button
                    onClick={() => {
                      setActiveDatasetId(d.id);
                      setOpen(false);
                    }}
                    className="flex min-w-0 flex-1 flex-col items-start gap-0.5 px-2 py-2.5 text-left text-sm hover:bg-stone-900/[0.03]"
                  >
                    <span className="w-full truncate text-stone-800">{d.filename}</span>
                    <span className="text-[11px] text-stone-400">
                      {d.cleaned_row_count.toLocaleString()} clean rows · {new Date(d.uploaded_at).toLocaleDateString()}
                      {d.duplicate_count > 1 && ` · ${d.duplicate_count} uploads with identical cleaned data`}
                    </span>
                  </button>
                  <button
                    type="button"
                    aria-label={`Delete ${d.filename}`}
                    title="Delete dataset"
                    disabled={deletingDatasetId !== null}
                    onClick={() => handleDelete(d.id, d.filename, d.duplicate_count)}
                    className="rounded-lg p-2 text-stone-400 transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
