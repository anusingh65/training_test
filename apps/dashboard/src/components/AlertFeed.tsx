"use client";

import { useRealtimeAlerts } from "@/hooks/useRealtimeAlerts";
import { AlertTriangle, Clock, CheckCircle, XCircle, Search as SearchIcon, ShieldAlert } from "lucide-react";

const severityConfig: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  critical: { bg: "bg-white", text: "text-danger", border: "border-l-danger", dot: "bg-danger" },
  high: { bg: "bg-white", text: "text-orange-500", border: "border-l-orange-500", dot: "bg-orange-500" },
  medium: { bg: "bg-white", text: "text-warning", border: "border-l-warning", dot: "bg-warning" },
  low: { bg: "bg-white", text: "text-info", border: "border-l-info", dot: "bg-info" },
};

const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  pending: { bg: "bg-gray-100", text: "text-text-secondary", label: "Pending" },
  investigating: { bg: "bg-warning-light", text: "text-warning", label: "Investigating" },
  confirmed: { bg: "bg-danger-light", text: "text-danger", label: "Confirmed" },
  dismissed: { bg: "bg-gray-100", text: "text-text-tertiary", label: "Dismissed" },
};

export default function AlertFeed() {
  const { alerts, loading } = useRealtimeAlerts();

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-border rounded-lg p-4 shadow-card animate-pulse">
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded bg-gray-100 mt-0.5" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-100 rounded w-3/4" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => {
        const sev = severityConfig[alert.severity] || severityConfig.medium;
        const stat = statusConfig[alert.status] || statusConfig.pending;

        return (
          <div
            key={alert.id}
            className={`${sev.bg} border border-border border-l-4 ${sev.border} rounded-lg p-4 shadow-card animate-fade-in`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="relative mt-0.5 shrink-0">
                  <AlertTriangle size={18} className={sev.text} />
                  <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${sev.dot} ${alert.status === "pending" ? "animate-pulse-dot" : ""}`} />
                </div>
                <div>
                  <p className="font-medium text-sm text-foreground">{alert.reason}</p>
                  <p className="text-xs text-text-secondary mt-1">
                    <span className="font-mono">{alert.drug_id}</span> &middot; {alert.location}
                  </p>
                  {alert.description && (
                    <p className="text-xs text-text-tertiary mt-2 leading-relaxed">{alert.description}</p>
                  )}
                </div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ml-3 ${stat.bg} ${stat.text}`}>
                {stat.label}
              </span>
            </div>
            <p className="text-xs text-text-tertiary mt-3">
              {new Date(alert.created_at).toLocaleString()}
            </p>
          </div>
        );
      })}
      {alerts.length === 0 && (
        <div className="text-center py-12">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
            <ShieldAlert size={28} className="text-text-tertiary" />
          </div>
          <p className="text-text-secondary font-medium">No alerts</p>
          <p className="text-text-tertiary text-xs mt-1">All clear — no flagged reports</p>
        </div>
      )}
    </div>
  );
}
