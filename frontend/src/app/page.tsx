"use client";

import { useEffect, useState } from "react";
import { DollarSign, Package, Percent, ShoppingCart } from "lucide-react";
import { api } from "@/lib/api";
import { useDatasetContext } from "@/lib/dataset-context";
import { KpiCard } from "@/components/KpiCard";
import { ChartCard, EmptyState, Skeleton } from "@/components/ChartCard";
import { TrendChart } from "@/components/TrendChart";
import { RegionBarChart } from "@/components/RegionBarChart";
import { TopProductsTable } from "@/components/TopProductsTable";
import { DataQualityPanel } from "@/components/DataQualityPanel";
import { FilterBar } from "@/components/FilterBar";
import { Banner } from "@/components/Banner";
import type { CategoryPerf, Dataset, FilterOptions, RegionPerf, SummaryKpis, TopProduct, TrendPoint } from "@/lib/types";

export default function OverviewPage() {
  const { activeDatasetId, loading: datasetsLoading } = useDatasetContext();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [kpis, setKpis] = useState<SummaryKpis | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [regions, setRegions] = useState<RegionPerf[]>([]);
  const [categories, setCategories] = useState<CategoryPerf[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [filters, setFilters] = useState({ productId: "", region: "", category: "" });
  const [metric, setMetric] = useState<"revenue" | "units_sold">("revenue");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeDatasetId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = {
      product_id: filters.productId || undefined,
      region: filters.region || undefined,
      category: filters.category || undefined,
    };

    Promise.all([
      api.getDataset(activeDatasetId),
      api.summary(activeDatasetId, params),
      api.trends(activeDatasetId, "D", params),
      api.topProducts(activeDatasetId, { region: params.region, category: params.category }),
      api.regions(activeDatasetId),
      api.categories(activeDatasetId),
      api.filters(activeDatasetId),
    ])
      .then(([ds, summary, trendRes, topRes, regionRes, categoryRes, filterRes]) => {
        if (cancelled) return;
        setDataset(ds);
        setKpis(summary);
        setTrend(trendRes.trend);
        setTopProducts(topRes.top_products);
        setRegions(regionRes.regions);
        setCategories(categoryRes.categories);
        setFilterOptions(filterRes);
      })
      .catch((err) => !cancelled && setError(err.message || "Failed to load analytics."))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [activeDatasetId, filters]);

  if (!datasetsLoading && !activeDatasetId) {
    return (
      <EmptyState
        title="No dataset uploaded yet"
        description="Upload a sales CSV from the Upload Data page to see analytics, trends, and forecasts here."
      />
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Overview</h1>
          <p className="mt-1 text-sm text-gray-500">
            {kpis ? `${kpis.date_range.start} — ${kpis.date_range.end}` : "Business performance at a glance"}
          </p>
        </div>
        <FilterBar
          options={filterOptions}
          productId={filters.productId}
          region={filters.region}
          category={filters.category}
          onChange={(next) => setFilters((prev) => ({ ...prev, ...next }))}
        />
      </div>

      {error && <Banner tone="error" message={error} />}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {loading || !kpis ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-2xl" />)
        ) : (
          <>
            <KpiCard label="Total Revenue" value={`₹${kpis.total_revenue.toLocaleString()}`} icon={DollarSign} accent="brand" delta={kpis.revenue_growth_rate_pct} deltaLabel="vs prior 7 days" />
            <KpiCard label="Units Sold" value={kpis.total_units_sold.toLocaleString()} icon={ShoppingCart} accent="teal" />
            <KpiCard label="Avg Order Value" value={`₹${kpis.average_order_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} icon={Percent} accent="violet" />
            <KpiCard label="Products Tracked" value={`${kpis.num_products}`} icon={Package} accent="amber" />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ChartCard
            title="Sales Trend"
            subtitle="Daily performance over the selected period"
            action={
              <div className="flex rounded-lg border border-surface-border p-0.5 text-xs">
                {(["revenue", "units_sold"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMetric(m)}
                    className={`rounded-md px-2.5 py-1 font-medium transition-colors ${metric === m ? "bg-brand-600/20 text-brand-200" : "text-gray-500 hover:text-gray-300"}`}
                  >
                    {m === "revenue" ? "Revenue" : "Units"}
                  </button>
                ))}
              </div>
            }
          >
            {loading ? <Skeleton className="h-[300px] rounded-xl" /> : <TrendChart data={trend} metric={metric} />}
          </ChartCard>
        </div>

        <ChartCard title="Top Products" subtitle="Ranked by revenue">
          {loading ? <Skeleton className="h-[260px] rounded-xl" /> : <TopProductsTable products={topProducts.slice(0, 6)} />}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Regional Performance" subtitle="Revenue by region">
          {loading ? <Skeleton className="h-[260px] rounded-xl" /> : regions.length ? <RegionBarChart data={regions} /> : <EmptyState title="No regional data" description="This dataset does not include a region column." />}
        </ChartCard>
        <ChartCard title="Category Performance" subtitle="Revenue by product category">
          {loading ? <Skeleton className="h-[260px] rounded-xl" /> : categories.length ? <RegionBarChart data={categories} /> : <EmptyState title="No category data" description="This dataset does not include a category column." />}
        </ChartCard>
      </div>

      {dataset && (
        <ChartCard title="Data Quality" subtitle="Validation and cleaning summary for the active dataset">
          <DataQualityPanel validation={dataset.validation_report} cleaning={dataset.cleaning_summary} />
        </ChartCard>
      )}
    </div>
  );
}
