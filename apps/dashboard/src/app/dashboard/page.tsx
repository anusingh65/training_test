"use client";

import StatsGrid from "@/components/StatsGrid";
import HeatMap from "@/components/HeatMap";
import AlertFeed from "@/components/AlertFeed";
import VerificationBadge from "@/components/VerificationBadge";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/ui/Card";
import { useDrugStats } from "@/hooks/useDrugStats";
import { isMockMode, MOCK_SCANS } from "@/lib/mock-data";

export default function DashboardHome() {
  const { stats, loading } = useDrugStats();

  const recentActivity = [...MOCK_SCANS]
    .sort((a, b) => b.scanned_at.localeCompare(a.scanned_at))
    .slice(0, 6);

  return (
    <div>
      <PageHeader
        title="Dashboard Overview"
        description={
          isMockMode()
            ? "Real-time pharmaceutical supply chain monitoring"
            : "Real-time pharmaceutical supply chain monitoring"
        }
        breadcrumbs={[{ label: "Dashboard" }]}
        actions={
          isMockMode() ? (
            <span className="text-xs bg-primary-50 text-primary px-2 py-0.5 rounded-full font-medium">
              Demo Mode
            </span>
          ) : undefined
        }
      />

      <div className="animate-fade-in">
        <StatsGrid
          totalDrugs={stats.totalDrugs}
          verificationRate={stats.verificationRate}
          activeFlags={stats.activeFlags}
          highRiskZones={stats.highRiskZones}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <div className="lg:col-span-2 animate-fade-in animate-fade-in-delay-1">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Risk Heatmap</h2>
            <a href="/dashboard/heatmap" className="text-xs text-primary hover:underline">
              Full screen →
            </a>
          </div>
          <HeatMap />
        </div>

        <div className="animate-fade-in animate-fade-in-delay-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Recent Alerts</h2>
            <a href="/dashboard/alerts" className="text-xs text-primary hover:underline">
              View all →
            </a>
          </div>
          <div className="max-h-80 overflow-y-auto pr-1">
            <AlertFeed />
          </div>
        </div>
      </div>

      <div className="mt-6 animate-fade-in animate-fade-in-delay-3">
        <h2 className="text-lg font-semibold text-foreground mb-4">Recent Scans</h2>
        <Card padding="sm" className="overflow-hidden">
          <div className="grid grid-cols-4 text-xs text-text-secondary uppercase tracking-wider px-6 py-3 bg-gray-50/50 border-b border-border -mx-4 -mt-4">
            <span>Drug ID</span>
            <span>Result</span>
            <span>Location</span>
            <span>Time</span>
          </div>
          {recentActivity.map((scan) => (
            <div
              key={scan.id}
              className="grid grid-cols-4 px-6 py-3 text-sm border-b border-border/50 hover:bg-gray-50 transition-colors -mx-4"
            >
              <span className="font-mono text-primary text-xs">{scan.drug_id}</span>
              <span>
                <VerificationBadge status={scan.result} />
              </span>
              <span className="text-text-secondary text-xs">{scan.location}</span>
              <span className="text-text-tertiary text-xs">
                {new Date(scan.scanned_at).toLocaleDateString()}
              </span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}
