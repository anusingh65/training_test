"use client";

import { useEffect, useRef, useState } from "react";
import { Pill, ShieldCheck, AlertTriangle, MapPin } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  iconBg: string;
  suffix?: string;
  delay?: number;
}

function StatCard({ label, value, icon, iconBg, suffix = "", delay = 0 }: StatCardProps) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (value === 0) return;
    const timeout = setTimeout(() => {
      const duration = 800;
      const steps = 25;
      const increment = value / steps;
      let current = 0;
      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          setDisplay(value);
          clearInterval(timer);
        } else {
          setDisplay(Math.floor(current));
        }
      }, duration / steps);
      return () => clearInterval(timer);
    }, delay);
    return () => clearTimeout(timeout);
  }, [value, delay]);

  return (
    <div
      ref={ref}
      className="bg-white border border-border rounded-lg p-6 shadow-card hover:shadow-card-hover transition-shadow"
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-text-secondary text-sm font-medium">{label}</span>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${iconBg}`}>
          {icon}
        </div>
      </div>
      <p className="text-3xl font-semibold text-foreground tracking-tight">
        {display.toLocaleString()}
        <span className="text-lg text-text-tertiary">{suffix}</span>
      </p>
    </div>
  );
}

interface StatsGridProps {
  totalDrugs: number;
  verificationRate: number;
  activeFlags: number;
  highRiskZones: number;
}

export default function StatsGrid({
  totalDrugs,
  verificationRate,
  activeFlags,
  highRiskZones,
}: StatsGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Total Drugs"
        value={totalDrugs}
        icon={<Pill size={20} className="text-primary" />}
        iconBg="bg-primary-50"
        delay={0}
      />
      <StatCard
        label="Verification Rate"
        value={verificationRate}
        icon={<ShieldCheck size={20} className="text-success" />}
        iconBg="bg-success-light"
        suffix="%"
        delay={100}
      />
      <StatCard
        label="Active Flags"
        value={activeFlags}
        icon={<AlertTriangle size={20} className="text-danger" />}
        iconBg="bg-danger-light"
        delay={200}
      />
      <StatCard
        label="High-Risk Zones"
        value={highRiskZones}
        icon={<MapPin size={20} className="text-warning" />}
        iconBg="bg-warning-light"
        delay={300}
      />
    </div>
  );
}
