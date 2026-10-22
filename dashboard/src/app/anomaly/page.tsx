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

const DEFAULT_VALUES = {
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
};

const ANOMALOUS_VALUES = {
  transfer_velocity_kmh: 800,
  time_since_last_transfer_hours: 2,
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
};

const FIELD_INFO: Record<string, string> = {
  transfer_velocity_kmh: "Speed between transfers (normal: 20-80)",
  time_since_last_transfer_hours: "Hours since last transfer (normal: 24-168)",
  transfer_count: "Total transfers (normal: 2-4)",
  scan_frequency_24h: "Scans in last 24h (normal: 1-3)",
  unique_devices_24h: "Unique devices in 24h (normal: 1-2)",
  path_deviation_score: "Path deviation 0-1 (normal: 0-0.2)",
  geographic_consistency: "Avg distance km (normal: 50-500)",
  hour_of_day: "Hour 0-23 (normal: 8-20)",
  is_weekend: "0 or 1",
  days_since_manufacture: "Days since mfg (normal: 7-365)",
  batch_anomaly_rate: "Batch anomaly rate (normal: 0-0.02)",
  actor_reputation_score: "Reputation 0-1000 (normal: 400-1000)",
};

export default function AnomalyPage() {
  const [values, setValues] = useState(DEFAULT_VALUES);
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

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold">Anomaly Detection</h1>
        <button
          onClick={() => setValues(DEFAULT_VALUES)}
          className="text-sm text-muted hover:text-white border border-white/10 px-3 py-1 rounded"
        >
          Normal Values
        </button>
        <button
          onClick={() => setValues(ANOMALOUS_VALUES)}
          className="text-sm text-red-400 hover:text-red-300 border border-red-500/30 px-3 py-1 rounded"
        >
          Anomalous Values
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="bg-surface rounded-xl p-5 border border-white/5">
            <h2 className="font-semibold mb-4">12 Supply Chain Features</h2>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(values).map(([key, val]) => (
                <div key={key}>
                  <label className="text-xs text-muted block mb-1">{key}</label>
                  <input
                    type="number"
                    step="any"
                    value={val}
                    onChange={(e) =>
                      setValues((v) => ({ ...v, [key]: parseFloat(e.target.value) || 0 }))
                    }
                    className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
                  />
                  <div className="text-[10px] text-muted/60 mt-0.5">{FIELD_INFO[key]}</div>
                </div>
              ))}
            </div>
            <button
              onClick={detect}
              disabled={loading}
              className="mt-4 w-full bg-accent text-white py-2 rounded font-semibold text-sm disabled:opacity-50"
            >
              {loading ? "Detecting..." : "Detect Anomaly"}
            </button>
          </div>
        </div>

        <div>
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 mb-4 text-sm">
              {error}
            </div>
          )}

          {result && (
            <div className="bg-surface rounded-xl p-5 border border-white/5">
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-4 h-4 rounded-full ${
                    result.is_anomaly ? "bg-red-500" : "bg-green-500"
                  }`}
                />
                <h2 className="font-semibold text-lg">
                  {result.is_anomaly ? "ANOMALY DETECTED" : "Normal Transaction"}
                </h2>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-xs text-muted">Anomaly Score</div>
                  <div className="text-2xl font-bold text-yellow-400">
                    {result.anomaly_score.toFixed(3)}
                  </div>
                </div>
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-xs text-muted">Severity</div>
                  <div
                    className={`text-2xl font-bold ${
                      result.recommended_severity === "critical"
                        ? "text-red-400"
                        : result.recommended_severity === "high"
                        ? "text-orange-400"
                        : result.recommended_severity === "medium"
                        ? "text-yellow-400"
                        : "text-green-400"
                    }`}
                  >
                    {result.recommended_severity || "none"}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-xs text-muted">IForest Score</div>
                  <div className="font-mono">{result.iforest_score?.toFixed(4)}</div>
                </div>
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-xs text-muted">Autoencoder Score</div>
                  <div className="font-mono">
                    {result.autoencoder_score?.toFixed(4)}
                  </div>
                </div>
              </div>

              {result.anomaly_reasons?.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Reasons</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.anomaly_reasons.map((r, i) => (
                      <span
                        key={i}
                        className="bg-red-500/10 text-red-400 border border-red-500/30 px-2 py-1 rounded text-xs"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-xs text-muted">
                Processing: {String(result.processing_time_ms)}ms
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
