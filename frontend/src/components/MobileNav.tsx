"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { LayoutDashboard, UploadCloud, TrendingUp } from "lucide-react";

const ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: UploadCloud },
  { href: "/forecast", label: "Forecast", icon: TrendingUp },
];

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 flex lg:hidden border-t border-surface-border bg-white/95 backdrop-blur-xl">
      {ITEMS.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex flex-1 flex-col items-center gap-1 py-3 text-[11px] font-medium",
              active ? "text-brand-600" : "text-stone-400"
            )}
          >
            <Icon size={18} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
