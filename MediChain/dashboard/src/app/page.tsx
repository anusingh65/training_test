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

const AI_MODULES = [
  {
    name: "Anomaly Detection",
    key: "anomaly_detector",
    icon: "🔍",
    desc: "Isolation Forest + Autoencoder ensemble analyzes 12 supply chain features to detect suspicious transfer patterns, velocity violations, and timing anomalies.",
    weight: "45% of risk score",
    link: "/anomaly",
  },
  {
    name: "Geographic Heatmap",
    key: "heatmap_engine",
    icon: "🗺️",
    desc: "DBSCAN clustering with time-decay weighting identifies counterfeit hotspots across India. Monitors known pharma hubs like Bhagirath Palace (Delhi) and Crawford Market (Mumbai).",
    weight: "40% of risk score",
    link: "/heatmap",
  },
  {
    name: "Risk Scoring Engine",
    key: "risk_scorer",
    icon: "⚖️",
    desc: "Weighted ensemble fuses all AI signals into a single 0-100 Trust Score. Scores below 50 auto-flag medicines on the blockchain via smart contract.",
    weight: "Composite output",
    link: "/risk",
  },
  {
    name: "Batch Trace Analysis",
    key: "heatmap_engine",
    icon: "🔗",
    desc: "Traces medicine batches through the entire supply chain, detecting route deviations, velocity impossibilities, and suspicious transfer patterns at each step.",
    weight: "Forensic tool",
    link: "/batch-trace",
  },
];

const ARCHITECTURE_FLOW = [
  { label: "Manufacturer", sub: "Registers batch on blockchain", color: "text-blue-400" },
  { label: "QR Scan + GPS", sub: "Mobile app logs scan with coordinates", color: "text-cyan-400" },
  { label: "AI Engine", sub: "Anomaly + Geographic + External signals", color: "text-emerald-400" },
  { label: "Risk Score", sub: "Trust Score 0-100, auto-flag if < 50", color: "text-yellow-400" },
  { label: "Blockchain Flag", sub: "flagDrug(id, severity) on Sepolia", color: "text-red-400" },
  { label: "Real-time Alert", sub: "WebSocket push to all connected clients", color: "text-purple-400" },
];

export default function OverviewPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/health").then(setHealth).catch((e) => setError(e.message));
    api.get("/api/dashboard-stats").then(setStats).catch(() => {});
  }, []);

  const loadedCount = health
    ? Object.values(health.models_loaded).filter(Boolean).length
    : 0;
  const totalModels = health ? Object.keys(health.models_loaded).length : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">MediChain AI Dashboard</h1>
        <p className="text-muted text-sm max-w-2xl">
          AI-powered pharmaceutical supply chain monitoring. Detects counterfeit drugs
          using anomaly detection, geographic heatmapping, and composite risk scoring —
          all connected to Ethereum smart contracts on Sepolia testnet.
        </p>
      </div>

      {/* Connection Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-4">
          Cannot connect to backend: {error}
          <p className="text-sm mt-1 text-muted">
            Make sure the FastAPI server is running on {api.base}
          </p>
        </div>
      )}

      {/* Live System Status */}
      {health && (
        <div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Live System Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatusCard
              label="Backend"
              value={health.status === "ok" ? "Online" : "Error"}
              ok={health.status === "ok"}
            />
            <StatusCard
              label="Blockchain"
              value={health.blockchain_connected ? "Sepolia" : "Disconnected"}
              ok={health.blockchain_connected}
            />
            <StatusCard
              label="Event Listener"
              value={health.event_listener_running ? "Active" : "Stopped"}
              ok={health.event_listener_running}
            />
            <StatusCard
              label="AI Models"
              value={`${loadedCount}/${totalModels}`}
              ok={loadedCount >= 3}
            />
            <StatusCard
              label="WebSocket"
              value={`${health.websocket_clients} client${health.websocket_clients !== 1 ? "s" : ""}`}
              ok={true}
            />
          </div>
        </div>
      )}

      {/* Data Pipeline Flow */}
      <div>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Data Pipeline</h2>
        <div className="bg-surface rounded-xl border border-white/5 p-5">
          <div className="flex items-center gap-1 overflow-x-auto pb-2">
            {ARCHITECTURE_FLOW.map((step, i) => (
              <div key={i} className="flex items-center flex-shrink-0">
                <div className="bg-primary rounded-lg px-4 py-3 border border-white/10 min-w-[150px]">
                  <div className={`font-semibold text-sm ${step.color}`}>{step.label}</div>
                  <div className="text-[10px] text-muted mt-1">{step.sub}</div>
                </div>
                {i < ARCHITECTURE_FLOW.length - 1 && (
                  <div className="text-muted/40 mx-1 text-lg flex-shrink-0">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Modules */}
      <div>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">AI Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {AI_MODULES.map((mod) => {
            const loaded = health?.models_loaded?.[mod.key];
            return (
              <a
                key={mod.name}
                href={mod.link}
                className="bg-surface rounded-xl p-5 border border-white/5 hover:border-white/15 transition-colors group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{mod.icon}</span>
                    <div>
                      <h3 className="font-semibold group-hover:text-accent-light transition-colors">{mod.name}</h3>
                      <span className="text-[10px] text-accent-light/70 font-mono">{mod.weight}</span>
                    </div>
                  </div>
                  {health && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                      loaded
                        ? "text-green-400 border-green-500/30 bg-green-500/10"
                        : "text-yellow-400 border-yellow-500/30 bg-yellow-500/10"
                    }`}>
                      {loaded ? "Loaded" : "Standby"}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted leading-relaxed">{mod.desc}</p>
              </a>
            );
          })}
        </div>
      </div>

      {/* Session Stats */}
      {stats && (
        <div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Session Activity</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="Risk Assessments" value={stats.total_scans} />
            <MetricCard label="Drugs Flagged" value={stats.total_flags} accent="red" />
            <MetricCard label="Anomaly Checks" value={stats.total_anomaly_checks} />
            <MetricCard label="Active Hotspots" value={stats.active_hotspots} accent="yellow" />
          </div>
          {stats.avg_trust_score > 0 && (
            <div className="mt-3 bg-surface rounded-xl p-4 border border-white/5">
              <div className="flex items-center gap-6">
                <div>
                  <div className="text-xs text-muted">Avg Trust Score</div>
                  <div className="text-2xl font-bold" style={{
                    color: stats.avg_trust_score >= 80 ? "#10B981"
                      : stats.avg_trust_score >= 50 ? "#F59E0B"
                      : "#EF4444"
                  }}>
                    {stats.avg_trust_score.toFixed(1)}
                  </div>
                </div>
                <div className="flex gap-3 ml-auto">
                  {Object.entries(stats.risk_distribution).map(([level, count]) => (
                    <div key={level} className="text-center">
                      <div className={`text-lg font-bold ${
                        level === "low" ? "text-green-400"
                        : level === "medium" ? "text-yellow-400"
                        : level === "high" ? "text-orange-400"
                        : "text-red-400"
                      }`}>{count}</div>
                      <div className="text-[10px] text-muted uppercase">{level}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trust Score Scale */}
      <div>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Trust Score Scale</h2>
        <div className="bg-surface rounded-xl p-5 border border-white/5">
          <div className="flex gap-2 mb-3">
            <div className="flex-1 h-3 rounded-full bg-red-500/80" title="Critical: 0-19" />
            <div className="flex-1 h-3 rounded-full bg-orange-500/80" title="High: 20-49" />
            <div className="flex-1 h-3 rounded-full bg-yellow-500/80" title="Medium: 50-79" />
            <div className="flex-1 h-3 rounded-full bg-green-500/80" title="Low: 80-100" />
          </div>
          <div className="flex justify-between text-[10px] text-muted">
            <span>0 — Critical (auto-flag + alert)</span>
            <span>20 — High (auto-flag on chain)</span>
            <span>50 — Medium (warning)</span>
            <span>80 — Low (safe)</span>
            <span>100</span>
          </div>
        </div>
      </div>

      {/* Smart Contract Info */}
      <div>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Smart Contracts (Sepolia)</h2>
        <div className="bg-surface rounded-xl p-5 border border-white/5 space-y-2">
          <ContractRow name="PharmaChainCore" address="0x42b07481fF87A9bBa4F6e9FA3DC7b81fFcBf7e7c" desc="Medicine registration, custody transfer, drug flagging" />
          <ContractRow name="PharmaChainScanner" address="0x710a91E2fCeF8662C150FA8C852063e119e12162" desc="Scan logging with GPS coordinates" />
          <ContractRow name="PharmaChainBatch" address="0x555d8aFe1a2B7f1B04D24b26F12573e42Fc0f0fA" desc="Batch management, medicine grouping" />
        </div>
      </div>
    </div>
  );
}

function StatusCard({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className={`rounded-lg p-3 border text-sm ${
      ok
        ? "bg-green-500/5 border-green-500/20"
        : "bg-red-500/5 border-red-500/20"
    }`}>
      <div className="text-[10px] text-muted uppercase">{label}</div>
      <div className={`font-semibold mt-0.5 ${ok ? "text-green-400" : "text-red-400"}`}>
        {value}
      </div>
    </div>
  );
}

function MetricCard({ label, value, accent }: { label: string; value: number; accent?: string }) {
  const colorMap: Record<string, string> = {
    red: "text-red-400",
    yellow: "text-yellow-400",
    green: "text-green-400",
  };
  return (
    <div className="bg-surface rounded-lg p-4 border border-white/5">
      <div className="text-[10px] text-muted uppercase tracking-wider">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${accent ? colorMap[accent] : "text-white"}`}>
        {value}
      </div>
    </div>
  );
}

function ContractRow({ name, address, desc }: { name: string; address: string; desc: string }) {
  return (
    <div className="flex items-center gap-3 bg-primary rounded-lg px-4 py-2.5 border border-white/5">
      <div className="flex-1">
        <div className="text-sm font-semibold">{name}</div>
        <div className="text-[10px] text-muted">{desc}</div>
      </div>
      <code className="text-[10px] text-accent-light/60 font-mono">
        {address.slice(0, 6)}...{address.slice(-4)}
      </code>
    </div>
  );
}
