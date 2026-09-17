import { AlertCircle, CheckCircle2 } from "lucide-react";
import { clsx } from "clsx";

export function Banner({ tone = "error", message }: { tone?: "error" | "success"; message: string }) {
  return (
    <div
      className={clsx(
        "flex items-center gap-2 rounded-xl border px-4 py-3 text-sm animate-fade-in",
        tone === "error" ? "border-accent-rose/30 bg-accent-rose/10 text-accent-rose" : "border-accent-emerald/30 bg-accent-emerald/10 text-accent-emerald"
      )}
    >
      {tone === "error" ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
      {message}
    </div>
  );
}
