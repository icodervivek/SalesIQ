"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { DatasetListItem } from "./types";

interface DatasetContextValue {
  datasets: DatasetListItem[];
  activeDatasetId: number | null;
  setActiveDatasetId: (id: number | null) => void;
  refreshDatasets: () => Promise<void>;
  loading: boolean;
}

const DatasetContext = createContext<DatasetContextValue | null>(null);

export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshDatasets = useCallback(async () => {
    setLoading(true);
    try {
      const list = await api.listDatasets();
      setDatasets(list);
      setActiveDatasetId((prev) => {
        if (prev && list.some((d) => d.id === prev)) return prev;
        return list.length > 0 ? list[0].id : null;
      });
    } catch {
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  const value = useMemo(
    () => ({ datasets, activeDatasetId, setActiveDatasetId, refreshDatasets, loading }),
    [datasets, activeDatasetId, refreshDatasets, loading]
  );

  return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>;
}

export function useDatasetContext() {
  const ctx = useContext(DatasetContext);
  if (!ctx) throw new Error("useDatasetContext must be used within DatasetProvider");
  return ctx;
}
