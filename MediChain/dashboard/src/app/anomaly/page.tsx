"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface AnomalyResult {
  is_anomaly: boolean;
  anomaly_score: number;
  iforest_score: number;
  autoencoder_score: number;
  anomaly_reasons: string[];
  recommended_severity: string;
  medicine_id?: number;
  transaction_id?: string;
  processing_time_ms: number;
}

const FIELD_INFO: Record<string, { label: string; desc: string; normal: string }> = {
  transfer_velocity_kmh: { label: "Transfer Velocity", desc: "Speed between two transfer locations (km/h)", normal: "20-80 km/h" },
  time_since_last_transfer_hours: { label: "Time Since Last Transfer", desc: "Hours elapsed since the previous custody transfer", normal: "24-168 hours" },
  transfer_count: { label: "Transfer Count", desc: "Total number of custody transfers this medicine has undergone", normal: "2-4 transfers" },
  scan_frequency_24h: { label: "Scan Frequency (24h)", desc: "Number of times scanned in the last 24 hours", normal: "1-3 scans" },
  unique_devices_24h: { label: "Unique Devices (24h)", desc: "Number of different scanning devices used in 24h", normal: "1-2 devices" },
  path_deviation_score: { label: "Path Deviation", desc: "How far the route deviates from the expected supply chain path (0 = on path, 1 = completely off)", normal: "0-0.2" },
  geographic_consistency: { label: "Geographic Consistency", desc: "Average distance between consecutive transfers (km) — higher = more erratic", normal: "50-500 km" },
  hour_of_day: { label: "Hour of Day", desc: "Hour when the transfer occurred (0-23)", normal: "8-20 (business hours)" },
  is_weekend: { label: "Weekend", desc: "Whether the transfer happened on a weekend (0 = weekday, 1 = weekend)", normal: "0 (weekday)" },
  days_since_manufacture: { label: "Days Since Manufacture", desc: "Days elapsed since the drug was manufactured", normal: "7-365 days" },
  batch_anomaly_rate: { label: "Batch Anomaly Rate", desc: "Historical anomaly rate for other medicines in this batch", normal: "0-0.02 (< 2%)" },
  actor_reputation_score: { label: "Actor Reputation", desc: "On-chain reputation score of the supply chain actor (0-1000)", normal: "400-1000" },
};

const SCENARIOS = [
  {
    name: "Legitimate Transfer",
    tag: "SAFE",
    tagColor: "text-green-400 border-green-500/30 bg-green-500/10",
    explanation: "A normal daytime transfer at reasonable speed (45 km/h), with consistent geographic routing, low batch anomaly rate, and a high-reputation actor. The AI should recognize this as completely normal.",
    values: {
      transfer_velocity_kmh: 45,
      time_since_last_transfer_hours: 48,
      transfer_count: 3,
      scan_frequency_24h: 2,
      unique_devices_24h: 1,
      path_deviation_score: 0.1,
      geographic_consistency: 120,
      hour_of_day: 14,
      is_weekend: 0,
      days_since_manufacture: 30,
      batch_anomaly_rate: 0.01,
      actor_reputation_score: 750,
    },
  },
  {
    name: "Suspicious Speed",
    tag: "MEDIUM",
    tagColor: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10",
    explanation: "The medicine moved at 600 km/h between locations — physically possible only by air freight, which is unusual for domestic pharma supply chains. Combined with a slight path deviation, this triggers a velocity_violation flag. A single rule triggers a warning but not necessarily a full anomaly.",
    values: {
      transfer_velocity_kmh: 600,
      time_since_last_transfer_hours: 12,
      transfer_count: 3,
      scan_frequency_24h: 2,
      unique_devices_24h: 1,
      path_deviation_score: 0.3,
      geographic_consistency: 400,
      hour_of_day: 10,
      is_weekend: 0,
      days_since_manufacture: 45,
      batch_anomaly_rate: 0.02,
      actor_reputation_score: 600,
    },
  },
  {
    name: "Night Weekend + Bad Actor",
    tag: "HIGH",
    tagColor: "text-orange-400 border-orange-500/30 bg-orange-500/10",
    explanation: "Transfer at 3 AM on a weekend by an actor with low reputation (200/1000). Legitimate pharma transfers almost never happen at 3 AM on weekends. The low-reputation actor amplifies suspicion. Two+ rule violations trigger an anomaly flag.",
    values: {
      transfer_velocity_kmh: 80,
      time_since_last_transfer_hours: 6,
      transfer_count: 5,
      scan_frequency_24h: 4,
      unique_devices_24h: 3,
      path_deviation_score: 0.15,
      geographic_consistency: 250,
      hour_of_day: 3,
      is_weekend: 1,
      days_since_manufacture: 60,
      batch_anomaly_rate: 0.05,
      actor_reputation_score: 200,
    },
  },
  {
    name: "Counterfeit Ring Pattern",
    tag: "CRITICAL",
    tagColor: "text-red-400 border-red-500/30 bg-red-500/10",
    explanation: "Every red flag is raised: impossible speed (900 km/h), 8 transfers (legitimate chains have 2-4), 6 unique devices scanning (drug being passed around), massive path deviation, 3 AM weekend transfer, expired manufacturing date (400 days), high batch contamination (25% of batch already flagged), and an extremely low-reputation actor. This pattern matches organized counterfeit distribution networks.",
    values: {
      transfer_velocity_kmh: 900,
      time_since_last_transfer_hours: 1.5,
      transfer_count: 8,
      scan_frequency_24h: 15,
      unique_devices_24h: 6,
      path_deviation_score: 0.9,
      geographic_consistency: 2000,
      hour_of_day: 3,
      is_weekend: 1,
      days_since_manufacture: 400,
      batch_anomaly_rate: 0.25,
      actor_reputation_score: 150,
    },
  },
  {
    name: "Expired Drug Diversion",
    tag: "HIGH",
    tagColor: "text-orange-400 border-orange-500/30 bg-orange-500/10",
    explanation: "A drug manufactured 500 days ago (well past typical 1-year shelf life) being transferred with excessive scan frequency and multiple devices — suggests someone is trying to move expired inventory through the supply chain quickly. The batch already has a 15% anomaly rate.",
    values: {
      transfer_velocity_kmh: 120,
      time_since_last_transfer_hours: 4,
      transfer_count: 6,
      scan_frequency_24h: 10,
      unique_devices_24h: 4,
      path_deviation_score: 0.4,
      geographic_consistency: 800,
      hour_of_day: 22,
      is_weekend: 0,
      days_since_manufacture: 500,
      batch_anomaly_rate: 0.15,
      actor_reputation_score: 350,
    },
  },
];

const REASON_EXPLANATIONS: Record<string, string> = {
  velocity_violation: "Transfer speed exceeds 500 km/h — physically suspicious for ground transport",
  path_deviation: "Route deviates significantly from expected supply chain path",
  excessive_transfers: "More than 5 custody transfers — legitimate chains rarely exceed 4",
  suspicious_timing: "Transfer occurred between 2-5 AM on a weekend",
  batch_contamination: "More than 10% of this batch has already been flagged as anomalous",
  low_reputation_actor: "Actor's on-chain reputation is below 300/1000",
};

export default function AnomalyPage() {
  const [values, setValues] = useState(SCENARIOS[0].values);
  const [activeScenario, setActiveScenario] = useState(0);
  const [result, setResult] = useState<AnomalyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const detect = () => {
    setLoading(true);
    setError("");
    api
      .post("/api/detect-anomaly", values)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const loadScenario = (index: number) => {
    setActiveScenario(index);
    setValues(SCENARIOS[index].values);
    setResult(null);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">Anomaly Detection</h1>
        <p className="text-sm text-muted">
          Isolation Forest + Autoencoder ensemble analyzes 12 supply chain features.
          Flags a transaction as anomalous when 2+ rule violations are triggered.
        </p>
      </div>

      {/* Scenario Selector */}
      <div className="mb-6">
        <h2 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Demo Scenarios</h2>
        <div className="flex flex-wrap gap-2">
          {SCENARIOS.map((s, i) => (
            <button
              key={i}
              onClick={() => loadScenario(i)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm transition-colors ${
                activeScenario === i
                  ? "border-accent-light/50 bg-accent-light/10 text-white"
                  : "border-white/10 text-muted hover:text-white hover:border-white/20"
              }`}
            >
              <span className={`text-[10px] px-1.5 py-0.5 rounded border ${s.tagColor}`}>{s.tag}</span>
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Scenario Explanation */}
      <div className="bg-surface rounded-xl p-4 border border-white/5 mb-6">
        <div className="flex items-start gap-3">
          <span className="text-lg mt-0.5">💡</span>
          <div>
            <h3 className="font-semibold text-sm mb-1">{SCENARIOS[activeScenario].name}</h3>
            <p className="text-xs text-muted leading-relaxed">{SCENARIOS[activeScenario].explanation}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div>
          <div className="bg-surface rounded-xl p-5 border border-white/5">
            <h2 className="font-semibold mb-4">12 Supply Chain Features</h2>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(values).map(([key, val]) => {
                const info = FIELD_INFO[key];
                return (
                  <div key={key}>
                    <label className="text-xs text-muted block mb-1">{info?.label || key}</label>
                    <input
                      type="number"
                      step="any"
                      value={val}
                      onChange={(e) =>
                        setValues((v) => ({ ...v, [key]: parseFloat(e.target.value) || 0 }))
                      }
                      className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
                    />
                    <div className="text-[10px] text-muted/60 mt-0.5">Normal: {info?.normal}</div>
                  </div>
                );
              })}
            </div>
            <button
              onClick={detect}
              disabled={loading}
              className="mt-4 w-full bg-accent text-white py-2.5 rounded-lg font-semibold text-sm disabled:opacity-50 hover:bg-accent/80 transition-colors"
            >
              {loading ? "Analyzing..." : "Run Anomaly Detection"}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div>
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 mb-4 text-sm">
              {error}
            </div>
          )}

          {result && (
            <div className="bg-surface rounded-xl p-5 border border-white/5">
              {/* Verdict */}
              <div className="flex items-center gap-3 mb-5">
                <div
                  className={`w-4 h-4 rounded-full ${
                    result.is_anomaly ? "bg-red-500 shadow-lg shadow-red-500/30" : "bg-green-500 shadow-lg shadow-green-500/30"
                  }`}
                />
                <h2 className={`font-bold text-lg ${result.is_anomaly ? "text-red-400" : "text-green-400"}`}>
                  {result.is_anomaly ? "ANOMALY DETECTED" : "Normal Transaction"}
                </h2>
              </div>

              {/* Scores */}
              <div className="grid grid-cols-2 gap-3 mb-5">
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-[10px] text-muted uppercase">Composite Score</div>
                  <div className={`text-3xl font-bold ${
                    result.anomaly_score > 0.7 ? "text-red-400"
                    : result.anomaly_score > 0.4 ? "text-yellow-400"
                    : "text-green-400"
                  }`}>
                    {(result.anomaly_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-[10px] text-muted uppercase">Severity</div>
                  <div className={`text-3xl font-bold capitalize ${
                    result.recommended_severity === "Critical" ? "text-red-400"
                    : result.recommended_severity === "High" ? "text-orange-400"
                    : result.recommended_severity === "Medium" ? "text-yellow-400"
                    : "text-green-400"
                  }`}>
                    {result.recommended_severity || "Low"}
                  </div>
                </div>
              </div>

              {/* Anomaly Reasons */}
              {result.anomaly_reasons?.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                    Rule Violations ({result.anomaly_reasons.length}/6 rules triggered)
                  </h3>
                  <div className="space-y-2">
                    {result.anomaly_reasons.map((r, i) => (
                      <div
                        key={i}
                        className="bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2"
                      >
                        <div className="text-xs font-semibold text-red-400">{r.replace(/_/g, " ").toUpperCase()}</div>
                        <div className="text-[10px] text-muted mt-0.5">
                          {REASON_EXPLANATIONS[r] || "Rule-based heuristic violation"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.anomaly_reasons?.length === 0 && (
                <div className="mb-4 bg-green-500/5 border border-green-500/20 rounded-lg px-3 py-2">
                  <div className="text-xs text-green-400">No rule violations triggered</div>
                  <div className="text-[10px] text-muted mt-0.5">All 12 features are within normal parameters</div>
                </div>
              )}

              {/* How it works */}
              <div className="text-[10px] text-muted border-t border-white/5 pt-3 mt-3">
                <span className="font-semibold">How scoring works:</span> Anomaly is flagged when EITHER ML model detects an outlier
                OR 2+ rule-based violations are triggered. Score = ratio of violations (min 0.3 if anomalous).
                <span className="ml-2">Processed in {String(result.processing_time_ms)}ms</span>
              </div>
            </div>
          )}

          {!result && !error && (
            <div className="bg-surface rounded-xl p-8 border border-white/5 text-center">
              <div className="text-4xl mb-3">🔬</div>
              <div className="text-sm text-muted">
                Select a scenario and click <span className="text-white font-semibold">Run Anomaly Detection</span> to see the AI analysis
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
