"use client";

import { AlertTriangle, Database, ChevronDown, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useDatasetContext } from "@/lib/dataset-context";
import { api, ApiError } from "@/lib/api";
import { clsx } from "clsx";

export function Topbar() {
  const { datasets, activeDatasetId, setActiveDatasetId, loading, refreshDatasets } = useDatasetContext();
  const [open, setOpen] = useState(false);
  const [datasetToDelete, setDatasetToDelete] = useState<{
    id: number;
    filename: string;
    duplicateCount: number;
  } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const active = datasets.find((d) => d.id === activeDatasetId);
  const menuRef = useRef<HTMLDivElement>(null);
  const deleteDialogRef = useRef<HTMLElement>(null);
  const cancelDeleteRef = useRef<HTMLButtonElement>(null);

  async function confirmDelete() {
    if (!datasetToDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteDataset(datasetToDelete.id);
      await refreshDatasets();
      setOpen(false);
      setDatasetToDelete(null);
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : "Could not delete the dataset.");
    } finally {
      setDeleting(false);
    }
  }

  useEffect(() => {
    if (!datasetToDelete) return;

    cancelDeleteRef.current?.focus();
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (!deleting) setDatasetToDelete(null);
        return;
      }

      if (e.key !== "Tab") return;
      const focusable = deleteDialogRef.current?.querySelectorAll<HTMLElement>("button:not(:disabled)");
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [datasetToDelete, deleting]);

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
    <header className="relative z-40 flex h-16 items-center justify-between border-b border-surface-border bg-white/75 backdrop-blur-xl px-4 lg:px-8">
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
            <div className="absolute right-0 z-20 mt-2 max-h-[min(70vh,32rem)] w-80 overflow-y-auto rounded-xl border border-surface-border bg-surface-card shadow-card animate-fade-in">
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
                    disabled={deleting}
                    onClick={() => {
                      setDeleteError(null);
                      setDatasetToDelete({
                        id: d.id,
                        filename: d.filename,
                        duplicateCount: d.duplicate_count,
                      });
                    }}
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
      {datasetToDelete && typeof document !== "undefined" &&
        createPortal(
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-stone-950/40 px-4 py-6 backdrop-blur-sm"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget && !deleting) setDatasetToDelete(null);
            }}
          >
            <section
              ref={deleteDialogRef}
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="delete-dataset-title"
              aria-describedby="delete-dataset-description"
              className="w-full max-w-md rounded-2xl border border-white/70 bg-white p-6 shadow-2xl animate-fade-in"
            >
              <div className="flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600">
                  <AlertTriangle size={21} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <h2 id="delete-dataset-title" className="text-base font-semibold text-stone-900">
                      Delete this dataset?
                    </h2>
                    <button
                      type="button"
                      aria-label="Close confirmation"
                      disabled={deleting}
                      onClick={() => setDatasetToDelete(null)}
                      className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 disabled:opacity-50"
                    >
                      <X size={17} />
                    </button>
                  </div>
                  <p id="delete-dataset-description" className="mt-2 break-words text-sm text-stone-600">
                    <span className="font-medium text-stone-800">{datasetToDelete.filename}</span> and its saved
                    analytics data will be permanently removed.
                    {datasetToDelete.duplicateCount > 1 &&
                      ` This includes ${datasetToDelete.duplicateCount - 1} other upload(s) with identical cleaned data.`}
                    {" "}Associated training runs and forecasts will also be deleted.
                  </p>
                </div>
              </div>
              {deleteError && (
                <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                  {deleteError}
                </p>
              )}
              <div className="mt-7 flex justify-end gap-3">
                <button
                  ref={cancelDeleteRef}
                  type="button"
                  disabled={deleting}
                  onClick={() => setDatasetToDelete(null)}
                  className="rounded-xl border border-surface-border px-4 py-2.5 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={deleting}
                  onClick={confirmDelete}
                  className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-red-700 disabled:cursor-wait disabled:opacity-60"
                >
                  <Trash2 size={15} />
                  {deleting ? "Deleting…" : "Delete dataset"}
                </button>
              </div>
            </section>
          </div>,
          document.body
        )}
    </header>
  );
}
