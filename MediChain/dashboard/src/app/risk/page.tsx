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

const SIGNAL_INFO: Record<string, { label: string; weight: string; desc: string }> = {
  supply_chain: {
    label: "Supply Chain Anomaly",
    weight: "45%",
    desc: "Isolation Forest + Autoencoder analysis of transfer patterns, velocity, timing",
  },
  geographic_risk: {
    label: "Geographic Risk",
    weight: "40%",
    desc: "Proximity to known counterfeit hotspots via DBSCAN clustering",
  },
  external_factors: {
    label: "External Factors",
    weight: "15%",
    desc: "Actor reputation (30%), adverse events (30%), shortage (20%), recall (20%)",
  },
};

const SCENARIOS = [
  {
    name: "Trusted Mumbai Pharmacy",
    tag: "LOW RISK",
    tagColor: "text-green-400 border-green-500/30 bg-green-500/10",
    explanation: "Medicine at a well-known pharmacy in South Mumbai (Colaba) with a highly reputable actor (0.85). Location is far from counterfeit hotspots. No shortage or recall flags. All signals should be green — trust score ~80+.",
    values: { medicine_id: 1001, drug_name: "paracetamol", lat: 18.9067, lng: 72.8147, actor_reputation: 0.85 },
  },
  {
    name: "Near Bhagirath Palace (Delhi)",
    tag: "HIGH RISK",
    tagColor: "text-orange-400 border-orange-500/30 bg-orange-500/10",
    explanation: "Medicine located near Bhagirath Palace in Old Delhi — India's largest wholesale pharma market and a known counterfeit hotspot. The geographic risk signal will spike because DBSCAN detects dense flagging activity in this zone. Even with a decent actor reputation (0.60), the proximity to a hotspot drives the trust score down significantly.",
    values: { medicine_id: 2001, drug_name: "amoxicillin", lat: 28.6562, lng: 77.2310, actor_reputation: 0.60 },
  },
  {
    name: "Low Reputation Distributor",
    tag: "MEDIUM RISK",
    tagColor: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10",
    explanation: "A distributor with poor reputation (0.25) handling medicine in Hyderabad. The external factors signal spikes because reputation_risk = 1 - 0.25 = 0.75 (high risk). Geographic risk is moderate. This shows how actor behavior history affects the composite score.",
    values: { medicine_id: 3001, drug_name: "ciprofloxacin", lat: 17.3850, lng: 78.4867, actor_reputation: 0.25 },
  },
  {
    name: "Counterfeit Corridor (Agra-Delhi)",
    tag: "CRITICAL",
    tagColor: "text-red-400 border-red-500/30 bg-red-500/10",
    explanation: "Medicine at a location along the Agra-Delhi corridor — one of the highest-risk supply chain routes for counterfeit drugs in India. Very low actor reputation (0.10) pushes external risk to maximum. Geographic heatmap shows elevated cluster activity. Trust score should be <20, triggering auto-flag with Critical severity on the blockchain.",
    values: { medicine_id: 4001, drug_name: "metformin", lat: 27.1767, lng: 78.0081, actor_reputation: 0.10 },
  },
  {
    name: "Rural Dispensary (Safe Zone)",
    tag: "LOW RISK",
    tagColor: "text-green-400 border-green-500/30 bg-green-500/10",
    explanation: "Medicine at a rural dispensary in central India, far from any known pharma hubs or hotspots. Good actor reputation (0.80). The heatmap engine finds no nearby clusters, so geographic risk is low. This demonstrates that the system doesn't penalize legitimate rural supply chains.",
    values: { medicine_id: 5001, drug_name: "azithromycin", lat: 23.2599, lng: 77.4126, actor_reputation: 0.80 },
  },
];

export default function RiskPage() {
  const [values, setValues] = useState(SCENARIOS[0].values);
  const [activeScenario, setActiveScenario] = useState(0);
  const [result, setResult] = useState<RiskResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const score = () => {
    setLoading(true);
    setError("");
    api
      .post("/api/risk-score", {
        medicine_id: values.medicine_id,
        drug_name: values.drug_name,
        location: { lat: values.lat, lng: values.lng },
        actor_reputation: values.actor_reputation,
        auto_flag: false,
      })
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
        <h1 className="text-2xl font-bold mb-1">Composite Risk Score</h1>
        <p className="text-sm text-muted">
          Fuses 3 AI signals into a single 0-100 Trust Score: Supply Chain Anomaly (45%),
          Geographic Risk (40%), External Factors (15%). Scores below 50 auto-flag on blockchain.
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
        <div className="bg-surface rounded-xl p-5 border border-white/5">
          <h2 className="font-semibold mb-4">Score a Medicine</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs text-muted block mb-1">Medicine ID</label>
              <input
                type="number"
                value={values.medicine_id}
                onChange={(e) => setValues((v) => ({ ...v, medicine_id: parseInt(e.target.value) || 0 }))}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
              <div className="text-[10px] text-muted/60 mt-0.5">On-chain medicine identifier</div>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Drug Name</label>
              <input
                value={values.drug_name}
                onChange={(e) => setValues((v) => ({ ...v, drug_name: e.target.value }))}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
              <div className="text-[10px] text-muted/60 mt-0.5">For adverse event lookup</div>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Latitude</label>
              <input
                type="number"
                step="any"
                value={values.lat}
                onChange={(e) => setValues((v) => ({ ...v, lat: parseFloat(e.target.value) || 0 }))}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
              <div className="text-[10px] text-muted/60 mt-0.5">GPS latitude of scan location</div>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Longitude</label>
              <input
                type="number"
                step="any"
                value={values.lng}
                onChange={(e) => setValues((v) => ({ ...v, lng: parseFloat(e.target.value) || 0 }))}
                className="w-full bg-primary border border-white/10 rounded px-2 py-1.5 text-sm"
              />
              <div className="text-[10px] text-muted/60 mt-0.5">GPS longitude of scan location</div>
            </div>
            <div className="col-span-2">
              <label className="text-xs text-muted block mb-1">Actor Reputation (0-1)</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={values.actor_reputation}
                  onChange={(e) => setValues((v) => ({ ...v, actor_reputation: parseFloat(e.target.value) }))}
                  className="flex-1"
                />
                <span className={`font-mono text-sm w-12 text-right ${
                  values.actor_reputation >= 0.7 ? "text-green-400"
                  : values.actor_reputation >= 0.4 ? "text-yellow-400"
                  : "text-red-400"
                }`}>
                  {values.actor_reputation.toFixed(2)}
                </span>
              </div>
              <div className="text-[10px] text-muted/60 mt-0.5">
                0.0 = worst reputation, 1.0 = perfect. Risk = 1 - reputation
              </div>
            </div>
          </div>
          <button
            onClick={score}
            disabled={loading}
            className="w-full bg-accent text-white py-2.5 rounded-lg font-semibold text-sm disabled:opacity-50 hover:bg-accent/80 transition-colors"
          >
            {loading ? "Computing..." : "Compute Risk Score"}
          </button>

          {/* Signal Weight Explanation */}
          <div className="mt-4 pt-4 border-t border-white/5">
            <h3 className="text-[10px] text-muted uppercase tracking-wider font-semibold mb-2">Signal Architecture</h3>
            <div className="space-y-2">
              {Object.entries(SIGNAL_INFO).map(([key, info]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-accent-light/70 w-8">{info.weight}</span>
                  <div className="flex-1">
                    <div className="text-xs text-white/80">{info.label}</div>
                    <div className="text-[10px] text-muted/60">{info.desc}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="text-[10px] text-muted mt-2 italic">
              Trust Score = 100 × (1 - weighted_risk). Auto-flag on blockchain if &lt; 50.
            </div>
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
              {/* Trust score big display */}
              <div className="text-center mb-6">
                <div className="text-7xl font-bold mb-2" style={{
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
                <div className={`text-sm font-bold uppercase tracking-widest ${
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
                <div className="text-[10px] text-muted mt-1">
                  Trust Score: 0 (dangerous) → 100 (safe)
                </div>
              </div>

              {/* Signals breakdown */}
              {result.signals && (
                <div className="space-y-3 mb-5">
                  <h3 className="text-xs text-muted font-semibold uppercase tracking-wider">Signal Breakdown</h3>
                  {Object.entries(result.signals).map(([key, sig]) => {
                    const sc = sig.score || 0;
                    const info = SIGNAL_INFO[key];
                    return (
                      <div key={key} className="bg-primary rounded-lg p-3 border border-white/5">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <span className="text-xs text-white/90">{info?.label || key}</span>
                            <span className="text-[10px] text-muted ml-2">({info?.weight || ""})</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                              sig.status === "pass" || sig.status === "normal"
                                ? "text-green-400 border-green-500/30 bg-green-500/10"
                                : sig.status === "warning"
                                ? "text-yellow-400 border-yellow-500/30 bg-yellow-500/10"
                                : sig.status === "elevated"
                                ? "text-orange-400 border-orange-500/30 bg-orange-500/10"
                                : "text-red-400 border-red-500/30 bg-red-500/10"
                            }`}>
                              {sig.status}
                            </span>
                            <span className="text-xs font-mono w-12 text-right">
                              {sc.toFixed(2)}
                            </span>
                          </div>
                        </div>
                        <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.max(sc * 100, 2)}%`,
                              backgroundColor: sc > 0.7 ? "#EF4444" : sc > 0.4 ? "#F59E0B" : "#10B981",
                            }}
                          />
                        </div>
                        <div className="text-[10px] text-muted/60 mt-1">
                          0.0 = no risk → 1.0 = maximum risk
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Auto-flag & Severity */}
              <div className={`rounded-lg p-3 border mb-4 ${
                result.auto_flag
                  ? "bg-red-500/5 border-red-500/20"
                  : "bg-green-500/5 border-green-500/20"
              }`}>
                <div className="flex items-center justify-between">
                  <div className="text-xs">
                    <span className="font-semibold">Auto-flag: </span>
                    <span className={result.auto_flag ? "text-red-400" : "text-green-400"}>
                      {result.auto_flag ? "YES — would flag on blockchain" : "No — trust score above threshold"}
                    </span>
                  </div>
                  <span className="text-[10px] text-muted">
                    Severity: {["Low", "Medium", "High", "Critical"][result.flag_severity]}
                  </span>
                </div>
              </div>

              {/* Recommendation */}
              {result.recommendation && (
                <div className="bg-primary rounded-lg p-3 border border-white/5 mb-3">
                  <div className="text-[10px] text-muted uppercase tracking-wider mb-1">AI Recommendation</div>
                  <div className="text-xs text-white/80 leading-relaxed">{result.recommendation}</div>
                </div>
              )}

              <div className="text-[10px] text-muted">
                Processed in {result.processing_time_ms}ms
              </div>
            </div>
          )}

          {!result && !error && (
            <div className="bg-surface rounded-xl p-8 border border-white/5 text-center">
              <div className="text-4xl mb-3">⚖️</div>
              <div className="text-sm text-muted">
                Select a scenario and click <span className="text-white font-semibold">Compute Risk Score</span> to see the composite analysis
              </div>
              <div className="mt-4 text-xs text-muted/60 max-w-sm mx-auto">
                The engine gathers signals from anomaly detection, geographic heatmap, and external factors,
                then fuses them into a single trust score
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
