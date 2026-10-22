"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { isMockMode, MOCK_HEATMAP_REGIONS } from "@/lib/mock-data";

const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false }
) as any;
const TileLayer = dynamic(
  () => import("react-leaflet").then((m) => m.TileLayer),
  { ssr: false }
) as any;
const CircleMarker = dynamic(
  () => import("react-leaflet").then((m) => m.CircleMarker),
  { ssr: false }
) as any;
const Popup = dynamic(
  () => import("react-leaflet").then((m) => m.Popup),
  { ssr: false }
) as any;

interface Region {
  city: string;
  latitude: number;
  longitude: number;
  total_scans: number;
  counterfeit_count: number;
  risk_ratio: number;
}

function riskColor(ratio: number): string {
  if (ratio > 0.3) return "#DC2626";
  if (ratio > 0.1) return "#D97706";
  return "#059669";
}

export default function HeatMap({ fullScreen = false }: { fullScreen?: boolean }) {
  const [regions, setRegions] = useState<Region[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (isMockMode()) {
      setRegions(MOCK_HEATMAP_REGIONS);
      return;
    }
    fetch("/api/risk-score?type=heatmap")
      .then((r) => r.json())
      .then((d) => setRegions(d.regions || []))
      .catch(() => setRegions(MOCK_HEATMAP_REGIONS));
  }, []);

  if (!mounted) {
    return (
      <div
        className={`bg-white border border-border rounded-lg shadow-card flex items-center justify-center text-text-secondary ${
          fullScreen ? "h-[calc(100vh-8rem)]" : "h-80"
        }`}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading map...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white border border-border rounded-lg shadow-card overflow-hidden ${
        fullScreen ? "h-[calc(100vh-8rem)]" : "h-80"
      }`}
    >
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <MapContainer
        center={[22.5, 78.9]}
        zoom={5}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {regions.map((r: Region) => (
          <CircleMarker
            key={r.city}
            center={[r.latitude, r.longitude]}
            radius={Math.max(8, Math.sqrt(r.total_scans) * 1.5)}
            pathOptions={{
              color: riskColor(r.risk_ratio),
              fillColor: riskColor(r.risk_ratio),
              fillOpacity: 0.6,
              weight: 2,
            }}
          >
            <Popup>
              <div className="text-sm text-foreground min-w-[140px]">
                <p className="font-bold text-base">{r.city}</p>
                <hr className="my-1.5 border-border" />
                <p className="text-text-secondary">Total Scans: <strong className="text-foreground">{r.total_scans}</strong></p>
                <p className="text-text-secondary">Counterfeit: <strong className="text-danger">{r.counterfeit_count}</strong></p>
                <p className="text-text-secondary">Risk: <strong style={{ color: riskColor(r.risk_ratio) }}>{(r.risk_ratio * 100).toFixed(1)}%</strong></p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
