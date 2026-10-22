"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export interface Transfer {
  step: number;
  from_actor: string;
  to_actor: string;
  from_coords: [number, number];
  to_coords: [number, number];
  from_state: string;
  to_state: string;
  timestamp: string;
  is_anomaly: boolean;
  anomaly_type: string;
  transfer_velocity_kmh: number;
}

export interface Origin {
  actor: string;
  coords: [number, number];
  state: string;
}

interface CommonOrigin {
  factory: string;
  coords: [number, number];
  state: string;
  batch_count: number;
  batch_ids: string[];
}

interface BatchTraceMapProps {
  chain: Transfer[];
  origin: Origin | null;
  selectedStep: number | null;
  onStepClick: (step: number) => void;
  commonOrigins?: CommonOrigin[];
  multiChains?: { batch_id: string; chain: Transfer[]; origin: Origin }[];
}

const ROLE_COLORS: Record<string, string> = {
  Manufacturer: "#3B82F6",
  Distributor: "#F59E0B",
  Pharmacy: "#10B981",
  Consumer: "#8B5CF6",
};

const MULTI_BATCH_COLORS = [
  "#3B82F6",
  "#F59E0B",
  "#10B981",
  "#8B5CF6",
  "#EF4444",
  "#EC4899",
  "#06B6D4",
  "#84CC16",
];

function roleColor(role: string): string {
  return ROLE_COLORS[role] || "#6B7280";
}

function nodeIcon(label: string, color: string, size: number = 28, pulse: boolean = false): L.DivIcon {
  const pulseRing = pulse
    ? `<div style="position:absolute;top:-6px;left:-6px;width:${size + 12}px;height:${size + 12}px;border-radius:50%;border:2px solid ${color};animation:tracePulse 2s infinite;opacity:0.6;"></div>`
    : "";
  return L.divIcon({
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    html: `
      <div style="position:relative;width:${size}px;height:${size}px;">
        ${pulseRing}
        <div style="
          width:${size}px;height:${size}px;border-radius:50%;
          background:${color};border:2px solid rgba(255,255,255,0.8);
          display:flex;align-items:center;justify-content:center;
          font-size:${size > 28 ? 13 : 11}px;font-weight:700;color:#fff;
          box-shadow:0 2px 8px rgba(0,0,0,0.4);
        ">${label}</div>
      </div>
    `,
  });
}

function anomalyIcon(): L.DivIcon {
  return L.divIcon({
    className: "",
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    html: `
      <div style="
        width:22px;height:22px;border-radius:50%;
        background:#FF2D55;border:2px solid #fff;
        display:flex;align-items:center;justify-content:center;
        font-size:13px;font-weight:700;color:#fff;
        box-shadow:0 2px 6px rgba(255,45,85,0.5);
      ">!</div>
    `,
  });
}

function commonOriginIcon(count: number): L.DivIcon {
  return L.divIcon({
    className: "",
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    html: `
      <div style="position:relative;width:40px;height:40px;">
        <div style="position:absolute;top:-4px;left:-4px;width:48px;height:48px;border-radius:50%;border:2px solid #FF2D55;animation:tracePulse 1.5s infinite;opacity:0.7;"></div>
        <div style="
          width:40px;height:40px;border-radius:8px;
          background:linear-gradient(135deg,#FF2D55,#FF6B35);
          border:2px solid #fff;transform:rotate(45deg);
          display:flex;align-items:center;justify-content:center;
          box-shadow:0 3px 12px rgba(255,45,85,0.5);
        ">
          <span style="transform:rotate(-45deg);font-size:14px;font-weight:800;color:#fff;">${count}</span>
        </div>
      </div>
    `,
  });
}

export default function BatchTraceMap({
  chain,
  origin,
  selectedStep,
  onStepClick,
  commonOrigins,
  multiChains,
}: BatchTraceMapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  // Init map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView([22.5, 78.9629], 5);

    L.control.zoom({ position: "bottomright" }).addTo(map);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19,
    }).addTo(map);

    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    // Inject keyframe animation
    if (!document.getElementById("trace-pulse-style")) {
      const style = document.createElement("style");
      style.id = "trace-pulse-style";
      style.textContent = `
        @keyframes tracePulse {
          0% { transform: scale(1); opacity: 0.7; }
          50% { transform: scale(1.4); opacity: 0.2; }
          100% { transform: scale(1); opacity: 0.7; }
        }
      `;
      document.head.appendChild(style);
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Render chain
  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    const map = mapRef.current;
    const group = layerRef.current;
    group.clearLayers();

    const allBounds: L.LatLng[] = [];

    // --- Multi-chain mode (common origin comparison) ---
    if (multiChains && multiChains.length > 0) {
      multiChains.forEach((mc, idx) => {
        const color = MULTI_BATCH_COLORS[idx % MULTI_BATCH_COLORS.length];

        mc.chain.forEach((t) => {
          const from: L.LatLngExpression = [t.from_coords[0], t.from_coords[1]];
          const to: L.LatLngExpression = [t.to_coords[0], t.to_coords[1]];
          allBounds.push(L.latLng(from), L.latLng(to));

          L.polyline([from, to], {
            color: t.is_anomaly ? "#FF2D55" : color,
            weight: 2.5,
            opacity: t.is_anomaly ? 0.9 : 0.6,
            dashArray: t.is_anomaly ? "6 4" : undefined,
          }).addTo(group);
        });

        // Origin marker
        if (mc.origin && mc.origin.coords) {
          const pos: L.LatLngExpression = [mc.origin.coords[0], mc.origin.coords[1]];
          L.marker(pos, { icon: nodeIcon(String(idx + 1), color, 30, true) })
            .bindTooltip(`${mc.batch_id}<br>${mc.origin.actor}`, {
              className: "route-tooltip",
              direction: "top",
            })
            .addTo(group);
        }
      });

      // Common origin markers
      if (commonOrigins) {
        commonOrigins.forEach((co) => {
          if (co.coords) {
            const pos: L.LatLngExpression = [co.coords[0], co.coords[1]];
            allBounds.push(L.latLng(pos));
            L.marker(pos, { icon: commonOriginIcon(co.batch_count) })
              .bindTooltip(
                `<b>Common Origin</b><br>${co.factory}<br>${co.state}<br>${co.batch_count} flagged batches`,
                { className: "route-tooltip", direction: "top" }
              )
              .addTo(group);
          }
        });
      }

      if (allBounds.length > 0) {
        map.fitBounds(L.latLngBounds(allBounds).pad(0.15));
      }
      return;
    }

    // --- Single-chain mode ---
    if (!chain || chain.length === 0) return;

    // Track unique nodes for markers
    const nodes: { coords: [number, number]; role: string; step: number }[] = [];

    chain.forEach((t) => {
      const from: L.LatLngExpression = [t.from_coords[0], t.from_coords[1]];
      const to: L.LatLngExpression = [t.to_coords[0], t.to_coords[1]];
      allBounds.push(L.latLng(from), L.latLng(to));

      const isSelected = selectedStep === t.step;
      const baseWeight = isSelected ? 5 : 3;
      const baseOpacity = selectedStep && !isSelected ? 0.3 : 0.8;

      // Transfer line
      const line = L.polyline([from, to], {
        color: t.is_anomaly ? "#FF2D55" : "#3B82F6",
        weight: baseWeight,
        opacity: baseOpacity,
        dashArray: t.is_anomaly ? "8 5" : undefined,
      }).addTo(group);

      line.on("click", () => onStepClick(t.step));

      // Anomaly marker at midpoint
      if (t.is_anomaly) {
        const midLat = (t.from_coords[0] + t.to_coords[0]) / 2;
        const midLng = (t.from_coords[1] + t.to_coords[1]) / 2;
        L.marker([midLat, midLng], { icon: anomalyIcon() })
          .bindTooltip(
            `<b>Anomaly</b><br>${t.anomaly_type.replace(/_/g, " ")}`,
            { className: "route-tooltip", direction: "top" }
          )
          .addTo(group);
      }

      // Collect node positions
      if (t.step === 1) {
        nodes.push({ coords: t.from_coords, role: t.from_actor, step: 0 });
      }
      nodes.push({ coords: t.to_coords, role: t.to_actor, step: t.step });
    });

    // Draw node markers
    nodes.forEach((n, idx) => {
      const pos: L.LatLngExpression = [n.coords[0], n.coords[1]];
      const isOrigin = idx === 0;
      const label = isOrigin ? "O" : String(n.step);
      const size = isOrigin ? 34 : 28;
      const color = roleColor(n.role);

      const marker = L.marker(pos, {
        icon: nodeIcon(label, color, size, isOrigin),
        zIndexOffset: isOrigin ? 1000 : 500 - idx,
      }).addTo(group);

      const tooltipContent = isOrigin
        ? `<b>Origin</b><br>${origin?.actor || n.role}<br>${origin?.state || ""}`
        : `<b>Step ${n.step}</b><br>${n.role}<br>${chain[n.step - 1]?.to_state || ""}`;

      marker.bindTooltip(tooltipContent, {
        className: "route-tooltip",
        direction: "top",
      });

      if (n.step > 0) {
        marker.on("click", () => onStepClick(n.step));
      }
    });

    if (allBounds.length > 0) {
      map.fitBounds(L.latLngBounds(allBounds).pad(0.15));
    }
  }, [chain, selectedStep, commonOrigins, multiChains]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-xl overflow-hidden"
      style={{ minHeight: 500 }}
    />
  );
}
