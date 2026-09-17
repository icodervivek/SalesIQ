"use client";

import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useDatasetContext } from "@/lib/dataset-context";
import { UploadDropzone } from "@/components/UploadDropzone";
import { ChartCard } from "@/components/ChartCard";
import { DataQualityPanel } from "@/components/DataQualityPanel";
import { Banner } from "@/components/Banner";
import type { Dataset } from "@/lib/types";

export default function UploadPage() {
  const { refreshDatasets, setActiveDatasetId } = useDatasetContext();
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const dataset = await api.uploadDataset(file);
      setResult(dataset);
      await refreshDatasets();
      setActiveDatasetId(dataset.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please check the file and try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Upload Sales Data</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload a CSV with historical sales transactions. Required columns: <code className="text-gray-400">date, product_id, product_name, units_sold, revenue</code>.
          Recommended: <code className="text-gray-400">category, region, unit_price</code>.
        </p>
      </div>

      <UploadDropzone onFile={handleFile} uploading={uploading} />

      {error && <Banner tone="error" message={error} />}

      {result && (
        <>
          <Banner
            tone="success"
            message={`"${result.filename}" uploaded — ${result.cleaned_row_count.toLocaleString()} of ${result.row_count.toLocaleString()} rows are ready for analysis.`}
          />
          <ChartCard
            title="Validation & Cleaning Report"
            subtitle="What was checked, and how the pipeline handled issues"
            action={<CheckCircle2 size={16} className="text-accent-emerald" />}
          >
            <DataQualityPanel validation={result.validation_report} cleaning={result.cleaning_summary} />
          </ChartCard>
        </>
      )}

      <ChartCard title="Expected CSV Format" subtitle="Column reference">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-surface-border text-left text-gray-500">
                <th className="py-2 pr-4 font-medium">Column</th>
                <th className="py-2 pr-4 font-medium">Type</th>
                <th className="py-2 font-medium">Requirement</th>
              </tr>
            </thead>
            <tbody className="text-gray-400">
              {[
                ["date", "Date", "Required"],
                ["product_id", "String", "Required"],
                ["product_name", "String", "Required"],
                ["units_sold", "Numeric", "Required"],
                ["revenue", "Numeric", "Required"],
                ["category", "String", "Recommended"],
                ["region", "String", "Recommended"],
                ["unit_price", "Numeric", "Recommended"],
                ["discount", "Numeric", "Optional"],
                ["marketing_spend", "Numeric", "Optional"],
              ].map(([col, type, req]) => (
                <tr key={col} className="border-b border-surface-border/50 last:border-0">
                  <td className="py-2 pr-4 font-mono text-gray-300">{col}</td>
                  <td className="py-2 pr-4">{type}</td>
                  <td className="py-2">{req}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  );
}
