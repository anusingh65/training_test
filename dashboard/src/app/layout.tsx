import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "MediChain Test Dashboard",
  description: "Test dashboard for MediChain AI backend",
};

const navLinks = [
  { href: "/", label: "Overview" },
  { href: "/heatmap", label: "Heatmap" },
  { href: "/anomaly", label: "Anomaly" },
  { href: "/verify", label: "Verify Pill" },
  { href: "/adverse", label: "Adverse Events" },
  { href: "/risk", label: "Risk Score" },
  { href: "/batch-trace", label: "Batch Trace" },
  { href: "/alerts", label: "Alerts (WS)" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-primary text-white min-h-screen">
        <nav className="bg-surface border-b border-white/10 px-6 py-3 flex items-center gap-6 sticky top-0 z-50">
          <span className="font-bold text-lg text-accent-light tracking-tight mr-4">
            MediChain
          </span>
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-muted hover:text-white transition-colors"
            >
              {l.label}
            </Link>
          ))}
          <span className="ml-auto text-xs text-muted/50">Test Dashboard</span>
        </nav>
        <main className="p-6 max-w-7xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
