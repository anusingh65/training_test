"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";
import { supabase } from "@/lib/supabase";
import { isMockMode, MOCK_DRUGS, MOCK_SCANS, MOCK_ALERTS } from "@/lib/mock-data";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/ui/Card";

const STATUS_COLORS: Record<string, string> = {
  verified: "#059669",
  suspicious: "#D97706",
  counterfeit: "#DC2626",
  pending: "#6B7280",
};

function buildMockData() {
  const counts: Record<string, number> = {};
  MOCK_DRUGS.forEach((d) => {
    counts[d.status] = (counts[d.status] || 0) + 1;
  });
  const statusData = Object.entries(counts).map(([name, value]) => ({ name, value }));

  const byDate: Record<string, number> = {};
  MOCK_SCANS.forEach((s) => {
    const date = s.scanned_at.split("T")[0];
    byDate[date] = (byDate[date] || 0) + 1;
  });
  const scanTrends = Object.entries(byDate)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, scans]) => ({ date: date.slice(5), scans }));

  const batchCounts: Record<string, number> = {};
  MOCK_ALERTS.forEach((f) => {
    batchCounts[f.drug_id] = (batchCounts[f.drug_id] || 0) + 1;
  });
  const topFlagged = Object.entries(batchCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([drug_id, count]) => ({ drug_id, count }));

  const mfgCounts: Record<string, number> = {};
  MOCK_DRUGS.forEach((d) => {
    mfgCounts[d.manufacturer] = (mfgCounts[d.manufacturer] || 0) + 1;
  });
  const mfgData = Object.entries(mfgCounts)
    .sort(([, a], [, b]) => b - a)
    .map(([name, count]) => ({ name: name.split(" ")[0], count }));

  return { statusData, scanTrends, topFlagged, mfgData };
}

export default function AnalyticsPage() {
  const [statusData, setStatusData] = useState<{ name: string; value: number }[]>([]);
  const [scanTrends, setScanTrends] = useState<{ date: string; scans: number }[]>([]);
  const [topFlagged, setTopFlagged] = useState<{ drug_id: string; count: number }[]>([]);
  const [mfgData, setMfgData] = useState<{ name: string; count: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode()) {
      const mock = buildMockData();
      setStatusData(mock.statusData);
      setScanTrends(mock.scanTrends);
      setTopFlagged(mock.topFlagged);
      setMfgData(mock.mfgData);
      setLoading(false);
      return;
    }

    async function fetchData() {
      const { data: drugs } = await supabase.from("drugs").select("status, manufacturer");
      if (drugs) {
        const counts: Record<string, number> = {};
        const mfg: Record<string, number> = {};
        drugs.forEach((d: any) => {
          counts[d.status] = (counts[d.status] || 0) + 1;
          mfg[d.manufacturer] = (mfg[d.manufacturer] || 0) + 1;
        });
        setStatusData(Object.entries(counts).map(([name, value]) => ({ name, value })));
        setMfgData(Object.entries(mfg).sort(([, a], [, b]) => b - a).map(([name, count]) => ({ name: name.split(" ")[0], count })));
      }

      const { data: scans } = await supabase.from("verification_scans").select("scanned_at");
      if (scans) {
        const byDate: Record<string, number> = {};
        scans.forEach((s: any) => {
          const date = s.scanned_at.split("T")[0];
          byDate[date] = (byDate[date] || 0) + 1;
        });
        setScanTrends(
          Object.entries(byDate)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([date, s]) => ({ date: date.slice(5), scans: s }))
        );
      }

      const { data: flags } = await supabase.from("flagged_reports").select("drug_id");
      if (flags) {
        const bc: Record<string, number> = {};
        flags.forEach((f: any) => { bc[f.drug_id] = (bc[f.drug_id] || 0) + 1; });
        setTopFlagged(Object.entries(bc).sort(([, a], [, b]) => b - a).slice(0, 10).map(([drug_id, count]) => ({ drug_id, count })));
      }
      setLoading(false);
    }
    fetchData();
  }, []);

  const tooltipStyle = { background: "#FFFFFF", border: "1px solid #E5E7EB", borderRadius: "8px", fontSize: "12px", color: "#111827" };

  if (loading) {
    return (
      <div>
        <PageHeader
          title="Analytics"
          breadcrumbs={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Analytics" },
          ]}
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white border border-border rounded-lg p-6 h-[380px] animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Analytics"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Analytics" },
        ]}
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-lg font-semibold text-foreground mb-4">Drug Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={4}
                label={({ name, percent }: { name: string; percent: number }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
              >
                {statusData.map((entry, index) => (
                  <Cell key={index} fill={STATUS_COLORS[entry.name] || "#6B7280"} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-foreground mb-4">Scans Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={scanTrends}>
              <defs>
                <linearGradient id="scanGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0D9488" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0D9488" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="scans" stroke="#0D9488" strokeWidth={2} fill="url(#scanGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-foreground mb-4">Top Flagged Drugs</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topFlagged} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" horizontal={false} />
              <XAxis type="number" stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="drug_id" stroke="#9CA3AF" fontSize={11} width={80} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill="#DC2626" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-foreground mb-4">Drugs by Manufacturer</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={mfgData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="name" stroke="#9CA3AF" fontSize={10} angle={-30} textAnchor="end" height={60} tickLine={false} axisLine={false} />
              <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill="#0D9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
