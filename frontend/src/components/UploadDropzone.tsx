"use client";

import { useCallback, useRef, useState } from "react";
import { clsx } from "clsx";
import { FileSpreadsheet, Loader2, UploadCloud } from "lucide-react";

export function UploadDropzone({ onFile, uploading }: { onFile: (file: File) => void; uploading: boolean }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.name.toLowerCase().endsWith(".csv")) return;
      onFile(file);
    },
    [onFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={clsx(
        "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-16 text-center transition-colors",
        dragging ? "border-brand-500 bg-brand-600/5" : "border-surface-border hover:border-brand-500/40 hover:bg-white/[0.02]"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient shadow-glow">
        {uploading ? <Loader2 size={22} className="animate-spin text-white" /> : <UploadCloud size={22} className="text-white" />}
      </div>
      <p className="mt-4 text-sm font-medium text-gray-200">
        {uploading ? "Uploading and validating…" : "Drop your sales CSV here, or click to browse"}
      </p>
      <p className="mt-1.5 flex items-center gap-1.5 text-xs text-gray-500">
        <FileSpreadsheet size={13} />
        Required columns: date, product_id, product_name, units_sold, revenue
      </p>
    </div>
  );
}
