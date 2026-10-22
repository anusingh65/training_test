"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

interface Alert {
  id: number;
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const idRef = useRef(0);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setError("");

    const ws = new WebSocket(api.wsUrl("/api/ws/alerts"));
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: "subscribe" }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setAlerts((prev) => [
          { id: idRef.current++, type: data.type || "unknown", timestamp: new Date().toISOString(), data },
          ...prev.slice(0, 99),
        ]);
      } catch {
        // ignore non-JSON
      }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => {
      setError("WebSocket connection failed");
      setConnected(false);
    };
  };

  const disconnect = () => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  };

  const ping = () => {
    wsRef.current?.send(JSON.stringify({ type: "ping" }));
  };

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const typeColors: Record<string, string> = {
    DrugScanned: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    CustodyTransferred: "text-purple-400 bg-purple-500/10 border-purple-500/30",
    DrugFlagged: "text-red-400 bg-red-500/10 border-red-500/30",
    VelocityAlert: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    MedicineRegistered: "text-green-400 bg-green-500/10 border-green-500/30",
    RiskAlert: "text-red-400 bg-red-500/10 border-red-500/30",
    pong: "text-muted bg-white/5 border-white/10",
  };

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold">WebSocket Alerts</h1>
        <div className={`w-3 h-3 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
        <span className="text-sm text-muted">{connected ? "Connected" : "Disconnected"}</span>

        {!connected ? (
          <button onClick={connect} className="bg-accent text-white px-4 py-1.5 rounded text-sm">
            Connect
          </button>
        ) : (
          <>
            <button onClick={ping} className="bg-surface text-white px-3 py-1.5 rounded text-sm border border-white/10">
              Ping
            </button>
            <button onClick={disconnect} className="text-red-400 border border-red-500/30 px-3 py-1.5 rounded text-sm">
              Disconnect
            </button>
          </>
        )}

        {alerts.length > 0 && (
          <button
            onClick={() => setAlerts([])}
            className="text-xs text-muted hover:text-white ml-auto"
          >
            Clear ({alerts.length})
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 mb-4 text-sm">
          {error}
        </div>
      )}

      {!connected && alerts.length === 0 && (
        <div className="bg-surface rounded-xl p-8 border border-white/5 text-center text-muted">
          Click Connect to start receiving real-time blockchain alerts via WebSocket.
          <br />
          <span className="text-xs">Endpoint: {api.wsUrl("/api/ws/alerts")}</span>
        </div>
      )}

      <div className="space-y-2">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-lg p-3 border text-sm ${
              typeColors[alert.type] || "text-white bg-surface border-white/10"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-xs uppercase tracking-wider">
                {alert.type}
              </span>
              <span className="text-xs opacity-60">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <pre className="text-xs opacity-80 overflow-auto max-h-20">
              {JSON.stringify(alert.data, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
