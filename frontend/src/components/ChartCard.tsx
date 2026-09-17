export function ChartCard({
  title,
  subtitle,
  action,
  children,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="glass-card rounded-2xl p-5 shadow-card">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-100">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className || "h-4 w-full"}`} />;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-surface-border py-16 text-center">
      <p className="text-sm font-medium text-gray-300">{title}</p>
      <p className="mt-1 max-w-sm text-xs text-gray-500">{description}</p>
    </div>
  );
}
