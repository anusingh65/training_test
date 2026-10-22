"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface AdverseResult {
  drug_name: string;
  total_reports: number;
  recent_reports_30d: number;
  quality_complaints: number;
  therapeutic_failures: number;
  counterfeit_risk_score: number;
  top_reactions: Array<{ term: string; count: number }>;
  signal_alerts: string[];
  processing_time_ms: number;
}

interface DrugIdentity {
  brand_name: string;
  generic_name: string;
  manufacturer: string;
  active_ingredients: Array<{ name: string; strength: string }>;
  dosage_form: string;
  route: string;
  packaging: Array<{ description: string; ndc: string }>;
  processing_time_ms: number;
}

interface RecallData {
  drug_name: string;
  recalls: Array<{
    recall_number: string;
    reason: string;
    status: string;
    date: string;
    classification: string;
  }>;
  total_recalls: number;
  processing_time_ms: number;
}

export default function AdversePage() {
  const [drugName, setDrugName] = useState("amoxicillin");
  const [daysBack, setDaysBack] = useState(90);
  const [result, setResult] = useState<AdverseResult | null>(null);
  const [identity, setIdentity] = useState<DrugIdentity | null>(null);
  const [recalls, setRecalls] = useState<RecallData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const search = () => {
    setLoading(true);
    setError("");
    setResult(null);
    setIdentity(null);
    setRecalls(null);

    Promise.allSettled([
      api.get(`/api/adverse-events/${encodeURIComponent(drugName)}?days_back=${daysBack}`),
      api.get(`/api/drug-identity/${encodeURIComponent(drugName)}`),
      api.get(`/api/drug-recalls/${encodeURIComponent(drugName)}`),
    ])
      .then(([ae, id, rc]) => {
        if (ae.status === "fulfilled") setResult(ae.value);
        if (id.status === "fulfilled") setIdentity(id.value);
        if (rc.status === "fulfilled") setRecalls(rc.value);
        if (ae.status === "rejected") setError(ae.reason?.message || "Failed");
      })
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Adverse Events & Drug Info</h1>

      <div className="flex gap-3 mb-6">
        <input
          value={drugName}
          onChange={(e) => setDrugName(e.target.value)}
          placeholder="Drug name (e.g. amoxicillin)"
          className="bg-surface border border-white/10 rounded px-3 py-2 text-sm flex-1"
        />
        <input
          type="number"
          value={daysBack}
          onChange={(e) => setDaysBack(parseInt(e.target.value) || 90)}
          className="bg-surface border border-white/10 rounded px-3 py-2 text-sm w-24"
        />
        <button
          onClick={search}
          disabled={loading || !drugName}
          className="bg-accent text-white px-6 py-2 rounded text-sm font-semibold disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Adverse events */}
        {result && (
          <div className="bg-surface rounded-xl p-5 border border-white/5">
            <h2 className="font-semibold mb-4">Adverse Events</h2>
            <div className="space-y-3">
              <Stat label="Total Reports" value={result.total_reports} />
              <Stat label="Recent (30d)" value={result.recent_reports_30d} />
              <Stat label="Quality Complaints" value={result.quality_complaints} />
              <Stat label="Therapeutic Failures" value={result.therapeutic_failures} />
              <div className="bg-primary rounded-lg p-3 border border-white/5">
                <div className="text-xs text-muted">Counterfeit Risk Score</div>
                <div
                  className={`text-2xl font-bold ${
                    result.counterfeit_risk_score > 0.5
                      ? "text-red-400"
                      : "text-green-400"
                  }`}
                >
                  {(result.counterfeit_risk_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {result.top_reactions?.length > 0 && (
              <div className="mt-4">
                <h3 className="text-xs text-muted font-semibold mb-2">Top Reactions</h3>
                <div className="space-y-1">
                  {result.top_reactions
                    .slice(0, 8)
                    .map((r, i) => (
                      <div key={i} className="flex justify-between text-xs">
                        <span className="text-muted">{r.term}</span>
                        <span>{r.count}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {result.signal_alerts?.length > 0 && (
              <div className="mt-4">
                <h3 className="text-xs text-muted font-semibold mb-2">Signal Alerts</h3>
                <div className="space-y-1">
                  {result.signal_alerts.map((a, i) => (
                    <div key={i} className="text-xs text-yellow-400 bg-yellow-500/10 rounded px-2 py-1">
                      {a}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Drug identity */}
        {identity && (
          <div className="bg-surface rounded-xl p-5 border border-white/5">
            <h2 className="font-semibold mb-4">Drug Identity</h2>
            <div className="space-y-2 text-sm">
              <Field label="Brand" value={identity.brand_name} />
              <Field label="Generic" value={identity.generic_name} />
              <Field label="Manufacturer" value={identity.manufacturer} />
              <Field label="Dosage Form" value={identity.dosage_form} />
              <Field label="Route" value={identity.route} />

              {identity.active_ingredients?.length > 0 && (
                <div>
                  <div className="text-xs text-muted mt-3 mb-1">Active Ingredients</div>
                  {identity.active_ingredients.map((ing, i) => (
                    <div key={i} className="text-xs bg-primary rounded px-2 py-1 mb-1 border border-white/5">
                      {ing.name} {ing.strength && `(${ing.strength})`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recalls */}
        {recalls && (
          <div className="bg-surface rounded-xl p-5 border border-white/5">
            <h2 className="font-semibold mb-4">
              Recalls ({recalls.total_recalls || 0})
            </h2>
            {recalls.recalls?.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {recalls.recalls.slice(0, 10).map((r, i) => (
                  <div key={i} className="bg-primary rounded-lg p-3 border border-white/5 text-xs">
                    <div className="font-semibold text-red-400">{r.classification}</div>
                    <div className="text-muted mt-1">{r.reason}</div>
                    <div className="flex justify-between mt-2 text-muted/60">
                      <span>{r.status}</span>
                      <span>{r.date}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted">No recalls found</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-muted">{label}</span>
      <span className="font-bold">{value}</span>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | undefined }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-xs text-muted">{label}: </span>
      <span className="text-xs">{value}</span>
    </div>
  );
}
