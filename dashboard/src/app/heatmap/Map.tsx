"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";

interface Cluster {
  center_lat: number;
  center_lng: number;
  risk_score: number;
  risk_label: string;
  event_count: number;
  recent_event_count?: number;
  radius_km: number;
  state?: string;
  nearest_known_hotspot?: string;
  nearest_hotspot_km?: number;
  flag_types?: string[];
  dominant_severity?: string;
  dominant_category?: string;
  category_breakdown?: Record<string, number>;
  // legacy format support
  center?: [number, number];
  severity?: string;
}

interface Corridor {
  from_coords: [number, number];
  to_coords: [number, number];
  waypoints: number[][];
  road_waypoints?: number[][];
  corridor_risk: number;
  risk_level: string;
  from_state: string;
  to_state: string;
  anomaly_count: number;
  total_shipments: number;
  anomaly_types: string[];
  distance_km?: number;
}

interface KnownHotspot {
  name: string;
  lat: number;
  lng: number;
  baseline_risk: string;
  recent_events: number;
  trend: string;
  effective_risk_level?: string;
}

interface PredictedHotspot {
  center_lat: number;
  center_lng: number;
  growth_pct: number;
  severity: string;
  state?: string;
  current_count: number;
  predicted_count_2w: number;
  alert?: string;
  is_emerging?: boolean;
  // legacy
  center?: [number, number];
  predicted_growth?: number;
}

type TileStyle = "dark" | "satellite" | "osm";
type OverlayMode = "heat" | "clusters" | "corridors" | "hotspots" | "all";

const TILE_LAYERS: Record<TileStyle, { url: string; attribution: string; maxZoom?: number }> = {
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19,
  },
  satellite: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "&copy; Esri",
    maxZoom: 18,
  },
  osm: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "&copy; OSM",
    maxZoom: 19,
  },
};

const RISK_COLORS: Record<string, string> = {
  critical: "#FF2D55",
  high: "#FF6B35",
  medium: "#FFB800",
  elevated: "#FF9500",
  low: "#30D158",
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#FF2D55",
  high: "#FF6B35",
  medium: "#FFB800",
  low: "#30D158",
};

function getClusterCenter(c: Cluster): [number, number] {
  if (c.center_lat != null && c.center_lng != null) return [c.center_lat, c.center_lng];
  if (c.center) return c.center;
  return [0, 0];
}

function getClusterSeverity(c: Cluster): string {
  return c.risk_label?.includes("Critical")
    ? "critical"
    : c.risk_label?.includes("High")
    ? "high"
    : c.risk_label?.includes("Medium")
    ? "medium"
    : c.dominant_severity || c.severity || "low";
}

export default function HeatmapMap({
  points,
  clusters,
  corridors = [],
  knownHotspots = [],
  predictedHotspots = [],
}: {
  points: number[][];
  clusters: Cluster[];
  corridors?: Corridor[];
  knownHotspots?: KnownHotspot[];
  predictedHotspots?: PredictedHotspot[];
}) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tileRef = useRef<L.TileLayer | null>(null);
  const heatRef = useRef<L.Layer | null>(null);
  const overlayGroupRef = useRef<L.LayerGroup | null>(null);
  const corridorGroupRef = useRef<L.LayerGroup | null>(null);
  const hotspotGroupRef = useRef<L.LayerGroup | null>(null);
  const predictionGroupRef = useRef<L.LayerGroup | null>(null);
  const [tileStyle, setTileStyle] = useState<TileStyle>("dark");
  const [overlay, setOverlay] = useState<OverlayMode>("all");

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView([22.5, 78.9629], 5);

    // Add zoom control to bottom-right
    L.control.zoom({ position: "bottomright" }).addTo(map);

    const tile = TILE_LAYERS[tileStyle];
    tileRef.current = L.tileLayer(tile.url, {
      attribution: tile.attribution,
      maxZoom: tile.maxZoom,
    }).addTo(map);

    overlayGroupRef.current = L.layerGroup().addTo(map);
    corridorGroupRef.current = L.layerGroup().addTo(map);
    hotspotGroupRef.current = L.layerGroup().addTo(map);
    predictionGroupRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Switch tile layer
  useEffect(() => {
    if (!mapRef.current || !tileRef.current) return;
    mapRef.current.removeLayer(tileRef.current);
    const tile = TILE_LAYERS[tileStyle];
    tileRef.current = L.tileLayer(tile.url, {
      attribution: tile.attribution,
      maxZoom: tile.maxZoom,
    }).addTo(mapRef.current);
    tileRef.current.bringToBack();
  }, [tileStyle]);

  // Update heat layer
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;

    if (heatRef.current) {
      map.removeLayer(heatRef.current);
      heatRef.current = null;
    }

    if (points.length > 0 && (overlay === "heat" || overlay === "all")) {
      const heatData = points.map(([lat, lng, intensity]) => [lat, lng, intensity || 0.5]);
      // @ts-expect-error -- L.heatLayer from leaflet.heat plugin
      heatRef.current = L.heatLayer(heatData, {
        radius: 20,
        blur: 25,
        maxZoom: 10,
        max: 1.0,
        minOpacity: 0,
        gradient: {
          0.0: "rgba(0, 0, 0, 0)",
          0.15: "rgba(0, 0, 0, 0)",
          0.25: "rgba(255, 200, 0, 0.4)",
          0.4: "#F59E0B",
          0.55: "#F97316",
          0.7: "#EF4444",
          0.82: "#DC2626",
          0.92: "#BE185D",
          1.0: "#7C3AED",
        },
      }).addTo(map);
    }
  }, [points, overlay]);

  // Update cluster overlays
  useEffect(() => {
    if (!mapRef.current) return;
    overlayGroupRef.current?.clearLayers();

    if (overlay !== "clusters" && overlay !== "all") return;

    const group = overlayGroupRef.current!;

    clusters.forEach((c) => {
      const center = getClusterCenter(c);
      const severity = getClusterSeverity(c);
      const col = SEVERITY_COLORS[severity] || "#2563EB";
      const riskScore = c.risk_score ?? 0.5;

      // Outer glow ring (severity-proportional opacity)
      L.circle(center, {
        radius: (c.radius_km || 5) * 1000,
        color: col,
        fillColor: col,
        fillOpacity: 0.04 + riskScore * 0.08,
        weight: 1.5,
        dashArray: severity === "critical" ? undefined : "8,6",
        className: severity === "critical" ? "cluster-pulse" : "",
      })
        .bindPopup(
          `<div style="font-family:system-ui;font-size:12px;min-width:180px;">
            <div style="font-size:14px;font-weight:700;color:${col};margin-bottom:6px;">
              ${c.risk_label || severity.toUpperCase()}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;margin-bottom:8px;">
              <span style="color:#94A3B8;">Events</span><span style="font-weight:600;">${c.event_count}</span>
              <span style="color:#94A3B8;">Recent (7d)</span><span style="font-weight:600;">${c.recent_event_count ?? "—"}</span>
              <span style="color:#94A3B8;">Risk Score</span><span style="font-weight:600;">${(riskScore * 100).toFixed(0)}%</span>
              <span style="color:#94A3B8;">Radius</span><span style="font-weight:600;">${c.radius_km?.toFixed(1)} km</span>
            </div>
            ${c.state ? `<div style="color:#94A3B8;font-size:11px;">${c.state}${c.nearest_known_hotspot ? ` · Near ${c.nearest_known_hotspot}` : ""}</div>` : ""}
            ${c.category_breakdown ? `<div style="margin-top:6px;font-size:10px;color:#64748B;">${Object.entries(c.category_breakdown).map(([k, v]) => `${k}: ${v}`).join(" · ")}</div>` : ""}
          </div>`
        )
        .addTo(group);

      // Inner ring
      L.circleMarker(center, {
        radius: 8,
        fillColor: col,
        color: "rgba(255,255,255,0.8)",
        weight: 1.5,
        fillOpacity: 0.9,
      }).addTo(group);

      // Outer pulse ring
      L.circleMarker(center, {
        radius: 16,
        fillColor: col,
        color: col,
        weight: 1,
        fillOpacity: 0.12,
      }).addTo(group);
    });
  }, [clusters, overlay]);

  // Update corridors (uses precomputed road_waypoints from backend)
  useEffect(() => {
    if (!mapRef.current) return;
    corridorGroupRef.current?.clearLayers();

    if ((overlay !== "corridors" && overlay !== "all") || !corridors.length) return;

    const group = corridorGroupRef.current!;

    corridors.forEach((c) => {
      const col = RISK_COLORS[c.risk_level] || "#FFB800";
      const opacity = Math.max(0.3, Math.min(0.8, c.corridor_risk));
      const weight = c.risk_level === "high" ? 3.5 : 2.5;

      // Use precomputed road route, fall back to straight-line waypoints
      const hasRoad = c.road_waypoints && c.road_waypoints.length > 1;
      const latlngs: L.LatLngExpression[] = hasRoad
        ? c.road_waypoints!.map((wp) => [wp[0], wp[1]] as L.LatLngExpression)
        : c.waypoints.map((wp) => [wp[0], wp[1]] as L.LatLngExpression);

      // Outer glow for high-risk routes
      if (c.corridor_risk > 0.5) {
        L.polyline(latlngs, {
          color: col,
          weight: weight + 4,
          opacity: opacity * 0.15,
          lineCap: "round",
          lineJoin: "round",
        }).addTo(group);
      }

      // Main route line
      L.polyline(latlngs, {
        color: col,
        weight,
        opacity,
        dashArray: hasRoad ? undefined : "10,6",
        lineCap: "round",
        lineJoin: "round",
      })
        .bindPopup(
          `<div style="font-family:system-ui;font-size:12px;min-width:180px;">
            <div style="font-weight:700;color:${col};margin-bottom:4px;">
              ${c.from_state} → ${c.to_state}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;">
              <span style="color:#94A3B8;">Risk</span><span style="font-weight:600;">${(c.corridor_risk * 100).toFixed(0)}%</span>
              <span style="color:#94A3B8;">Distance</span><span>${c.distance_km?.toFixed(0) || "—"} km</span>
              <span style="color:#94A3B8;">Anomalies</span><span style="color:${col};">${c.anomaly_count}/${c.total_shipments}</span>
            </div>
            ${c.anomaly_types.length ? `<div style="margin-top:4px;font-size:10px;color:#64748B;">${c.anomaly_types.join(", ")}</div>` : ""}
          </div>`
        )
        .addTo(group);

      // Origin marker
      L.circleMarker([c.from_coords[0], c.from_coords[1]], {
        radius: 5,
        fillColor: col,
        color: "rgba(255,255,255,0.7)",
        weight: 1.5,
        fillOpacity: 0.9,
      })
        .bindTooltip(c.from_state, { permanent: false, direction: "top", className: "route-tooltip" })
        .addTo(group);

      // Destination marker
      L.circleMarker([c.to_coords[0], c.to_coords[1]], {
        radius: 5,
        fillColor: col,
        color: "rgba(255,255,255,0.7)",
        weight: 1.5,
        fillOpacity: 0.9,
      })
        .bindTooltip(c.to_state, { permanent: false, direction: "top", className: "route-tooltip" })
        .addTo(group);

      // Direction arrow at midpoint for road routes
      if (hasRoad && c.road_waypoints!.length > 2) {
        const mid = c.road_waypoints![Math.floor(c.road_waypoints!.length / 2)];
        const arrowIcon = L.divIcon({
          className: "",
          html: `<div style="font-size:10px;color:${col};text-shadow:0 0 4px rgba(0,0,0,0.8);font-weight:700;">▶</div>`,
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        });
        L.marker([mid[0], mid[1]], { icon: arrowIcon, interactive: false }).addTo(group);
      }
    });
  }, [corridors, overlay]);

  // Update known hotspots
  useEffect(() => {
    if (!mapRef.current) return;
    hotspotGroupRef.current?.clearLayers();

    if ((overlay !== "hotspots" && overlay !== "all") || !knownHotspots.length) return;

    const group = hotspotGroupRef.current!;

    knownHotspots.forEach((hs) => {
      const riskCol = RISK_COLORS[hs.effective_risk_level || hs.baseline_risk] || "#FFB800";
      const trendIcon = hs.trend === "increasing" ? "▲" : hs.trend === "decreasing" ? "▼" : "●";
      const trendCol = hs.trend === "increasing" ? "#FF2D55" : hs.trend === "decreasing" ? "#30D158" : "#94A3B8";

      // Diamond marker for known hotspots
      const icon = L.divIcon({
        className: "",
        html: `<div style="
          width:14px;height:14px;
          background:${riskCol};
          transform:rotate(45deg);
          border:2px solid rgba(255,255,255,0.7);
          box-shadow:0 0 8px ${riskCol}80;
        "></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      L.marker([hs.lat, hs.lng], { icon })
        .bindPopup(
          `<div style="font-family:system-ui;font-size:12px;min-width:170px;">
            <div style="font-weight:700;color:${riskCol};margin-bottom:4px;">
              ◆ ${hs.name}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;">
              <span style="color:#94A3B8;">Baseline</span><span>${hs.baseline_risk}</span>
              <span style="color:#94A3B8;">Events (7d)</span><span style="font-weight:600;">${hs.recent_events}</span>
              <span style="color:#94A3B8;">Trend</span><span style="color:${trendCol};font-weight:600;">${trendIcon} ${hs.trend}</span>
            </div>
          </div>`
        )
        .addTo(group);

      // Ambient ring around hotspot
      L.circle([hs.lat, hs.lng], {
        radius: 5000,
        color: riskCol,
        fillColor: riskCol,
        fillOpacity: 0.03,
        weight: 1,
        dashArray: "4,4",
      }).addTo(group);
    });
  }, [knownHotspots, overlay]);

  // Update predicted hotspots
  useEffect(() => {
    if (!mapRef.current) return;
    predictionGroupRef.current?.clearLayers();

    if ((overlay !== "all" && overlay !== "clusters") || !predictedHotspots.length) return;

    const group = predictionGroupRef.current!;

    predictedHotspots
      .filter((h) => h.is_emerging)
      .forEach((h) => {
        const center: [number, number] = h.center_lat != null
          ? [h.center_lat, h.center_lng]
          : h.center || [0, 0];
        const col = h.severity === "critical" ? "#7C3AED" : h.severity === "high" ? "#A855F7" : "#C084FC";

        // Pulsing prediction ring
        L.circle(center, {
          radius: 15000,
          color: col,
          fillColor: col,
          fillOpacity: 0.06,
          weight: 2,
          dashArray: "12,8",
          className: "prediction-pulse",
        })
          .bindPopup(
            `<div style="font-family:system-ui;font-size:12px;min-width:170px;">
              <div style="font-weight:700;color:${col};margin-bottom:4px;">
                ⚡ Emerging Hotspot
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;">
                <span style="color:#94A3B8;">Now</span><span>${h.current_count} events</span>
                <span style="color:#94A3B8;">In 2 weeks</span><span style="font-weight:700;color:${col};">~${h.predicted_count_2w?.toFixed(0)}</span>
                <span style="color:#94A3B8;">Growth</span><span style="color:${col};">+${h.growth_pct?.toFixed(0)}%</span>
              </div>
              ${h.state ? `<div style="margin-top:4px;color:#94A3B8;font-size:11px;">${h.state}</div>` : ""}
            </div>`
          )
          .addTo(group);

        // Upward arrow icon
        const arrowIcon = L.divIcon({
          className: "",
          html: `<div style="
            font-size:16px;
            color:${col};
            text-shadow:0 0 6px ${col};
            font-weight:900;
          ">⚡</div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });
        L.marker(center, { icon: arrowIcon }).addTo(group);
      });
  }, [predictedHotspots, overlay]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* Top-left: Layer controls */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-col gap-2">
        {/* Tile switcher */}
        <div className="flex gap-1 bg-[rgba(10,15,26,0.9)] backdrop-blur-sm rounded-lg p-1 border border-white/10">
          {(["dark", "satellite", "osm"] as TileStyle[]).map((style) => (
            <button
              key={style}
              onClick={() => setTileStyle(style)}
              className={`px-2.5 py-1 text-[11px] rounded-md transition-all ${
                tileStyle === style
                  ? "bg-accent text-white font-semibold"
                  : "text-muted hover:text-white"
              }`}
            >
              {style === "dark" ? "Dark" : style === "satellite" ? "Satellite" : "Street"}
            </button>
          ))}
        </div>

        {/* Overlay mode */}
        <div className="flex flex-wrap gap-1 bg-[rgba(10,15,26,0.9)] backdrop-blur-sm rounded-lg p-1 border border-white/10">
          {(["all", "heat", "clusters", "corridors", "hotspots"] as OverlayMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setOverlay(mode)}
              className={`px-2 py-1 text-[10px] rounded-md transition-all capitalize ${
                overlay === mode
                  ? "bg-purple-600 text-white font-semibold"
                  : "text-muted hover:text-white"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Bottom-left: Legend */}
      <div className="absolute bottom-6 left-3 z-[1000] bg-[rgba(10,15,26,0.9)] backdrop-blur-sm rounded-lg p-3 border border-white/10 text-[10px]">
        <div className="text-[11px] font-semibold mb-2 text-white/80">Legend</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: "#F59E0B" }} />
            <span className="text-muted">Low risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: "#F97316" }} />
            <span className="text-muted">Medium risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: "#EF4444" }} />
            <span className="text-muted">High risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: "#BE185D" }} />
            <span className="text-muted">Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rotate-45" style={{ background: "#FFB800", border: "1px solid white" }} />
            <span className="text-muted">Known hotspot</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: "#A855F7", fontSize: 12 }}>⚡</span>
            <span className="text-muted">Emerging</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ background: "#FF6B35" }} />
            <span className="text-muted">Road route</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5" style={{ background: "#FFB800", borderTop: "1px dashed #FFB800" }} />
            <span className="text-muted">Estimated route</span>
          </div>
        </div>
      </div>
    </div>
  );
}
