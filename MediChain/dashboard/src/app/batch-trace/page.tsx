"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import type { Transfer, Origin } from "./BatchTraceMap";

const BatchTraceMap = dynamic(() => import("./BatchTraceMap"), { ssr: false });

interface BatchSummary {
  batch_id: string;
  medicine_name: string;
  manufacturer: string;
  total_transfers: number;
  anomaly_count: number;
}

interface TraceResult {
  batch_id: string;
  origin: Origin;
  chain: Transfer[];
  total_transfers: number;
  anomaly_count: number;
  anomaly_rate: number;
  risk_level: string;
  affected_locations: Array<Record<string, unknown>>;
  actors_involved: string[];
  medicine_name: string;
  manufacturer: string;
  processing_time_ms: number;
}

interface CommonOriginResult {
  batches: Array<{ batch_id: string; origin: Origin; chain: Transfer[] } & Record<string, unknown>>;
  common_origins: Array<{
    factory: string;
    coords: [number, number];
    state: string;
    batch_count: number;
    batch_ids: string[];
    affected_locations: Array<Record<string, unknown>>;
  }>;
  pattern_detected: boolean;
  alert: string;
  processing_time_ms: number;
}

const RISK_COLORS: Record<string, string> = {
  critical: "#FF2D55",
  high: "#FF6B35",
  medium: "#FFB800",
  low: "#30D158",
};

const ANOMALY_LABELS: Record<string, string> = {
  velocity_violation: "Speed Violation",
  path_deviation: "Path Deviation",
  duplicate_scan: "Duplicate Scan",
  reverse_flow: "Reverse Flow",
  geographic_impossibility: "Impossible Route",
  excessive_transfers: "Excessive Transfers",
  suspicious_timing: "Suspicious Timing",
  hotspot_routing: "Hotspot Routing",
};

function formatTimestamp(ts: string): string {
  if (!ts) return "N/A";
  try {
    return new Date(ts).toLocaleString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

export default function BatchTracePage() {
  const [batchList, setBatchList] = useState<BatchSummary[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [batchId, setBatchId] = useState("");
  const [traceResult, setTraceResult] = useState<TraceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedStep, setSelectedStep] = useState<number | null>(null);

  // Common origin mode
  const [compareMode, setCompareMode] = useState(false);
  const [selectedBatches, setSelectedBatches] = useState<Set<string>>(new Set());
  const [commonResult, setCommonResult] = useState<CommonOriginResult | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // Dropdown open state
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Fetch batch list on mount
  useEffect(() => {
    api
      .get("/api/batch-trace/batches")
      .then((data: { flagged_batches: BatchSummary[] }) => {
        setBatchList(data.flagged_batches || []);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setListLoading(false));
  }, []);

  const traceBatch = (id?: string) => {
    const target = id || batchId;
    if (!target) return;
    setLoading(true);
    setError("");
    setTraceResult(null);
    setSelectedStep(null);
    setCompareMode(false);
    setCommonResult(null);
    api
      .get(`/api/batch-trace/${target}`)
      .then((data: TraceResult) => {
        setTraceResult(data);
        setBatchId(target);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const toggleBatchSelection = (bid: string) => {
    setSelectedBatches((prev) => {
      const next = new Set(prev);
      if (next.has(bid)) next.delete(bid);
      else if (next.size < 10) next.add(bid);
      return next;
    });
  };

  const findCommonOrigin = () => {
    if (selectedBatches.size < 2) return;
    setCompareLoading(true);
    setError("");
    setCommonResult(null);
    api
      .post("/api/batch-trace/common-origin", {
        batch_ids: Array.from(selectedBatches),
      })
      .then((data: CommonOriginResult) => setCommonResult(data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setCompareLoading(false));
  };

  const riskColor = traceResult ? RISK_COLORS[traceResult.risk_level] || "#6B7280" : "#6B7280";

  // Filter batch list for search
  const filteredBatches = batchList.filter(
    (b) =>
      b.batch_id.toLowerCase().includes(batchId.toLowerCase()) ||
      b.medicine_name.toLowerCase().includes(batchId.toLowerCase()) ||
      b.manufacturer.toLowerCase().includes(batchId.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Batch Trace</h1>
          <p className="text-muted text-sm mt-1">
            Trace drug batches through the supply chain and detect common origins
          </p>
        </div>
        {traceResult && (
          <span className="text-xs text-muted">
            Traced in {traceResult.processing_time_ms}ms
          </span>
        )}
      </div>

      {/* Search Bar */}
      <div className="bg-surface rounded-xl p-4 border border-white/5">
        <div className="flex gap-3 items-center">
          <div className="relative flex-1">
            <input
              type="text"
              value={batchId}
              onChange={(e) => {
                setBatchId(e.target.value);
                setDropdownOpen(true);
              }}
              onFocus={() => setDropdownOpen(true)}
              placeholder="Search by batch ID, medicine, or manufacturer..."
              className="w-full bg-primary border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder:text-muted/50 focus:outline-none focus:border-accent/50"
            />
            {dropdownOpen && batchId && filteredBatches.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-surface border border-white/10 rounded-lg max-h-64 overflow-y-auto z-50 shadow-xl">
                {filteredBatches.slice(0, 15).map((b) => (
                  <button
                    key={b.batch_id}
                    onClick={() => {
                      setDropdownOpen(false);
                      traceBatch(b.batch_id);
                    }}
                    className="w-full text-left px-4 py-2.5 hover:bg-white/5 flex items-center justify-between text-sm border-b border-white/5 last:border-0"
                  >
                    <div>
                      <span className="font-mono text-white">{b.batch_id}</span>
                      <span className="text-muted ml-2">{b.medicine_name}</span>
                      <span className="text-muted/60 ml-2 text-xs">{b.manufacturer}</span>
                    </div>
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{
                        background: `${b.anomaly_count >= 6 ? "#FF2D55" : b.anomaly_count >= 3 ? "#FF6B35" : "#FFB800"}20`,
                        color: b.anomaly_count >= 6 ? "#FF2D55" : b.anomaly_count >= 3 ? "#FF6B35" : "#FFB800",
                      }}
                    >
                      {b.anomaly_count} anomalies
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={() => traceBatch()}
            disabled={!batchId || loading}
            className="bg-accent hover:bg-accent/80 disabled:opacity-40 text-white px-6 py-2.5 rounded-lg font-semibold text-sm transition-colors"
          >
            {loading ? "Tracing..." : "Trace"}
          </button>
          <button
            onClick={() => {
              setCompareMode(!compareMode);
              if (compareMode) {
                setSelectedBatches(new Set());
                setCommonResult(null);
              }
            }}
            className={`px-4 py-2.5 rounded-lg font-semibold text-sm transition-colors border ${
              compareMode
                ? "bg-red-500/20 border-red-500/30 text-red-400"
                : "bg-primary border-white/10 text-muted hover:text-white"
            }`}
          >
            {compareMode ? "Exit Compare" : "Compare Batches"}
          </button>
        </div>

        {/* Quick presets */}
        {!traceResult && !compareMode && (
          <div className="flex gap-2 mt-3 flex-wrap">
            <span className="text-xs text-muted/60 py-1">Quick demo:</span>
            {batchList.slice(0, 5).map((b) => (
              <button
                key={b.batch_id}
                onClick={() => traceBatch(b.batch_id)}
                className="text-xs bg-primary border border-white/10 hover:border-accent/30 rounded px-2.5 py-1 text-muted hover:text-white transition-colors"
              >
                {b.batch_id}
              </button>
            ))}
            {listLoading && <span className="text-xs text-muted/40">Loading batches...</span>}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Compare mode panel */}
      {compareMode && (
        <div className="bg-surface rounded-xl p-4 border border-white/5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm">
              Select batches to compare ({selectedBatches.size} selected)
            </h3>
            <button
              onClick={findCommonOrigin}
              disabled={selectedBatches.size < 2 || compareLoading}
              className="bg-red-500 hover:bg-red-600 disabled:opacity-40 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors"
            >
              {compareLoading ? "Analyzing..." : "Find Common Origin"}
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-48 overflow-y-auto">
            {batchList.slice(0, 24).map((b) => (
              <button
                key={b.batch_id}
                onClick={() => toggleBatchSelection(b.batch_id)}
                className={`text-left p-2.5 rounded-lg border text-xs transition-colors ${
                  selectedBatches.has(b.batch_id)
                    ? "bg-accent/20 border-accent/40 text-white"
                    : "bg-primary border-white/5 text-muted hover:border-white/20"
                }`}
              >
                <div className="font-mono font-semibold truncate">{b.batch_id}</div>
                <div className="truncate text-muted/70">{b.medicine_name}</div>
                <div className="truncate text-muted/50">{b.manufacturer}</div>
              </button>
            ))}
          </div>

          {/* Common origin result */}
          {commonResult && (
            <div className="space-y-3 pt-2 border-t border-white/5">
              {commonResult.pattern_detected ? (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-red-400 font-bold text-sm">PATTERN DETECTED</span>
                  </div>
                  <p className="text-sm text-red-300">{commonResult.alert}</p>
                  <div className="mt-3 space-y-2">
                    {commonResult.common_origins.map((co, i) => (
                      <div key={i} className="bg-red-500/5 rounded-lg p-3 text-sm">
                        <span className="font-semibold text-white">{co.factory}</span>
                        <span className="text-muted ml-2">({co.state})</span>
                        <span className="text-red-400 ml-2">
                          {co.batch_count} flagged batches
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-sm text-green-300">
                  No common origin pattern detected across the selected batches.
                </div>
              )}
              <span className="text-xs text-muted/50">
                Analyzed in {commonResult.processing_time_ms}ms
              </span>
            </div>
          )}
        </div>
      )}

      {/* Main content: Map + Sidebar */}
      {(traceResult || commonResult) && (
        <div className="flex gap-4" style={{ height: "calc(100vh - 360px)", minHeight: 500 }}>
          {/* Map */}
          <div className="flex-1 bg-surface rounded-xl border border-white/5 overflow-hidden">
            <BatchTraceMap
              chain={traceResult?.chain || []}
              origin={traceResult?.origin || null}
              selectedStep={selectedStep}
              onStepClick={setSelectedStep}
              commonOrigins={commonResult?.common_origins}
              multiChains={
                commonResult
                  ? commonResult.batches.map((b) => ({
                      batch_id: b.batch_id,
                      chain: (b.chain || []) as Transfer[],
                      origin: (b.origin || { actor: "", coords: [0, 0], state: "" }) as Origin,
                    }))
                  : undefined
              }
            />
          </div>

          {/* Sidebar */}
          {traceResult && (
            <div className="w-80 flex flex-col gap-3 overflow-y-auto">
              {/* Batch info */}
              <div className="bg-surface rounded-xl p-4 border border-white/5 space-y-3">
                <h3 className="font-semibold text-sm text-muted/80 uppercase tracking-wider">
                  Batch Info
                </h3>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs text-muted/60">Batch ID</span>
                    <p className="font-mono text-sm font-semibold">{traceResult.batch_id}</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted/60">Medicine</span>
                    <p className="text-sm">{traceResult.medicine_name || "Unknown"}</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted/60">Manufacturer</span>
                    <p className="text-sm">{traceResult.manufacturer || "Unknown"}</p>
                  </div>
                  <div>
                    <span className="text-xs text-muted/60">Origin</span>
                    <p className="text-sm">
                      {traceResult.origin?.actor || "Unknown"}{" "}
                      <span className="text-muted/60">({traceResult.origin?.state})</span>
                    </p>
                  </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-primary rounded-lg p-2.5 border border-white/5 text-center">
                    <div className="text-lg font-bold">{traceResult.total_transfers}</div>
                    <div className="text-xs text-muted/60">Transfers</div>
                  </div>
                  <div className="bg-primary rounded-lg p-2.5 border border-white/5 text-center">
                    <div
                      className="text-lg font-bold"
                      style={{ color: traceResult.anomaly_count > 0 ? "#FF2D55" : "#30D158" }}
                    >
                      {traceResult.anomaly_count}
                    </div>
                    <div className="text-xs text-muted/60">Anomalies</div>
                  </div>
                </div>

                {/* Risk badge */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted/60">Risk Level:</span>
                  <span
                    className="text-xs font-bold px-2.5 py-1 rounded-full uppercase"
                    style={{
                      background: `${riskColor}20`,
                      color: riskColor,
                    }}
                  >
                    {traceResult.risk_level}
                  </span>
                  <span className="text-xs text-muted/40 ml-auto">
                    {(traceResult.anomaly_rate * 100).toFixed(0)}% anomaly rate
                  </span>
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-surface rounded-xl p-4 border border-white/5 flex-1 overflow-y-auto">
                <h3 className="font-semibold text-sm text-muted/80 uppercase tracking-wider mb-3">
                  Supply Chain Timeline
                </h3>
                <div className="space-y-1">
                  {traceResult.chain.map((t) => (
                    <button
                      key={t.step}
                      onClick={() =>
                        setSelectedStep(selectedStep === t.step ? null : t.step)
                      }
                      className={`w-full text-left rounded-lg p-3 transition-colors border-l-[3px] ${
                        selectedStep === t.step
                          ? "bg-white/10 border-accent"
                          : t.is_anomaly
                          ? "bg-red-500/5 border-red-500/60 hover:bg-red-500/10"
                          : "bg-primary border-transparent hover:bg-white/5"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-mono text-muted/50">Step {t.step}</span>
                        {t.is_anomaly && (
                          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">
                            {ANOMALY_LABELS[t.anomaly_type] || t.anomaly_type}
                          </span>
                        )}
                      </div>
                      <div className="text-sm">
                        <span className="text-white font-medium">{t.from_actor}</span>
                        <span className="text-muted mx-1.5">&rarr;</span>
                        <span className="text-white font-medium">{t.to_actor}</span>
                      </div>
                      <div className="text-xs text-muted/50 mt-1">
                        {t.from_state} &rarr; {t.to_state}
                      </div>
                      <div className="text-xs text-muted/40 mt-0.5">
                        {formatTimestamp(t.timestamp)}
                        {t.transfer_velocity_kmh > 0 && (
                          <span className="ml-2">
                            {t.transfer_velocity_kmh.toFixed(0)} km/h
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Actors */}
              <div className="bg-surface rounded-xl p-4 border border-white/5">
                <h3 className="font-semibold text-sm text-muted/80 uppercase tracking-wider mb-2">
                  Actors Involved
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {traceResult.actors_involved.map((a) => (
                    <span
                      key={a}
                      className="text-xs px-2 py-1 rounded-full bg-primary border border-white/5 text-muted"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!traceResult && !commonResult && !loading && !compareMode && (
        <div className="bg-surface rounded-xl border border-white/5 p-16 text-center">
          <div className="text-4xl mb-4 opacity-30">&#128270;</div>
          <h3 className="text-lg font-semibold text-muted/80 mb-2">
            Select a batch to trace
          </h3>
          <p className="text-sm text-muted/50 max-w-md mx-auto">
            Search for a batch ID above or click one of the quick demo buttons to trace
            a drug batch through the supply chain. Anomalous transfers will be highlighted.
          </p>
        </div>
      )}
    </div>
  );
}
