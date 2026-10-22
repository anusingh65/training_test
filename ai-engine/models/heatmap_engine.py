"""
Geographic heatmap and hotspot-detection engine for MediChain.

Uses DBSCAN clustering on flagged scan events to identify geographic
concentrations of suspicious pharmaceutical activity, known-hotspot priors
from ``indian_pharma_hubs.json``, multi-source anomaly ingestion, and
exponential-smoothing trend prediction.

Key capabilities
----------------
* **Known-hotspot priors** -- Pre-loaded from reference data so the engine
  starts with baseline awareness of historically risky areas (Bhagirath
  Palace, Agra wholesale, etc.) even before scan data arrives.
* **Multi-source anomaly intensity** -- All 8 supply-chain anomaly types
  contribute to the heatmap at appropriate intensities.
* **Composite cluster risk scoring** -- Combines event count, severity,
  recency, and known-hotspot proximity into a single 0-1 score.
* **State-level risk aggregation** -- Rolls up cluster risk by Indian
  state for dashboard choropleth rendering.
* **Exponential smoothing prediction** -- Uses Holt's double exponential
  smoothing (level + trend) instead of naive linear regression.
* **Enhanced zone risk** -- Considers both cluster proximity AND known-
  hotspot proximity, returns richer metadata.

DBSCAN parameters
-----------------
* ``eps=0.05`` degrees (~5.5 km at Indian latitudes around 20 degN).
* ``min_samples=3`` balances sensitivity against noise.

Time decay
----------
Exponential decay with a configurable half-life (default 7 days).

Dependencies: ``numpy``, ``scikit-learn`` (DBSCAN).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import DBSCAN

# --------------------------------------------------------------------------- #
#  Constants                                                                   #
# --------------------------------------------------------------------------- #

EARTH_RADIUS_KM: float = 6371.0

# Base intensity values by flag type.  "flag_type" is a string present on
# each scan event dict (set upstream by the scan-verification pipeline).
_INTENSITY_MAP: Dict[str, float] = {
    "normal": 0.10,
    "flagged_low": 0.30,
    "flagged_medium": 0.50,
    "flagged_high": 0.80,
    "velocity_anomaly": 1.00,
    # Supply-chain anomaly types (injected from supply_chain_transactions.csv)
    "velocity_violation": 1.00,
    "geographic_impossibility": 0.95,
    "reverse_flow": 0.85,
    "path_deviation": 0.80,
    "hotspot_routing": 0.90,
    "excessive_transfers": 0.70,
    "suspicious_timing": 0.65,
    "duplicate_scan": 0.60,
}

# Indian state bounding boxes (approximate centroids for state assignment).
# Used for state-level aggregation.
_INDIA_STATES: Dict[str, Tuple[float, float]] = {
    "Andhra Pradesh": (15.9129, 79.7400),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    "Delhi": (28.7041, 77.1025),
    "Chandigarh": (30.7333, 76.7794),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Ladakh": (34.1526, 77.5771),
}


def _haversine_km(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> float:
    """Great-circle distance in km between two (lat, lng) points."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2.0) ** 2
    )
    return EARTH_RADIUS_KM * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _nearest_state(lat: float, lng: float) -> str:
    """Return the nearest Indian state name for a (lat, lng) point."""
    best_state = "Unknown"
    best_dist = float("inf")
    for state, (s_lat, s_lng) in _INDIA_STATES.items():
        d = (lat - s_lat) ** 2 + (lng - s_lng) ** 2
        if d < best_dist:
            best_dist = d
            best_state = state
    return best_state


# --------------------------------------------------------------------------- #
#  Main engine class                                                           #
# --------------------------------------------------------------------------- #


class HeatmapEngine:
    """Hotspot detection, risk assessment, and prediction engine.

    Parameters (all tuneable after construction via attribute assignment):

    * ``eps_degrees`` -- DBSCAN neighbourhood radius in decimal degrees.
    * ``min_samples`` -- DBSCAN minimum cluster size.
    * ``time_decay_halflife_days`` -- half-life for exponential time decay.
    """

    def __init__(self) -> None:
        self.eps_degrees: float = 0.05
        self.min_samples: int = 3
        self.time_decay_halflife_days: int = 7
        self.clusters: List[Dict[str, Any]] = []
        self.heatmap_points: List[List[float]] = []
        self.known_hotspots: List[Dict[str, Any]] = []
        self.state_risk: Dict[str, Dict[str, Any]] = {}
        self._load_known_hotspots()

    def _load_known_hotspots(self) -> None:
        """Load known hotspot priors from indian_pharma_hubs.json."""
        hubs_path = (
            Path(__file__).resolve().parent.parent
            / "data" / "synthetic" / "indian_pharma_hubs.json"
        )
        if not hubs_path.exists():
            return
        try:
            with open(hubs_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.known_hotspots = data.get("known_hotspots", [])
        except (json.JSONDecodeError, KeyError):
            pass

    # ----------------------------------------------------------------------- #
    #  Public API                                                              #
    # ----------------------------------------------------------------------- #

    def compute_heatmap(
        self,
        scan_events: List[Dict[str, Any]],
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Build a full heatmap payload from a list of scan events.

        Parameters
        ----------
        scan_events:
            Each event is a dict with **at least** the keys ``lat`` (float),
            ``lng`` (float), ``timestamp`` (ISO-8601 string **or**
            ``datetime``), and ``flag_type`` (str -- one of the keys in
            ``_INTENSITY_MAP``; defaults to ``"normal"`` if missing).
        reference_time:
            The "now" reference for time-decay computation.  Defaults to
            ``datetime.now(timezone.utc)``.

        Returns
        -------
        dict
            ``heatmap_points`` -- list of ``[lat, lng, intensity]`` triples.
            ``clusters`` -- list of cluster dicts.
            ``predicted_hotspots`` -- list of prediction dicts.
            ``state_risk`` -- per-state risk aggregation.
            ``known_hotspot_activity`` -- activity near known hotspots.
            ``stats`` -- summary statistics.
        """

        if reference_time is None:
            reference_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if not scan_events:
            empty: Dict[str, Any] = {
                "heatmap_points": [],
                "clusters": [],
                "predicted_hotspots": [],
                "state_risk": {},
                "known_hotspot_activity": [],
                "stats": {
                    "total_events": 0,
                    "flagged_events": 0,
                    "cluster_count": 0,
                    "hotspot_predictions": 0,
                    "known_hotspots_active": 0,
                },
            }
            self.heatmap_points = []
            self.clusters = []
            self.state_risk = {}
            return empty

        # -- 1. Compute time-decayed intensity for every event ---------------
        heatmap_points: List[List[float]] = []
        flagged_events: List[Dict[str, Any]] = []

        for event in scan_events:
            flag_type = event.get("flag_type", "normal")
            lat = float(event["lat"])
            lng = float(event["lng"])

            # Skip points outside India's land mass (prevents ocean blobs)
            if lat < 7.5 or lat > 36.0 or lng < 68.5 or lng > 97.5:
                continue

            if flag_type != "normal":
                intensity = self._compute_intensity(event, reference_time)
                heatmap_points.append([lat, lng, intensity])
                flagged_events.append(event)

        # -- 2. Inject known-hotspot ambient signal --------------------------
        for hs in self.known_hotspots:
            risk_level = hs.get("risk_level", "medium")
            ambient = {"low": 0.15, "medium": 0.30, "high": 0.50, "critical": 0.70}
            base = ambient.get(risk_level, 0.30)
            heatmap_points.append([
                float(hs["lat"]), float(hs["lng"]), base,
            ])

        # -- 3. DBSCAN clustering on flagged events --------------------------
        clusters = self._find_clusters(flagged_events, reference_time)

        # -- 4. Compute cluster growth via exponential smoothing -------------
        weekly_cluster_data = self._weekly_cluster_snapshots(
            flagged_events, reference_time, num_weeks=6
        )

        # -- 5. Predict emerging hotspots ------------------------------------
        predicted_hotspots = self._predict_hotspots(clusters, weekly_cluster_data)

        # -- 6. Known-hotspot activity report --------------------------------
        hotspot_activity = self._assess_known_hotspots(flagged_events, reference_time)

        # -- 7. State-level risk aggregation ---------------------------------
        state_risk = self._aggregate_state_risk(clusters, hotspot_activity)
        self.state_risk = state_risk

        # -- 8. Cache and return ---------------------------------------------
        self.heatmap_points = heatmap_points
        self.clusters = clusters

        return {
            "heatmap_points": heatmap_points,
            "clusters": clusters,
            "predicted_hotspots": predicted_hotspots,
            "state_risk": state_risk,
            "known_hotspot_activity": hotspot_activity,
            "stats": {
                "total_events": len(scan_events),
                "flagged_events": len(flagged_events),
                "cluster_count": len(clusters),
                "hotspot_predictions": len(predicted_hotspots),
                "known_hotspots_active": sum(
                    1 for h in hotspot_activity if h["recent_events"] > 0
                ),
                "states_at_risk": sum(
                    1 for s in state_risk.values() if s["risk_level"] != "low"
                ),
            },
        }

    def get_zone_risk_level(
        self,
        lat: float,
        lng: float,
    ) -> Dict[str, Any]:
        """Assess the risk level at a given coordinate.

        Combines proximity to DBSCAN clusters AND known hotspot priors.
        The final risk is the maximum of both assessments.

        Risk levels (from clusters):
        * **critical** -- within the cluster radius.
        * **high** -- within 2x the cluster radius (or < 5 km).
        * **elevated** -- within 10 km of a cluster.
        * **moderate** -- within 20 km of a cluster or 5 km of known hotspot.
        * **low** -- farther than all risk sources.

        Returns
        -------
        dict
            ``risk_level``, ``risk_score`` (0-1), ``nearest_cluster``,
            ``nearest_hotspot``, ``distance_km``, ``state``.
        """

        risk_order = ["low", "moderate", "elevated", "high", "critical"]
        risk_to_score = {"low": 0.1, "moderate": 0.3, "elevated": 0.5, "high": 0.7, "critical": 0.9}

        # --- Cluster proximity ---
        cluster_risk = "low"
        best_cluster_dist: float = float("inf")
        best_cluster: Optional[Dict[str, Any]] = None

        for cluster in self.clusters:
            c_lat = cluster["center_lat"]
            c_lng = cluster["center_lng"]
            dist = _haversine_km(lat, lng, c_lat, c_lng)
            if dist < best_cluster_dist:
                best_cluster_dist = dist
                best_cluster = cluster

        if best_cluster is not None:
            cluster_radius_km = best_cluster.get("radius_km", 5.0)
            cluster_severity = best_cluster.get("risk_score", 0.5)

            if best_cluster_dist <= cluster_radius_km:
                cluster_risk = "critical"
            elif best_cluster_dist <= cluster_radius_km * 2.0:
                cluster_risk = "high"
            elif best_cluster_dist <= 10.0:
                cluster_risk = "elevated"
            elif best_cluster_dist <= 20.0:
                cluster_risk = "moderate"

        # --- Known hotspot proximity ---
        hotspot_risk = "low"
        best_hs_dist: float = float("inf")
        best_hotspot: Optional[Dict[str, Any]] = None

        for hs in self.known_hotspots:
            dist = _haversine_km(lat, lng, float(hs["lat"]), float(hs["lng"]))
            if dist < best_hs_dist:
                best_hs_dist = dist
                best_hotspot = hs

        if best_hotspot is not None:
            hs_risk_level = best_hotspot.get("risk_level", "medium")
            if best_hs_dist <= 2.0:
                hotspot_risk = "critical" if hs_risk_level in ("high", "critical") else "high"
            elif best_hs_dist <= 5.0:
                hotspot_risk = "high" if hs_risk_level in ("high", "critical") else "elevated"
            elif best_hs_dist <= 15.0:
                hotspot_risk = "moderate"

        # --- Take the maximum risk ---
        final_risk = cluster_risk
        if risk_order.index(hotspot_risk) > risk_order.index(cluster_risk):
            final_risk = hotspot_risk

        result: Dict[str, Any] = {
            "risk_level": final_risk,
            "risk_score": risk_to_score.get(final_risk, 0.1),
            "state": _nearest_state(lat, lng),
        }

        if best_cluster is not None:
            result["nearest_cluster"] = best_cluster
            result["cluster_distance_km"] = round(best_cluster_dist, 3)

        if best_hotspot is not None:
            result["nearest_hotspot"] = best_hotspot.get("name", "Unknown")
            result["hotspot_distance_km"] = round(best_hs_dist, 3)

        result["distance_km"] = round(min(best_cluster_dist, best_hs_dist), 3)

        return result

    def get_state_risk(self, state: str) -> Dict[str, Any]:
        """Return aggregated risk data for a specific Indian state."""
        return self.state_risk.get(state, {
            "risk_level": "low",
            "risk_score": 0.0,
            "cluster_count": 0,
            "flagged_events": 0,
            "known_hotspots": 0,
        })

    def load_seed_data(self, filepath: str) -> None:
        """Load precomputed heatmap data from a JSON file.

        The file should contain a JSON object with optional keys
        ``heatmap_points`` (list of ``[lat, lng, intensity]`` or dicts),
        ``clusters`` (list of cluster dicts), and ``state_risk``.
        """

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Seed data file not found: {filepath}")

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # Support both list-of-lists and list-of-dicts formats for points.
        raw_points = data.get("heatmap_points", data.get("points", []))
        self.heatmap_points = []
        for p in raw_points:
            if isinstance(p, list):
                self.heatmap_points.append(p)
            elif isinstance(p, dict):
                self.heatmap_points.append([
                    p.get("lat", 0), p.get("lng", 0), p.get("intensity", 0),
                ])

        # Normalize cluster key names (seed generator uses centroid_lat/lng,
        # engine uses center_lat/lng).
        raw_clusters = data.get("clusters", [])
        for c in raw_clusters:
            if "centroid_lat" in c and "center_lat" not in c:
                c["center_lat"] = c["centroid_lat"]
                c["center_lng"] = c["centroid_lng"]
            if "member_count" in c and "event_count" not in c:
                c["event_count"] = c["member_count"]
            if "recent_count" in c and "recent_event_count" not in c:
                c["recent_event_count"] = c["recent_count"]
        self.clusters = raw_clusters
        self.state_risk = data.get("state_risk", {})

        # Load known hotspot activity if present in seed data
        raw_hotspot_activity = data.get("known_hotspot_activity", [])
        if raw_hotspot_activity:
            self._seed_hotspot_activity = raw_hotspot_activity

        # Load precomputed corridors if present
        raw_corridors = data.get("corridors", [])
        if raw_corridors:
            self._precomputed_corridors = raw_corridors

    # ----------------------------------------------------------------------- #
    #  Private helpers                                                         #
    # ----------------------------------------------------------------------- #

    def _compute_intensity(
        self,
        event: Dict[str, Any],
        reference_time: datetime,
    ) -> float:
        """Compute time-decayed intensity for a single scan event.

        ``intensity = base_intensity * exp(-ln2 * days_old / halflife)``
        """

        flag_type = event.get("flag_type", "normal")
        base_intensity = _INTENSITY_MAP.get(flag_type, 0.1)

        # Boost intensity if near a known hotspot.
        try:
            ev_lat = float(event["lat"])
            ev_lng = float(event["lng"])
            for hs in self.known_hotspots:
                dist = _haversine_km(ev_lat, ev_lng, float(hs["lat"]), float(hs["lng"]))
                if dist < 5.0:
                    hs_boost = {"critical": 1.5, "high": 1.3, "medium": 1.15, "low": 1.0}
                    base_intensity *= hs_boost.get(hs.get("risk_level", "medium"), 1.0)
                    break
        except (ValueError, KeyError):
            pass

        timestamp = event.get("timestamp")
        if timestamp is None:
            return round(base_intensity, 6)

        if isinstance(timestamp, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
                try:
                    timestamp = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:
                return round(base_intensity, 6)

        days_old = max((reference_time - timestamp).total_seconds() / 86400.0, 0.0)
        decay = math.exp(
            -math.log(2) * days_old / max(self.time_decay_halflife_days, 1e-9)
        )
        return round(base_intensity * decay, 6)

    def _find_clusters(
        self,
        flagged_events: List[Dict[str, Any]],
        reference_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Run DBSCAN on flagged events and return enriched cluster summaries.

        Each cluster includes a composite ``risk_score`` (0-1) combining:
        * Event density (count relative to max cluster).
        * Severity (avg of member severities).
        * Recency (fraction of events in last 7 days).
        * Known-hotspot proximity (boost if within 10 km).
        """

        if len(flagged_events) < self.min_samples:
            return []

        coords = np.array(
            [[float(e["lat"]), float(e["lng"])] for e in flagged_events],
            dtype=np.float64,
        )

        db = DBSCAN(
            eps=self.eps_degrees,
            min_samples=self.min_samples,
            metric="euclidean",
        ).fit(coords)

        labels = db.labels_
        unique_labels = set(labels)
        unique_labels.discard(-1)  # noise

        severity_map = {
            "flagged_low": 0.3,
            "flagged_medium": 0.5,
            "flagged_high": 0.8,
            "velocity_anomaly": 1.0,
            "velocity_violation": 1.0,
            "geographic_impossibility": 0.95,
            "reverse_flow": 0.85,
            "path_deviation": 0.80,
            "hotspot_routing": 0.90,
            "excessive_transfers": 0.70,
            "suspicious_timing": 0.65,
            "duplicate_scan": 0.60,
        }

        raw_clusters: List[Dict[str, Any]] = []
        max_count = 1

        for label in sorted(unique_labels):
            member_mask = labels == label
            member_coords = coords[member_mask]
            member_events = [
                e for e, m in zip(flagged_events, member_mask) if m
            ]

            center_lat = float(np.mean(member_coords[:, 0]))
            center_lng = float(np.mean(member_coords[:, 1]))
            count = int(np.sum(member_mask))
            max_count = max(max_count, count)

            # Cluster radius
            if len(member_coords) > 1:
                distances = np.array([
                    _haversine_km(center_lat, center_lng, float(c[0]), float(c[1]))
                    for c in member_coords
                ])
                radius_km = float(np.max(distances))
            else:
                radius_km = 0.0

            # Severities
            severities = [
                severity_map.get(e.get("flag_type", "flagged_low"), 0.3)
                for e in member_events
            ]
            flag_types = list(set(
                e.get("flag_type", "flagged_low") for e in member_events
            ))

            # Recency: fraction of events in last 7 days
            recent_count = 0
            if reference_time is not None:
                cutoff = reference_time - timedelta(days=7)
                for e in member_events:
                    ts = self._parse_timestamp(e.get("timestamp"))
                    if ts is not None and ts >= cutoff:
                        recent_count += 1
            recency_ratio = recent_count / max(count, 1)

            # Nearest known hotspot
            nearest_hs_dist = float("inf")
            nearest_hs_name = None
            for hs in self.known_hotspots:
                d = _haversine_km(center_lat, center_lng, float(hs["lat"]), float(hs["lng"]))
                if d < nearest_hs_dist:
                    nearest_hs_dist = d
                    nearest_hs_name = hs.get("name", "Unknown")

            state = _nearest_state(center_lat, center_lng)

            raw_clusters.append({
                "cluster_id": int(label),
                "center_lat": round(center_lat, 6),
                "center_lng": round(center_lng, 6),
                "radius_km": round(radius_km, 3),
                "event_count": count,
                "recent_event_count": recent_count,
                "recency_ratio": round(recency_ratio, 3),
                "avg_severity": round(float(np.mean(severities)), 4),
                "max_severity": round(float(np.max(severities)), 4),
                "flag_types": flag_types,
                "state": state,
                "nearest_known_hotspot": nearest_hs_name,
                "nearest_hotspot_km": round(nearest_hs_dist, 2) if nearest_hs_dist < float("inf") else None,
            })

        # Compute composite risk scores (normalized)
        for c in raw_clusters:
            density_score = min(c["event_count"] / max(max_count, 1), 1.0)
            severity_score = c["avg_severity"]
            recency_score = c["recency_ratio"]
            hotspot_boost = 0.0
            if c["nearest_hotspot_km"] is not None and c["nearest_hotspot_km"] < 10:
                hotspot_boost = max(0, 1.0 - c["nearest_hotspot_km"] / 10.0) * 0.2

            risk_score = (
                density_score * 0.25
                + severity_score * 0.30
                + recency_score * 0.30
                + 0.15  # base (any cluster is inherently somewhat risky)
                + hotspot_boost
            )
            c["risk_score"] = round(min(risk_score, 1.0), 4)

            # Risk label
            if risk_score >= 0.75:
                c["risk_label"] = "Critical hotspot"
            elif risk_score >= 0.55:
                c["risk_label"] = "High-risk cluster"
            elif risk_score >= 0.35:
                c["risk_label"] = "Medium-risk cluster"
            else:
                c["risk_label"] = "Low-risk cluster"

        # Sort by risk score descending
        raw_clusters.sort(key=lambda c: c["risk_score"], reverse=True)

        return raw_clusters

    def _assess_known_hotspots(
        self,
        flagged_events: List[Dict[str, Any]],
        reference_time: datetime,
    ) -> List[Dict[str, Any]]:
        """Assess recent activity near each known hotspot.

        Returns one entry per known hotspot with nearby event counts,
        trend direction, and effective risk level.
        """
        cutoff_7d = reference_time - timedelta(days=7)
        cutoff_30d = reference_time - timedelta(days=30)
        results: List[Dict[str, Any]] = []

        for hs in self.known_hotspots:
            hs_lat = float(hs["lat"])
            hs_lng = float(hs["lng"])
            radius_km = 10.0  # 10 km scan radius around known hotspots

            events_7d = 0
            events_30d = 0
            total_nearby = 0

            for e in flagged_events:
                try:
                    e_lat = float(e["lat"])
                    e_lng = float(e["lng"])
                except (ValueError, KeyError):
                    continue

                dist = _haversine_km(hs_lat, hs_lng, e_lat, e_lng)
                if dist > radius_km:
                    continue

                total_nearby += 1
                ts = self._parse_timestamp(e.get("timestamp"))
                if ts is not None:
                    if ts >= cutoff_7d:
                        events_7d += 1
                    if ts >= cutoff_30d:
                        events_30d += 1

            # Trend: compare last 7 days vs weekly average over 30 days
            weekly_avg_30d = events_30d / 4.0 if events_30d > 0 else 0
            if events_7d > weekly_avg_30d * 1.5 and events_7d >= 3:
                trend = "increasing"
            elif events_7d < weekly_avg_30d * 0.5:
                trend = "decreasing"
            else:
                trend = "stable"

            # Effective risk combines baseline + recent activity
            baseline_risk = {"low": 0.2, "medium": 0.4, "high": 0.6, "critical": 0.8}
            base = baseline_risk.get(hs.get("risk_level", "medium"), 0.4)
            activity_boost = min(events_7d / 20.0, 0.4)
            effective_risk = min(base + activity_boost, 1.0)

            if effective_risk >= 0.75:
                level = "critical"
            elif effective_risk >= 0.55:
                level = "high"
            elif effective_risk >= 0.35:
                level = "medium"
            else:
                level = "low"

            results.append({
                "name": hs.get("name", "Unknown"),
                "lat": hs_lat,
                "lng": hs_lng,
                "state": hs.get("state", _nearest_state(hs_lat, hs_lng)),
                "baseline_risk": hs.get("risk_level", "medium"),
                "recent_events": events_7d,
                "monthly_events": events_30d,
                "total_nearby": total_nearby,
                "trend": trend,
                "effective_risk_score": round(effective_risk, 3),
                "effective_risk_level": level,
            })

        # Sort by effective risk descending
        results.sort(key=lambda h: h["effective_risk_score"], reverse=True)
        return results

    def _aggregate_state_risk(
        self,
        clusters: List[Dict[str, Any]],
        hotspot_activity: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Roll up cluster and hotspot data into per-state risk summaries."""
        state_data: Dict[str, Dict[str, Any]] = {}

        # Initialize from clusters
        for c in clusters:
            state = c.get("state", "Unknown")
            if state not in state_data:
                state_data[state] = {
                    "cluster_count": 0,
                    "total_events": 0,
                    "max_cluster_risk": 0.0,
                    "known_hotspots_active": 0,
                    "cluster_risk_sum": 0.0,
                }
            sd = state_data[state]
            sd["cluster_count"] += 1
            sd["total_events"] += c["event_count"]
            sd["max_cluster_risk"] = max(sd["max_cluster_risk"], c["risk_score"])
            sd["cluster_risk_sum"] += c["risk_score"]

        # Add known hotspot activity
        for ha in hotspot_activity:
            state = ha.get("state", "Unknown")
            if state not in state_data:
                state_data[state] = {
                    "cluster_count": 0,
                    "total_events": 0,
                    "max_cluster_risk": 0.0,
                    "known_hotspots_active": 0,
                    "cluster_risk_sum": 0.0,
                }
            if ha["recent_events"] > 0:
                state_data[state]["known_hotspots_active"] += 1

        # Compute state-level risk scores
        result: Dict[str, Dict[str, Any]] = {}
        for state, sd in state_data.items():
            cc = sd["cluster_count"]
            avg_risk = sd["cluster_risk_sum"] / max(cc, 1)
            hs_active = sd["known_hotspots_active"]

            # State risk = weighted combination
            state_score = (
                min(cc / 5.0, 1.0) * 0.30          # cluster density
                + avg_risk * 0.40                     # avg cluster severity
                + min(hs_active / 3.0, 1.0) * 0.30   # known hotspot activity
            )
            state_score = min(state_score, 1.0)

            if state_score >= 0.65:
                level = "critical"
            elif state_score >= 0.45:
                level = "high"
            elif state_score >= 0.25:
                level = "medium"
            else:
                level = "low"

            result[state] = {
                "risk_level": level,
                "risk_score": round(state_score, 3),
                "cluster_count": cc,
                "flagged_events": sd["total_events"],
                "known_hotspots_active": hs_active,
                "max_cluster_risk": round(sd["max_cluster_risk"], 3),
            }

        return result

    def _weekly_cluster_snapshots(
        self,
        flagged_events: List[Dict[str, Any]],
        reference_time: datetime,
        num_weeks: int = 6,
    ) -> List[List[Dict[str, Any]]]:
        """Run DBSCAN on cumulative weekly windows to observe cluster growth."""

        weekly_snapshots: List[List[Dict[str, Any]]] = []

        for week_idx in range(num_weeks):
            cutoff = reference_time - timedelta(weeks=num_weeks - 1 - week_idx)

            windowed_events: List[Dict[str, Any]] = []
            for event in flagged_events:
                ts = self._parse_timestamp(event.get("timestamp"))
                if ts is None or ts <= cutoff:
                    windowed_events.append(event)

            snapshot_clusters = self._find_clusters(windowed_events)
            weekly_snapshots.append(snapshot_clusters)

        return weekly_snapshots

    def _predict_hotspots(
        self,
        current_clusters: List[Dict[str, Any]],
        weekly_cluster_data: List[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Predict which clusters are likely to grow into major hotspots.

        Uses Holt's double exponential smoothing (level + trend) for more
        robust prediction than simple linear regression.  Also accounts for
        known-hotspot proximity as a risk amplifier.
        """

        if not current_clusters or not weekly_cluster_data:
            return []

        num_weeks = len(weekly_cluster_data)
        predictions: List[Dict[str, Any]] = []

        for cluster in current_clusters:
            c_lat = cluster["center_lat"]
            c_lng = cluster["center_lng"]

            # Build a time series of event counts across weekly snapshots.
            counts: List[float] = []
            for snapshot in weekly_cluster_data:
                matched_count = 0
                best_dist = float("inf")
                for sc in snapshot:
                    dist_deg = math.sqrt(
                        (sc["center_lat"] - c_lat) ** 2
                        + (sc["center_lng"] - c_lng) ** 2
                    )
                    if dist_deg < best_dist:
                        best_dist = dist_deg
                        matched_count = sc["event_count"]
                if best_dist <= self.eps_degrees * 3:
                    counts.append(float(matched_count))
                else:
                    counts.append(0.0)

            n = len(counts)
            if n < 2:
                continue

            # Holt's double exponential smoothing
            alpha = 0.4  # level smoothing
            beta = 0.3   # trend smoothing

            level = counts[0]
            trend = counts[1] - counts[0] if n > 1 else 0.0

            for i in range(1, n):
                new_level = alpha * counts[i] + (1 - alpha) * (level + trend)
                new_trend = beta * (new_level - level) + (1 - beta) * trend
                level = new_level
                trend = new_trend

            # Predict 2 weeks ahead
            predicted_count_2w = max(level + 2 * trend, 0.0)
            current_count = cluster["event_count"]

            # Confidence: higher when trend is consistent
            if n >= 3:
                diffs = [counts[i] - counts[i-1] for i in range(1, n)]
                trend_consistency = 1.0 - (np.std(diffs) / (abs(np.mean(diffs)) + 1e-9))
                confidence = max(0.0, min(1.0, trend_consistency))
            else:
                confidence = 0.3

            # Growth rate per week
            growth_rate = trend

            # Known-hotspot amplifier
            hs_amplifier = 1.0
            if cluster.get("nearest_hotspot_km") is not None and cluster["nearest_hotspot_km"] < 10:
                hs_amplifier = 1.3

            predicted_count_2w *= hs_amplifier

            # Flag conditions: growth > 50% OR near known hotspot with growth > 25%
            growth_pct = (predicted_count_2w - current_count) / max(current_count, 1) * 100
            is_emerging = (
                (growth_pct >= 50 and current_count > 0)
                or (growth_pct >= 25 and hs_amplifier > 1.0)
                or (growth_rate > 3)
            )

            severity = "critical" if growth_pct >= 100 else "high" if growth_pct >= 50 else "medium"

            alert = ""
            if is_emerging:
                alert = (
                    f"Cluster near {cluster.get('state', 'Unknown')} "
                    f"({c_lat:.4f}, {c_lng:.4f}) predicted to grow from "
                    f"{current_count} to ~{predicted_count_2w:.0f} events "
                    f"in 2 weeks ({growth_pct:+.0f}%, "
                    f"trend: {growth_rate:+.1f}/week)."
                )
                if hs_amplifier > 1.0:
                    alert += f" Near known hotspot: {cluster.get('nearest_known_hotspot', 'Unknown')}."

            if is_emerging or growth_rate > 0:
                predictions.append({
                    "cluster_id": cluster["cluster_id"],
                    "center_lat": c_lat,
                    "center_lng": c_lng,
                    "state": cluster.get("state", "Unknown"),
                    "current_count": current_count,
                    "predicted_count_2w": round(predicted_count_2w, 1),
                    "growth_rate_per_week": round(growth_rate, 2),
                    "growth_pct": round(growth_pct, 1),
                    "confidence": round(confidence, 3),
                    "severity": severity,
                    "near_known_hotspot": hs_amplifier > 1.0,
                    "is_emerging": is_emerging,
                    "alert": alert,
                })

        # Sort: emerging first, then by growth rate
        predictions.sort(key=lambda p: (not p["is_emerging"], -p["growth_rate_per_week"]))
        return predictions

    # ----------------------------------------------------------------------- #
    #  Route-corridor risk                                                     #
    # ----------------------------------------------------------------------- #

    def compute_route_corridor_risk(
        self,
        supply_chain_events: List[Dict[str, Any]],
        num_interpolation_points: int = 10,
    ) -> List[Dict[str, Any]]:
        """Compute risk along supply-chain route corridors.

        Instead of just marking cities, this interpolates points BETWEEN
        origin and destination and computes corridor-level risk.  This
        reveals which transport corridors (e.g., NH-44 Delhi-Mumbai) are
        high-risk, not just the endpoints.

        Parameters
        ----------
        supply_chain_events:
            List of dicts with ``from_lat``, ``from_lng``, ``to_lat``,
            ``to_lng``, ``is_anomaly`` (0/1), ``anomaly_type`` (str),
            ``batch_id`` (str).
        num_interpolation_points:
            How many intermediate points to sample along each route.

        Returns
        -------
        list[dict]
            Each entry: ``corridor_id``, ``from_city``, ``to_city``,
            ``waypoints`` (list of [lat, lng, risk]), ``corridor_risk``,
            ``anomaly_count``, ``total_shipments``.
        """
        # Group events by corridor (from->to, rounded to 0.5 degree grid)
        corridors: Dict[str, Dict[str, Any]] = {}

        for event in supply_chain_events:
            try:
                f_lat = float(event["from_lat"])
                f_lng = float(event["from_lng"])
                t_lat = float(event["to_lat"])
                t_lng = float(event["to_lng"])
            except (ValueError, KeyError):
                continue

            # Round to 0.5-degree grid to group nearby routes
            key = (
                round(f_lat * 2) / 2, round(f_lng * 2) / 2,
                round(t_lat * 2) / 2, round(t_lng * 2) / 2,
            )
            key_str = f"{key[0]},{key[1]}->{key[2]},{key[3]}"

            if key_str not in corridors:
                corridors[key_str] = {
                    "from_lat": f_lat, "from_lng": f_lng,
                    "to_lat": t_lat, "to_lng": t_lng,
                    "total": 0, "anomalous": 0,
                    "anomaly_types": [],
                }
            c = corridors[key_str]
            c["total"] += 1
            is_anom = str(event.get("is_anomaly", "0"))
            if is_anom in ("1", "True", "true"):
                c["anomalous"] += 1
                atype = event.get("anomaly_type", "unknown")
                if atype:
                    c["anomaly_types"].append(atype)

        # Build corridor risk with interpolated waypoints
        result: List[Dict[str, Any]] = []
        for idx, (key_str, c) in enumerate(corridors.items()):
            if c["total"] < 2:
                continue

            anomaly_rate = c["anomalous"] / c["total"]

            # Interpolate waypoints between origin and destination
            waypoints: List[List[float]] = []
            for step in range(num_interpolation_points + 1):
                t = step / num_interpolation_points
                wp_lat = c["from_lat"] + t * (c["to_lat"] - c["from_lat"])
                wp_lng = c["from_lng"] + t * (c["to_lng"] - c["from_lng"])

                # Point risk = corridor anomaly rate + cluster/hotspot proximity boost
                zone = self.get_zone_risk_level(wp_lat, wp_lng)
                zone_score = zone.get("risk_score", 0.1)
                point_risk = min(anomaly_rate * 0.6 + zone_score * 0.4, 1.0)

                waypoints.append([round(wp_lat, 6), round(wp_lng, 6), round(point_risk, 4)])

            corridor_risk = float(np.mean([w[2] for w in waypoints]))

            if corridor_risk >= 0.5:
                risk_level = "high"
            elif corridor_risk >= 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"

            from_state = _nearest_state(c["from_lat"], c["from_lng"])
            to_state = _nearest_state(c["to_lat"], c["to_lng"])
            distance_km = _haversine_km(
                c["from_lat"], c["from_lng"], c["to_lat"], c["to_lng"],
            )

            result.append({
                "corridor_id": idx,
                "from_state": from_state,
                "to_state": to_state,
                "from_coords": [round(c["from_lat"], 4), round(c["from_lng"], 4)],
                "to_coords": [round(c["to_lat"], 4), round(c["to_lng"], 4)],
                "distance_km": round(distance_km, 1),
                "waypoints": waypoints,
                "corridor_risk": round(corridor_risk, 4),
                "risk_level": risk_level,
                "total_shipments": c["total"],
                "anomaly_count": c["anomalous"],
                "anomaly_rate": round(anomaly_rate, 4),
                "anomaly_types": list(set(c["anomaly_types"])),
            })

        result.sort(key=lambda r: r["corridor_risk"], reverse=True)
        return result

    # ----------------------------------------------------------------------- #
    #  Batch backtracking                                                      #
    # ----------------------------------------------------------------------- #

    def backtrace_batch(
        self,
        batch_id: str,
        supply_chain_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Trace a flagged batch back through the supply chain.

        Given a batch_id, finds all transactions involving that batch,
        reconstructs the chain, and identifies the common origin
        (manufacturer/factory).  This is the "backtracking" feature from
        the pitch: if bad batches appear in Delhi, Mumbai, and Chennai,
        trace them all back to the same factory.

        Parameters
        ----------
        batch_id:
            The batch identifier to trace.
        supply_chain_events:
            Full list of supply-chain events (dicts with ``batch_id``,
            ``from_actor``, ``to_actor``, ``from_lat``, ``from_lng``,
            ``to_lat``, ``to_lng``, ``timestamp``, ``is_anomaly``,
            ``anomaly_type``).

        Returns
        -------
        dict
            ``batch_id``, ``origin`` (factory info), ``chain`` (ordered
            list of transfers), ``affected_cities`` (endpoints where batch
            was flagged), ``total_transfers``, ``anomaly_count``,
            ``risk_assessment``.
        """
        # Filter events for this batch
        batch_events = [
            e for e in supply_chain_events
            if e.get("batch_id") == batch_id
        ]

        if not batch_events:
            return {
                "batch_id": batch_id,
                "error": "Batch not found",
                "chain": [],
            }

        # Sort by timestamp to reconstruct the chain
        def _parse_ts(e):
            ts = e.get("timestamp", "")
            try:
                return datetime.fromisoformat(ts) if ts else datetime.min
            except ValueError:
                return datetime.min

        batch_events.sort(key=_parse_ts)

        # Build the chain
        chain: List[Dict[str, Any]] = []
        anomaly_count = 0
        affected_locations: List[Dict[str, Any]] = []
        actors_seen: List[str] = []

        for e in batch_events:
            is_anom = str(e.get("is_anomaly", "0")) in ("1", "True", "true")
            if is_anom:
                anomaly_count += 1

            from_actor = e.get("from_actor", "Unknown")
            to_actor = e.get("to_actor", "Unknown")

            try:
                from_lat = float(e.get("from_lat", 0))
                from_lng = float(e.get("from_lng", 0))
                to_lat = float(e.get("to_lat", 0))
                to_lng = float(e.get("to_lng", 0))
            except (ValueError, TypeError):
                from_lat = from_lng = to_lat = to_lng = 0.0

            transfer = {
                "step": len(chain) + 1,
                "from_actor": from_actor,
                "to_actor": to_actor,
                "from_coords": [round(from_lat, 4), round(from_lng, 4)],
                "to_coords": [round(to_lat, 4), round(to_lng, 4)],
                "from_state": _nearest_state(from_lat, from_lng),
                "to_state": _nearest_state(to_lat, to_lng),
                "timestamp": e.get("timestamp", ""),
                "is_anomaly": is_anom,
                "anomaly_type": e.get("anomaly_type", ""),
                "transfer_velocity_kmh": float(e.get("transfer_velocity_kmh", 0)),
            }
            chain.append(transfer)

            if from_actor not in actors_seen:
                actors_seen.append(from_actor)
            if to_actor not in actors_seen:
                actors_seen.append(to_actor)

            # Track endpoint locations (final destinations)
            affected_locations.append({
                "lat": to_lat,
                "lng": to_lng,
                "state": _nearest_state(to_lat, to_lng),
                "actor": to_actor,
            })

        # Origin = first "from" actor in the chain (manufacturer)
        origin = {
            "actor": chain[0]["from_actor"] if chain else "Unknown",
            "coords": chain[0]["from_coords"] if chain else [0, 0],
            "state": chain[0]["from_state"] if chain else "Unknown",
        }

        # Unique affected cities (deduplicated by state)
        seen_states = set()
        unique_affected = []
        for loc in affected_locations:
            if loc["state"] not in seen_states:
                seen_states.add(loc["state"])
                unique_affected.append(loc)

        # Risk assessment
        anomaly_rate = anomaly_count / max(len(batch_events), 1)
        if anomaly_rate >= 0.5:
            risk_level = "critical"
        elif anomaly_rate >= 0.25:
            risk_level = "high"
        elif anomaly_rate > 0:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "batch_id": batch_id,
            "origin": origin,
            "chain": chain,
            "total_transfers": len(chain),
            "anomaly_count": anomaly_count,
            "anomaly_rate": round(anomaly_rate, 4),
            "risk_level": risk_level,
            "affected_locations": unique_affected,
            "actors_involved": actors_seen,
        }

    def backtrace_common_origin(
        self,
        batch_ids: List[str],
        supply_chain_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Find common origins across multiple flagged batches.

        The pitch scenario: bad batches in Delhi, Mumbai, and Chennai all
        trace back to the same factory.  This method finds that pattern.

        Parameters
        ----------
        batch_ids:
            List of batch IDs to investigate.
        supply_chain_events:
            Full list of supply-chain events.

        Returns
        -------
        dict
            ``batches`` (individual traces), ``common_origins`` (factories
            that appear across multiple batches), ``pattern_detected``
            (bool), ``alert`` (human-readable summary).
        """
        traces: List[Dict[str, Any]] = []
        origin_to_batches: Dict[str, List[str]] = {}

        for bid in batch_ids:
            trace = self.backtrace_batch(bid, supply_chain_events)
            traces.append(trace)

            origin_actor = trace.get("origin", {}).get("actor", "Unknown")
            if origin_actor != "Unknown":
                if origin_actor not in origin_to_batches:
                    origin_to_batches[origin_actor] = []
                origin_to_batches[origin_actor].append(bid)

        # Find origins that appear in multiple batches
        common_origins: List[Dict[str, Any]] = []
        for actor, bids in origin_to_batches.items():
            if len(bids) >= 2:
                # Find the origin coordinates from traces
                origin_info = None
                for t in traces:
                    if t.get("origin", {}).get("actor") == actor:
                        origin_info = t["origin"]
                        break

                all_affected = []
                for t in traces:
                    if t.get("origin", {}).get("actor") == actor:
                        all_affected.extend(t.get("affected_locations", []))

                common_origins.append({
                    "factory": actor,
                    "coords": origin_info.get("coords", [0, 0]) if origin_info else [0, 0],
                    "state": origin_info.get("state", "Unknown") if origin_info else "Unknown",
                    "batch_count": len(bids),
                    "batch_ids": bids,
                    "affected_locations": all_affected,
                })

        pattern_detected = len(common_origins) > 0
        alert = ""
        if pattern_detected:
            for co in common_origins:
                states = list(set(
                    loc["state"] for loc in co["affected_locations"]
                ))
                alert += (
                    f"ALERT: {co['factory']} in {co['state']} is the common "
                    f"origin for {co['batch_count']} flagged batches affecting "
                    f"{', '.join(states)}. "
                )

        return {
            "batches": traces,
            "common_origins": common_origins,
            "pattern_detected": pattern_detected,
            "alert": alert.strip(),
        }

    # ----------------------------------------------------------------------- #
    #  Utilities                                                               #
    # ----------------------------------------------------------------------- #

    @staticmethod
    def _parse_timestamp(raw: Any) -> Optional[datetime]:
        """Best-effort parse of a timestamp value."""
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
        return None
