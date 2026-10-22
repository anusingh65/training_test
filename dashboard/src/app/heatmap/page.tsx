"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";

const HeatmapMap = dynamic(() => import("./Map"), { ssr: false });

interface HeatmapData {
  heatmap_points: number[][];
  clusters: Array<Record<string, unknown>>;
  predicted_hotspots: Array<Record<string, unknown>>;
  corridors?: Array<Record<string, unknown>>;
  known_hotspot_activity?: Array<Record<string, unknown>>;
  state_risk?: Record<string, Record<string, unknown>>;
  stats: Record<string, unknown>;
  processing_time_ms: number;
}

interface ZoneRisk {
  risk_level: string;
  risk_score?: number;
  state?: string;
  nearest_cluster?: Record<string, unknown>;
  nearest_hotspot?: string;
  hotspot_distance_km?: number;
  cluster_distance_km?: number;
  distance_km?: number;
}

const RISK_COLORS: Record<string, string> = {
  critical: "#FF2D55",
  high: "#FF6B35",
  medium: "#FFB800",
  elevated: "#FF9500",
  low: "#30D158",
};

const PRESET_LOCATIONS = [
  { name: "Bhagirath Palace, Delhi", lat: "28.6567", lng: "77.2306" },
  { name: "Crawford Market, Mumbai", lat: "18.9476", lng: "72.8335" },
  { name: "Agra Wholesale", lat: "27.1767", lng: "78.0081" },
  { name: "Guwahati, Assam", lat: "26.1445", lng: "91.7362" },
  { name: "Patna, Bihar", lat: "25.6093", lng: "85.1376" },
];

export default function HeatmapPage() {
  const [data, setData] = useState<HeatmapData | null>(null);
  const [timeWindow, setTimeWindow] = useState("90d");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [zoneResult, setZoneResult] = useState<ZoneRisk | null>(null);
  const [zoneLat, setZoneLat] = useState("28.6567");
  const [zoneLng, setZoneLng] = useState("77.2306");
  const [sidebarTab, setSidebarTab] = useState<"clusters" | "hotspots" | "states" | "corridors">("clusters");

  const fetchData = () => {
    setLoading(true);
    setError("");
    api
      .get(`/api/heatmap-data?time_window=${timeWindow}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [timeWindow]);

  const checkZone = () => {
    api
      .get(`/api/heatmap-zone-risk?lat=${zoneLat}&lng=${zoneLng}`)
      .then(setZoneResult)
      .catch((e) => setError(e.message));
  };

  const stats = data?.stats || {};
  const stateRisk = data?.state_risk || {};
  const hotspotActivity = (data?.known_hotspot_activity || []) as Array<Record<string, unknown>>;
  const corridors = (data?.corridors || []) as Array<Record<string, unknown>>;
  const predictedHotspots = (data?.predicted_hotspots || []) as Array<Record<string, unknown>>;
  const emergingCount = predictedHotspots.filter((h) => h.is_emerging).length;

  const statesAtRisk = Object.entries(stateRisk)
    .filter(([, v]) => v.risk_level !== "low")
    .sort((a, b) => ((b[1].risk_score as number) || 0) - ((a[1].risk_score as number) || 0));

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold tracking-tight">Threat Heatmap</h1>
          <div className="flex gap-1 bg-surface rounded-lg p-0.5">
            {["1h", "6h", "24h", "7d", "30d", "90d", "all"].map((w) => (
              <button
                key={w}
                onClick={() => setTimeWindow(w)}
                className={`px-2.5 py-1 text-xs rounded-md transition-all ${
                  timeWindow === w ? "bg-accent text-white font-semibold" : "text-muted hover:text-white"
                }`}
              >
                {w}
              </button>
            ))}
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="bg-accent/20 text-accent-light px-3 py-1 rounded-lg text-xs font-medium hover:bg-accent/30 transition-all disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {/* Stat pills */}
        {data && (
          <div className="flex gap-3">
            <StatPill label="Points" value={String(stats.total_events || stats.total_points || 0)} />
            <StatPill label="Clusters" value={String(stats.cluster_count || 0)} color="#FF6B35" />
            <StatPill label="Predictions" value={String(stats.hotspot_predictions || emergingCount)} color="#A855F7" />
            <StatPill label="States at Risk" value={String(stats.states_at_risk || statesAtRisk.length)} color="#FF2D55" />
          </div>
        )}
      </div>

      {error && (
        <div className="mx-4 mt-2 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-2.5 text-xs">
          {error}
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          {data && (
            <HeatmapMap
              points={data.heatmap_points}
              clusters={data.clusters as never[]}
              corridors={corridors as never[]}
              knownHotspots={hotspotActivity as never[]}
              predictedHotspots={predictedHotspots as never[]}
            />
          )}
          {!data && !loading && (
            <div className="absolute inset-0 flex items-center justify-center text-muted text-sm">
              No data loaded. Connect to the backend to view the heatmap.
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="w-80 border-l border-white/5 flex flex-col bg-surface/50 overflow-hidden">
          {/* Zone risk checker */}
          <div className="p-3 border-b border-white/5">
            <div className="text-xs font-semibold text-white/70 mb-2">Zone Risk Scanner</div>
            <div className="flex gap-1.5 mb-2">
              <input
                value={zoneLat}
                onChange={(e) => setZoneLat(e.target.value)}
                placeholder="Lat"
                className="bg-primary border border-white/10 rounded-md px-2 py-1.5 text-xs flex-1 focus:border-accent focus:outline-none"
              />
              <input
                value={zoneLng}
                onChange={(e) => setZoneLng(e.target.value)}
                placeholder="Lng"
                className="bg-primary border border-white/10 rounded-md px-2 py-1.5 text-xs flex-1 focus:border-accent focus:outline-none"
              />
              <button onClick={checkZone} className="bg-accent text-white px-3 py-1.5 rounded-md text-xs font-medium">
                Scan
              </button>
            </div>
            {/* Preset buttons */}
            <div className="flex flex-wrap gap-1 mb-2">
              {PRESET_LOCATIONS.map((loc) => (
                <button
                  key={loc.name}
                  onClick={() => {
                    setZoneLat(loc.lat);
                    setZoneLng(loc.lng);
                  }}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-muted hover:text-white hover:bg-white/10 transition-all"
                >
                  {loc.name.split(",")[0]}
                </button>
              ))}
            </div>
            {zoneResult && (
              <div className="bg-primary rounded-lg p-2.5 border border-white/5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-muted uppercase tracking-wider">Risk Level</span>
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded-full"
                    style={{
                      background: (RISK_COLORS[zoneResult.risk_level] || "#30D158") + "20",
                      color: RISK_COLORS[zoneResult.risk_level] || "#30D158",
                    }}
                  >
                    {zoneResult.risk_level.toUpperCase()}
                  </span>
                </div>
                {zoneResult.risk_score != null && (
                  <div className="mt-1.5">
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${zoneResult.risk_score * 100}%`,
                          background: RISK_COLORS[zoneResult.risk_level] || "#30D158",
                        }}
                      />
                    </div>
                  </div>
                )}
                <div className="mt-2 space-y-0.5 text-[11px]">
                  {zoneResult.state && (
                    <div className="text-muted">
                      State: <span className="text-white/80">{zoneResult.state}</span>
                    </div>
                  )}
                  {zoneResult.nearest_hotspot && (
                    <div className="text-muted">
                      Nearest hotspot: <span className="text-white/80">{zoneResult.nearest_hotspot}</span>{" "}
                      ({zoneResult.hotspot_distance_km?.toFixed(1)} km)
                    </div>
                  )}
                  {zoneResult.cluster_distance_km != null && (
                    <div className="text-muted">
                      Nearest cluster: <span className="text-white/80">{zoneResult.cluster_distance_km.toFixed(1)} km</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar tabs */}
          <div className="flex border-b border-white/5">
            {(["clusters", "hotspots", "states", "corridors"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setSidebarTab(tab)}
                className={`flex-1 py-2 text-[10px] uppercase tracking-wider font-medium transition-all ${
                  sidebarTab === tab
                    ? "text-white border-b-2 border-accent"
                    : "text-muted hover:text-white/60"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {sidebarTab === "clusters" && data && (
              <>
                {data.clusters.length === 0 && <EmptyState text="No clusters detected" />}
                {(data.clusters as Array<Record<string, unknown>>).slice(0, 50).map((c, i) => {
                  const severity = (c.risk_label as string)?.includes("Critical")
                    ? "critical"
                    : (c.risk_label as string)?.includes("High")
                    ? "high"
                    : "medium";
                  return (
                    <div key={i} className="bg-primary rounded-lg p-2.5 border border-white/5">
                      <div className="flex items-start justify-between">
                        <div>
                          <span
                            className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                            style={{
                              background: (RISK_COLORS[severity] || "#FFB800") + "20",
                              color: RISK_COLORS[severity] || "#FFB800",
                            }}
                          >
                            {(c.risk_label as string) || severity}
                          </span>
                          {c.state ? <span className="text-[10px] text-muted ml-1.5">{c.state as string}</span> : null}
                        </div>
                        <span className="text-[10px] font-mono text-muted">
                          {((c.risk_score as number) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="mt-1.5 flex gap-3 text-[10px] text-muted">
                        <span>{c.event_count as number} events</span>
                        <span>{String(c.recent_event_count ?? c.recent_count ?? "—")} recent</span>
                        <span>{((c.radius_km as number) || 0).toFixed(1)} km</span>
                      </div>
                      {c.nearest_known_hotspot ? (
                        <div className="mt-1 text-[10px] text-purple-light">
                          Near {c.nearest_known_hotspot as string}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
                {/* Emerging hotspots */}
                {emergingCount > 0 && (
                  <>
                    <div className="text-[10px] font-semibold text-purple-light uppercase tracking-wider mt-3 mb-1 px-1">
                      Emerging Hotspots ({emergingCount})
                    </div>
                    {predictedHotspots
                      .filter((h) => h.is_emerging)
                      .map((h, i) => (
                        <div key={`pred-${i}`} className="bg-purple-500/10 rounded-lg p-2.5 border border-purple-500/20">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold text-purple-light">
                              {(h.state as string) || "Unknown"}
                            </span>
                            <span className="text-[10px] font-mono text-purple-light">
                              +{((h.growth_pct as number) || 0).toFixed(0)}%
                            </span>
                          </div>
                          <div className="mt-1 text-[10px] text-muted">
                            {h.current_count as number} → ~{((h.predicted_count_2w as number) || 0).toFixed(0)} in 2wk
                          </div>
                          {h.alert ? (
                            <div className="mt-1 text-[10px] text-purple-400/70 leading-tight">
                              {(h.alert as string).slice(0, 120)}
                            </div>
                          ) : null}
                        </div>
                      ))}
                  </>
                )}
              </>
            )}

            {sidebarTab === "hotspots" && (
              <>
                {hotspotActivity.length === 0 && <EmptyState text="No hotspot data" />}
                {hotspotActivity.map((hs, i) => {
                  const trend = hs.trend as string;
                  const trendCol = trend === "increasing" ? "#FF2D55" : trend === "decreasing" ? "#30D158" : "#94A3B8";
                  const riskLevel = (hs.effective_risk_level || hs.baseline_risk) as string;
                  return (
                    <div key={i} className="bg-primary rounded-lg p-2.5 border border-white/5">
                      <div className="flex items-start justify-between">
                        <div className="text-xs font-medium">{hs.name as string}</div>
                        <span
                          className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                          style={{
                            background: (RISK_COLORS[riskLevel] || "#FFB800") + "20",
                            color: RISK_COLORS[riskLevel] || "#FFB800",
                          }}
                        >
                          {riskLevel}
                        </span>
                      </div>
                      <div className="text-[10px] text-muted mt-0.5">{hs.state as string}</div>
                      <div className="mt-1.5 flex gap-3 text-[10px]">
                        <span className="text-muted">
                          7d: <span className="text-white/80 font-medium">{hs.recent_events as number}</span>
                        </span>
                        <span className="text-muted">
                          30d: <span className="text-white/80">{hs.monthly_events as number}</span>
                        </span>
                        <span style={{ color: trendCol }} className="font-medium">
                          {trend === "increasing" ? "▲" : trend === "decreasing" ? "▼" : "●"} {trend}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </>
            )}

            {sidebarTab === "states" && (
              <>
                {statesAtRisk.length === 0 && <EmptyState text="No states at risk" />}
                {statesAtRisk.map(([state, info]) => (
                  <div key={state} className="bg-primary rounded-lg p-2.5 border border-white/5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{state}</span>
                      <span
                        className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                        style={{
                          background: (RISK_COLORS[info.risk_level as string] || "#FFB800") + "20",
                          color: RISK_COLORS[info.risk_level as string] || "#FFB800",
                        }}
                      >
                        {(info.risk_level as string).toUpperCase()}
                      </span>
                    </div>
                    <div className="mt-1.5">
                      <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${((info.risk_score as number) || 0) * 100}%`,
                            background: RISK_COLORS[info.risk_level as string] || "#FFB800",
                          }}
                        />
                      </div>
                    </div>
                    <div className="mt-1.5 flex gap-3 text-[10px] text-muted">
                      <span>{info.cluster_count as number} clusters</span>
                      <span>{info.flagged_events as number} events</span>
                      {(info.known_hotspots_active || info.hotspots_active) ? (
                        <span>{(info.known_hotspots_active || info.hotspots_active) as number} hotspots</span>
                      ) : null}
                    </div>
                  </div>
                ))}
              </>
            )}

            {sidebarTab === "corridors" && (
              <>
                {corridors.length === 0 && <EmptyState text="No corridor data. Requires backend route analysis." />}
                {corridors.length > 0 && (
                  <div className="text-[10px] text-muted/60 px-1 mb-1">
                    Routes rendered using OSRM road data
                  </div>
                )}
                {(corridors as Array<Record<string, unknown>>).slice(0, 30).map((c, i) => {
                  const riskLevel = c.risk_level as string;
                  return (
                    <div key={i} className="bg-primary rounded-lg p-2.5 border border-white/5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium">
                          {c.from_state as string} → {c.to_state as string}
                        </span>
                        <span
                          className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                          style={{
                            background: (RISK_COLORS[riskLevel] || "#FFB800") + "20",
                            color: RISK_COLORS[riskLevel] || "#FFB800",
                          }}
                        >
                          {((c.corridor_risk as number) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="mt-1 flex gap-3 text-[10px] text-muted">
                        <span>{c.anomaly_count as number}/{c.total_shipments as number} anomalies</span>
                        <span>{((c.distance_km as number) || 0).toFixed(0)} km</span>
                      </div>
                      {(c.anomaly_types as string[])?.length > 0 && (
                        <div className="mt-1 text-[10px] text-muted/60">
                          {(c.anomaly_types as string[]).join(", ")}
                        </div>
                      )}
                    </div>
                  );
                })}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatPill({ label, value, color = "#3B82F6" }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center gap-2 bg-surface/80 rounded-lg px-3 py-1.5 border border-white/5">
      <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      <span className="text-[10px] text-muted">{label}</span>
      <span className="text-xs font-bold" style={{ color }}>
        {value}
      </span>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center h-20 text-muted text-xs">
      {text}
    </div>
  );
}
