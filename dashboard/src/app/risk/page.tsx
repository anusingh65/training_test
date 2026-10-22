"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface SignalData {
  score: number;
  status: string;
  [key: string]: unknown;
}

interface RiskResult {
  medicine_id: number;
  trust_score: number;
  risk_level: string;
  flag_severity: number;
  signals: Record<string, SignalData>;
  recommendation: string;
  auto_flag: boolean;
  blockchain_tx?: string;
  timestamp: string;
  processing_time_ms: number;
}

export default function RiskPage() {
  const [medicineId, setMedicineId] = useState(1);
  const [drugName, setDrugName] = useState("amoxicillin");
  const [lat, setLat] = useState(19.076);
  const [lng, setLng] = useState(72.877);
  const [actorRep, setActorRep] = useState(0.75);
  const [result, setResult] = useState<RiskResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const score = () => {
    setLoading(true);
    setError("");
    api
      .post("/api/risk-score", {
        medicine_id: medicineId,
        drug_name: drugName,
        location: { lat, lng },
        actor_reputation: actorRep,
        auto_flag: true,
      })
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const lookup = () => {
    setLoading(true);
    setError("");
    api
      .get(`/api/risk-score/${medicineId}`)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Composite Risk Score</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface rounded-xl p-5 border border-white/5">
          <h2 className="font-semibold mb-4">Score a Medicine</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs text-muted block mb-1">Medicine ID</label>
              <input
                type="number"
                value={medicineId}
                onChange={(e) => setMedicineId(parseInt(e.target.value) || 0)}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Drug Name</label>
              <input
                value={drugName}
                onChange={(e) => setDrugName(e.target.value)}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Latitude</label>
              <input
                type="number"
                step="any"
                value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Longitude</label>
              <input
                type="number"
                step="any"
                value={lng}
                onChange={(e) => setLng(parseFloat(e.target.value) || 0)}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-muted block mb-1">Actor Reputation (0-1)</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={actorRep}
                onChange={(e) => setActorRep(parseFloat(e.target.value) || 0)}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={score}
              disabled={loading}
              className="flex-1 bg-accent text-white py-2 rounded font-semibold text-sm disabled:opacity-50"
            >
              {loading ? "Scoring..." : "Compute Risk Score"}
            </button>
            <button
              onClick={lookup}
              disabled={loading}
              className="bg-surface text-white py-2 px-4 rounded text-sm border border-white/10 disabled:opacity-50"
            >
              Lookup Cached
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
              {/* Trust score big display */}
              <div className="text-center mb-6">
                <div className="text-6xl font-bold mb-2" style={{
                  color: result.trust_score >= 80
                    ? "#10B981"
                    : result.trust_score >= 50
                    ? "#F59E0B"
                    : result.trust_score >= 20
                    ? "#FB923C"
                    : "#EF4444",
                }}>
                  {result.trust_score}
                </div>
                <div className={`text-sm font-semibold uppercase tracking-wider ${
                  result.risk_level === "low"
                    ? "text-green-400"
                    : result.risk_level === "medium"
                    ? "text-yellow-400"
                    : result.risk_level === "high"
                    ? "text-orange-400"
                    : "text-red-400"
                }`}>
                  {result.risk_level} risk
                </div>
              </div>

              {/* Signals breakdown */}
              {result.signals && (
                <div className="space-y-2 mb-4">
                  <h3 className="text-xs text-muted font-semibold">Signal Breakdown</h3>
                  {Object.entries(result.signals).map(
                    ([key, sig]) => {
                      const sc = sig.score || 0;
                      return (
                        <div key={key} className="flex items-center justify-between bg-primary rounded-lg px-3 py-2 border border-white/5">
                          <span className="text-xs text-muted">{key.replace(/_/g, " ")}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-white/5 rounded-full h-2 overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${sc * 100}%`,
                                  backgroundColor: sc > 0.7 ? "#EF4444" : sc > 0.4 ? "#F59E0B" : "#10B981",
                                }}
                              />
                            </div>
                            <span className="text-xs font-mono w-10 text-right">
                              {sc.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              )}

              <div className="flex justify-between text-xs text-muted">
                <span>Auto-flag: {result.auto_flag ? "YES" : "no"}</span>
                <span>Severity: {result.flag_severity}</span>
              </div>
              {result.recommendation && (
                <div className="mt-3 text-xs bg-primary rounded-lg p-3 border border-white/5 text-muted">
                  {result.recommendation}
                </div>
              )}
              <div className="text-xs text-muted mt-2">
                Processing: {result.processing_time_ms}ms
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
