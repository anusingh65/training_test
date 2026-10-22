"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface HealthData {
  status: string;
  models_loaded: Record<string, boolean>;
  blockchain_connected: boolean;
  event_listener_running: boolean;
  simulation_mode: boolean;
  websocket_clients: number;
}

interface DashboardStats {
  total_scans: number;
  total_flags: number;
  total_verifications: number;
  total_anomaly_checks: number;
  avg_trust_score: number;
  active_hotspots: number;
  risk_distribution: Record<string, number>;
  blockchain_connected: boolean;
  websocket_clients: number;
}

export default function OverviewPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/health").then(setHealth).catch((e) => setError(e.message));
    api.get("/api/dashboard-stats").then(setStats).catch(() => {});
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Backend Status</h1>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-4 mb-6">
          Cannot connect to backend: {error}
          <p className="text-sm mt-1 text-muted">
            Make sure the FastAPI server is running on {api.base}
          </p>
        </div>
      )}

      {health && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card label="Status" value={health.status} color="green" />
          <Card
            label="Blockchain"
            value={health.blockchain_connected ? "Connected" : "Disconnected"}
            color={health.blockchain_connected ? "green" : "red"}
          />
          <Card
            label="Event Listener"
            value={health.event_listener_running ? "Running" : "Stopped"}
            color={health.event_listener_running ? "green" : "yellow"}
          />
          <Card
            label="Simulation Mode"
            value={health.simulation_mode ? "ON" : "OFF"}
            color={health.simulation_mode ? "yellow" : "muted"}
          />
        </div>
      )}

      {health && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Models Loaded</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(health.models_loaded).map(([name, loaded]) => (
              <div
                key={name}
                className={`rounded-lg p-3 border text-sm ${
                  loaded
                    ? "bg-green-500/10 border-green-500/30 text-green-400"
                    : "bg-red-500/10 border-red-500/30 text-red-400"
                }`}
              >
                <div className="font-mono text-xs">{name}</div>
                <div className="font-bold mt-1">{loaded ? "Loaded" : "Not loaded"}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Dashboard Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Card label="Total Scans" value={stats.total_scans} />
            <Card label="Total Flags" value={stats.total_flags} color="red" />
            <Card label="Verifications" value={stats.total_verifications} />
            <Card label="Anomaly Checks" value={stats.total_anomaly_checks} />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card label="Avg Trust Score" value={stats.avg_trust_score.toFixed(1)} color="accent" />
            <Card label="Active Hotspots" value={stats.active_hotspots} color="yellow" />
            <Card label="WS Clients" value={stats.websocket_clients} />
            <Card
              label="Blockchain"
              value={stats.blockchain_connected ? "Connected" : "Off"}
              color={stats.blockchain_connected ? "green" : "muted"}
            />
          </div>

          {stats.risk_distribution && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold mb-2 text-muted">Risk Distribution</h3>
              <div className="flex gap-3">
                {Object.entries(stats.risk_distribution).map(([level, count]) => (
                  <div
                    key={level}
                    className="bg-surface rounded-lg px-4 py-2 border border-white/5"
                  >
                    <span className="text-xs text-muted uppercase">{level}</span>
                    <span className="ml-2 font-bold">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Card({
  label,
  value,
  color = "accent",
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  const colorMap: Record<string, string> = {
    green: "text-green-400",
    red: "text-red-400",
    yellow: "text-yellow-400",
    accent: "text-blue-400",
    muted: "text-muted",
  };
  return (
    <div className="bg-surface rounded-lg p-4 border border-white/5">
      <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
      <div className={`text-xl font-bold mt-1 ${colorMap[color] || "text-white"}`}>
        {value}
      </div>
    </div>
  );
}
