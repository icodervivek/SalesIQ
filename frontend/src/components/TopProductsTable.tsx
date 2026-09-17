import type { TopProduct } from "@/lib/types";

export function TopProductsTable({ products }: { products: TopProduct[] }) {
  const max = Math.max(...products.map((p) => p.revenue), 1);
  return (
    <div className="space-y-3">
      {products.map((p, i) => (
        <div key={p.product_id} className="flex items-center gap-3">
          <span className="w-5 shrink-0 text-xs font-medium text-stone-400">{i + 1}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2 text-sm">
              <span className="truncate text-stone-700">{p.product_name}</span>
              <span className="shrink-0 font-medium text-stone-900">₹{p.revenue.toLocaleString()}</span>
            </div>
            <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-stone-900/[0.05]">
              <div
                className="h-full rounded-full bg-brand-gradient"
                style={{ width: `${Math.max(4, (p.revenue / max) * 100)}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
