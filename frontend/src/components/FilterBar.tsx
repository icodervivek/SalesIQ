"use client";

import type { FilterOptions } from "@/lib/types";

interface FilterBarProps {
  options: FilterOptions | null;
  productId: string;
  region: string;
  category: string;
  onChange: (next: { productId?: string; region?: string; category?: string }) => void;
}

function Select({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-surface-border bg-surface-card px-3 py-2 text-sm text-gray-200 outline-none transition-colors focus:border-brand-500 min-w-[160px]"
      >
        {children}
      </select>
    </label>
  );
}

export function FilterBar({ options, productId, region, category, onChange }: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <Select label="Product" value={productId} onChange={(v) => onChange({ productId: v })}>
        <option value="">All products</option>
        {options?.products.map((p) => (
          <option key={p.product_id} value={p.product_id}>
            {p.product_name}
          </option>
        ))}
      </Select>
      <Select label="Region" value={region} onChange={(v) => onChange({ region: v })}>
        <option value="">All regions</option>
        {options?.regions.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </Select>
      <Select label="Category" value={category} onChange={(v) => onChange({ category: v })}>
        <option value="">All categories</option>
        {options?.categories.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </Select>
    </div>
  );
}
