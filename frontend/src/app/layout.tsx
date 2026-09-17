import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { DatasetProvider } from "@/lib/dataset-context";
import { MobileNav } from "@/components/MobileNav";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "SalesIQ — Intelligent Sales Analytics & Forecasting",
  description: "AI/ML-powered sales analytics and demand forecasting platform.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans bg-surface text-stone-900 min-h-screen`}>
        <DatasetProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <Topbar />
              <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8 pb-24 lg:pb-8">{children}</main>
              <MobileNav />
            </div>
          </div>
        </DatasetProvider>
      </body>
    </html>
  );
}
