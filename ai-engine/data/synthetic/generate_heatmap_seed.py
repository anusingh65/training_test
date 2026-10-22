"""
Heatmap seed-data generator for MediChain.

Reads ``scan_events.csv`` and ``supply_chain_transactions.csv`` to produce
a comprehensive heatmap seed with:

* Time-decayed intensity points from scan events.
* **All 8 anomaly types** injected from supply-chain data (not just velocity).
* Known-hotspot baseline ambient signals.
* DBSCAN clusters with composite risk scores.
* State-level risk aggregation.
* Known-hotspot activity reports with trend detection.

Intensity mapping
-----------------
* Normal (unflagged) scan:           0.10
* Flagged -- severity ``low``:       0.30
* Flagged -- severity ``medium``:    0.50
* Flagged -- severity ``high``:      0.80
* velocity_violation:                1.00
* geographic_impossibility:          0.95
* hotspot_routing:                   0.90
* reverse_flow:                      0.85
* path_deviation:                    0.80
* excessive_transfers:               0.70
* suspicious_timing:                 0.65
* duplicate_scan:                    0.60

Output
------
``data/synthetic/heatmap_seed.json``

Usage
-----
    python -m data.synthetic.generate_heatmap_seed
    python -m data.synthetic.generate_heatmap_seed --half-life 14
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
#  Path setup
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_AI_ENGINE_DIR = _THIS_DIR.parent.parent

if str(_AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_DIR))

from config import SYNTHETIC_DIR

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

INTENSITY_NORMAL         = 0.10
INTENSITY_FLAG_LOW       = 0.30
INTENSITY_FLAG_MEDIUM    = 0.50
INTENSITY_FLAG_HIGH      = 0.80

# All supply-chain anomaly type intensities
ANOMALY_TYPE_INTENSITY: Dict[str, float] = {
    "velocity_violation": 1.00,
    "geographic_impossibility": 0.95,
    "hotspot_routing": 0.90,
    "reverse_flow": 0.85,
    "path_deviation": 0.80,
    "excessive_transfers": 0.70,
    "suspicious_timing": 0.65,
    "duplicate_scan": 0.60,
}

SEVERITY_INTENSITY_MAP = {
    "":       INTENSITY_NORMAL,
    "low":    INTENSITY_FLAG_LOW,
    "medium": INTENSITY_FLAG_MEDIUM,
    "high":   INTENSITY_FLAG_HIGH,
}

DEFAULT_HALF_LIFE_DAYS = 7.0

# DBSCAN parameters (in degree-space; 0.3 deg ~ 33 km at Indian latitudes).
DBSCAN_EPS = 0.3
DBSCAN_MIN_SAMPLES = 5

EARTH_RADIUS_KM = 6371.0

# Indian state centroids for state assignment
_INDIA_STATES: Dict[str, tuple] = {
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


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2.0) ** 2
    )
    return EARTH_RADIUS_KM * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _nearest_state(lat: float, lng: float) -> str:
    best_state = "Unknown"
    best_dist = float("inf")
    for state, (s_lat, s_lng) in _INDIA_STATES.items():
        d = (lat - s_lat) ** 2 + (lng - s_lng) ** 2
        if d < best_dist:
            best_dist = d
            best_state = state
    return best_state


def _decay_weight(
    base_intensity: float,
    event_time: datetime,
    reference_time: datetime,
    half_life_days: float,
) -> float:
    delta_days = (reference_time - event_time).total_seconds() / 86400.0
    if delta_days < 0:
        delta_days = 0.0
    return base_intensity * (2.0 ** (-delta_days / half_life_days))


# ---------------------------------------------------------------------------
#  DBSCAN
# ---------------------------------------------------------------------------

def _run_dbscan(coords: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    try:
        from sklearn.cluster import DBSCAN
        model = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
        return model.fit_predict(coords)
    except ImportError:
        # Pure-numpy fallback for environments without sklearn
        n = len(coords)
        labels = np.full(n, -1, dtype=int)
        visited = np.zeros(n, dtype=bool)
        cluster_id = 0

        def _region_query(idx: int) -> List[int]:
            diffs = coords - coords[idx]
            dists = np.sqrt(np.sum(diffs ** 2, axis=1))
            return list(np.where(dists <= eps)[0])

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            neighbours = _region_query(i)
            if len(neighbours) < min_samples:
                continue
            labels[i] = cluster_id
            seed_set = list(neighbours)
            j = 0
            while j < len(seed_set):
                q = seed_set[j]
                if not visited[q]:
                    visited[q] = True
                    q_neighbours = _region_query(q)
                    if len(q_neighbours) >= min_samples:
                        seed_set.extend(q_neighbours)
                if labels[q] == -1:
                    labels[q] = cluster_id
                j += 1
            cluster_id += 1
        return labels


# ---------------------------------------------------------------------------
#  Supply-chain anomaly loader (ALL anomaly types)
# ---------------------------------------------------------------------------

def _load_supply_chain_anomalies() -> List[Dict[str, Any]]:
    """Load ALL anomalous transactions from supply_chain_transactions.csv.

    Returns a list of dicts with lat, lng, timestamp, anomaly_type for each
    anomalous row.  Returns an empty list if the file does not exist.
    """
    sc_path = SYNTHETIC_DIR / "supply_chain_transactions.csv"
    if not sc_path.exists():
        return []

    alerts: List[Dict[str, Any]] = []
    with open(sc_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("is_anomaly") != "1":
                continue
            anomaly_type = row.get("anomaly_type", "").strip()
            if not anomaly_type:
                continue
            try:
                alerts.append({
                    "lat": float(row["to_lat"]),
                    "lng": float(row["to_lng"]),
                    "timestamp": row["timestamp"],
                    "anomaly_type": anomaly_type,
                })
            except (ValueError, KeyError):
                continue
    return alerts


# ---------------------------------------------------------------------------
#  Known hotspot loader
# ---------------------------------------------------------------------------

def _load_known_hotspots() -> List[Dict[str, Any]]:
    """Load known hotspots from indian_pharma_hubs.json."""
    hubs_path = _THIS_DIR / "indian_pharma_hubs.json"
    if not hubs_path.exists():
        return []
    try:
        with open(hubs_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("known_hotspots", [])
    except (json.JSONDecodeError, KeyError):
        return []


# ---------------------------------------------------------------------------
#  Main generator
# ---------------------------------------------------------------------------


def generate_heatmap_seed(
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
    dbscan_eps: float = DBSCAN_EPS,
    dbscan_min_samples: int = DBSCAN_MIN_SAMPLES,
) -> Path:
    """Read scan_events.csv + supply_chain_transactions.csv and compute
    a comprehensive heatmap seed JSON.

    Returns
    -------
    Path
        Path to the output JSON file.
    """
    scan_path = SYNTHETIC_DIR / "scan_events.csv"
    out_path = SYNTHETIC_DIR / "heatmap_seed.json"

    if not scan_path.exists():
        print(f"[Heatmap] ERROR: {scan_path} not found. Run generate_scan_events first.")
        sys.exit(1)

    # --- Read scan events ----------------------------------------------------
    print(f"[Heatmap] Reading scan events from {scan_path} ...")
    events: List[Dict[str, Any]] = []
    with open(scan_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            events.append(row)

    print(f"[Heatmap] Loaded {len(events)} scan events.")

    # Determine reference time (latest event timestamp).
    timestamps = []
    for e in events:
        try:
            timestamps.append(datetime.fromisoformat(e["timestamp"]))
        except (ValueError, KeyError):
            continue

    if not timestamps:
        print("[Heatmap] ERROR: No valid timestamps found.")
        sys.exit(1)

    reference_time = max(timestamps)
    print(f"[Heatmap] Reference time: {reference_time.isoformat()}")

    # --- Compute intensity per scan-event point ------------------------------
    points: List[Dict[str, Any]] = []

    for e in events:
        try:
            lat = float(e["latitude"])
            lng = float(e["longitude"])
            ts = datetime.fromisoformat(e["timestamp"])
        except (ValueError, KeyError):
            continue

        is_flagged = e.get("is_flagged", "0") in ("1", "True", "true")
        severity = e.get("flag_severity", "").strip().lower()

        if is_flagged:
            base_intensity = SEVERITY_INTENSITY_MAP.get(severity, INTENSITY_FLAG_LOW)
            category = f"flagged_{severity}" if severity else "flagged"
        else:
            base_intensity = INTENSITY_NORMAL
            category = "normal"

        intensity = _decay_weight(base_intensity, ts, reference_time, half_life_days)

        points.append({
            "lat": lat,
            "lng": lng,
            "intensity": round(intensity, 6),
            "timestamp": ts.isoformat(),
            "category": category,
        })

    # --- Inject ALL supply-chain anomalies -----------------------------------
    sc_anomalies = _load_supply_chain_anomalies()
    anomaly_type_counts: Dict[str, int] = {}

    if sc_anomalies:
        print(f"[Heatmap] Enriching with {len(sc_anomalies)} supply-chain anomalies "
              f"(all 8 types).")
        for sa in sc_anomalies:
            anomaly_type = sa["anomaly_type"]
            base = ANOMALY_TYPE_INTENSITY.get(anomaly_type, 0.60)
            anomaly_type_counts[anomaly_type] = anomaly_type_counts.get(anomaly_type, 0) + 1

            try:
                ts = datetime.fromisoformat(sa["timestamp"])
            except (ValueError, KeyError):
                ts = reference_time

            intensity = _decay_weight(base, ts, reference_time, half_life_days)
            points.append({
                "lat": sa["lat"],
                "lng": sa["lng"],
                "intensity": round(intensity, 6),
                "timestamp": ts.isoformat(),
                "category": anomaly_type,
            })

        print(f"[Heatmap] Anomaly type breakdown: {json.dumps(anomaly_type_counts)}")

    # --- Inject known-hotspot ambient baseline --------------------------------
    known_hotspots = _load_known_hotspots()
    if known_hotspots:
        print(f"[Heatmap] Injecting {len(known_hotspots)} known-hotspot baselines.")
        ambient_map = {"low": 0.15, "medium": 0.30, "high": 0.50, "critical": 0.70}
        for hs in known_hotspots:
            risk_level = hs.get("risk_level", "medium")
            base = ambient_map.get(risk_level, 0.30)
            points.append({
                "lat": float(hs["lat"]),
                "lng": float(hs["lng"]),
                "intensity": base,
                "timestamp": reference_time.isoformat(),
                "category": f"known_hotspot_{risk_level}",
            })

    print(f"[Heatmap] Total heatmap points: {len(points)}")

    # --- DBSCAN clustering on flagged + anomaly points -----------------------
    flagged_points = [p for p in points if p["category"] not in ("normal",)]
    print(f"[Heatmap] Running DBSCAN on {len(flagged_points)} non-normal points "
          f"(eps={dbscan_eps}, min_samples={dbscan_min_samples}) ...")

    clusters: List[Dict[str, Any]] = []

    if len(flagged_points) >= dbscan_min_samples:
        coords = np.array([[p["lat"], p["lng"]] for p in flagged_points])
        labels = _run_dbscan(coords, dbscan_eps, dbscan_min_samples)

        unique_labels = set(labels)
        unique_labels.discard(-1)  # noise

        severity_map = {
            "flagged_high": 0.8, "flagged_medium": 0.5, "flagged_low": 0.3,
            "velocity_violation": 1.0, "geographic_impossibility": 0.95,
            "hotspot_routing": 0.90, "reverse_flow": 0.85,
            "path_deviation": 0.80, "excessive_transfers": 0.70,
            "suspicious_timing": 0.65, "duplicate_scan": 0.60,
            "known_hotspot_critical": 0.70, "known_hotspot_high": 0.50,
            "known_hotspot_medium": 0.30, "known_hotspot_low": 0.15,
        }

        max_count = max(
            (int((labels == cid).sum()) for cid in unique_labels),
            default=1,
        )

        for cid in sorted(unique_labels):
            member_mask = labels == cid
            member_coords = coords[member_mask]
            member_indices = [i for i, m in enumerate(member_mask) if m]

            centroid_lat = float(np.mean(member_coords[:, 0]))
            centroid_lng = float(np.mean(member_coords[:, 1]))
            count = int(member_mask.sum())

            # Compute radius
            if len(member_coords) > 1:
                dists = np.array([
                    _haversine_km(centroid_lat, centroid_lng, float(c[0]), float(c[1]))
                    for c in member_coords
                ])
                radius_km = float(np.max(dists))
            else:
                radius_km = 0.0

            # Severity analysis
            severities = []
            categories = []
            member_pts = []
            for idx in member_indices:
                fp = flagged_points[idx]
                cat = fp["category"]
                categories.append(cat)
                sev = severity_map.get(cat, 0.3)
                severities.append(sev)
                member_pts.append({
                    "lat": fp["lat"], "lng": fp["lng"], "intensity": fp["intensity"],
                })

            cat_counter = Counter(categories)
            dominant_category = cat_counter.most_common(1)[0][0] if cat_counter else "unknown"

            # Determine dominant severity
            sev_labels = []
            for s in severities:
                if s >= 0.8:
                    sev_labels.append("high")
                elif s >= 0.5:
                    sev_labels.append("medium")
                else:
                    sev_labels.append("low")
            sev_counter = Counter(sev_labels)
            dominant_severity = sev_counter.most_common(1)[0][0] if sev_counter else "low"

            # Recency (events in last 7 days)
            recent_count = 0
            from datetime import timedelta
            cutoff_7d = reference_time - timedelta(days=7)
            for idx in member_indices:
                fp = flagged_points[idx]
                try:
                    ts = datetime.fromisoformat(fp["timestamp"])
                    if ts >= cutoff_7d:
                        recent_count += 1
                except (ValueError, KeyError):
                    pass
            recency_ratio = recent_count / max(count, 1)

            # Nearest known hotspot
            nearest_hs_dist = float("inf")
            nearest_hs_name = None
            for hs in known_hotspots:
                d = _haversine_km(centroid_lat, centroid_lng, float(hs["lat"]), float(hs["lng"]))
                if d < nearest_hs_dist:
                    nearest_hs_dist = d
                    nearest_hs_name = hs.get("name", "Unknown")

            state = _nearest_state(centroid_lat, centroid_lng)

            # Composite risk score
            density_score = min(count / max(max_count, 1), 1.0)
            severity_score = float(np.mean(severities))
            hotspot_boost = 0.0
            if nearest_hs_dist < 10:
                hotspot_boost = max(0, 1.0 - nearest_hs_dist / 10.0) * 0.2

            risk_score = (
                density_score * 0.25
                + severity_score * 0.30
                + recency_ratio * 0.30
                + 0.15
                + hotspot_boost
            )
            risk_score = min(risk_score, 1.0)

            if risk_score >= 0.75:
                risk_label = "Critical hotspot"
            elif risk_score >= 0.55:
                risk_label = "High-risk cluster"
            elif risk_score >= 0.35:
                risk_label = "Medium-risk cluster"
            else:
                risk_label = "Low-risk cluster"

            clusters.append({
                "cluster_id": int(cid),
                "centroid_lat": round(centroid_lat, 6),
                "centroid_lng": round(centroid_lng, 6),
                "radius_km": round(radius_km, 3),
                "member_count": count,
                "recent_count": recent_count,
                "recency_ratio": round(recency_ratio, 3),
                "dominant_severity": dominant_severity,
                "dominant_category": dominant_category,
                "avg_severity": round(float(np.mean(severities)), 4),
                "risk_score": round(risk_score, 4),
                "risk_label": risk_label,
                "state": state,
                "nearest_known_hotspot": nearest_hs_name,
                "nearest_hotspot_km": round(nearest_hs_dist, 2) if nearest_hs_dist < float("inf") else None,
                "category_breakdown": dict(cat_counter.most_common()),
                "member_points": member_pts,
            })

        # Sort by risk score
        clusters.sort(key=lambda c: c["risk_score"], reverse=True)

        print(f"[Heatmap] Found {len(clusters)} clusters ({len(unique_labels)} labels, "
              f"{int((labels == -1).sum())} noise points).")
    else:
        print("[Heatmap] Not enough flagged points for clustering.")

    # --- Known-hotspot activity report ---------------------------------------
    hotspot_activity: List[Dict[str, Any]] = []
    if known_hotspots:
        from datetime import timedelta
        cutoff_7d = reference_time - timedelta(days=7)
        cutoff_30d = reference_time - timedelta(days=30)

        for hs in known_hotspots:
            hs_lat = float(hs["lat"])
            hs_lng = float(hs["lng"])

            events_7d = 0
            events_30d = 0
            total_nearby = 0

            for fp in flagged_points:
                try:
                    d = _haversine_km(hs_lat, hs_lng, fp["lat"], fp["lng"])
                except (ValueError, TypeError):
                    continue
                if d > 10.0:
                    continue
                total_nearby += 1
                try:
                    ts = datetime.fromisoformat(fp["timestamp"])
                    if ts >= cutoff_7d:
                        events_7d += 1
                    if ts >= cutoff_30d:
                        events_30d += 1
                except (ValueError, KeyError):
                    pass

            weekly_avg = events_30d / 4.0 if events_30d > 0 else 0
            if events_7d > weekly_avg * 1.5 and events_7d >= 3:
                trend = "increasing"
            elif events_7d < weekly_avg * 0.5:
                trend = "decreasing"
            else:
                trend = "stable"

            hotspot_activity.append({
                "name": hs.get("name", "Unknown"),
                "lat": hs_lat,
                "lng": hs_lng,
                "state": hs.get("state", _nearest_state(hs_lat, hs_lng)),
                "baseline_risk": hs.get("risk_level", "medium"),
                "recent_events": events_7d,
                "monthly_events": events_30d,
                "total_nearby": total_nearby,
                "trend": trend,
            })

        hotspot_activity.sort(key=lambda h: h["recent_events"], reverse=True)
        active = sum(1 for h in hotspot_activity if h["recent_events"] > 0)
        print(f"[Heatmap] Known hotspot activity: {active}/{len(known_hotspots)} active.")

    # --- State-level risk aggregation ----------------------------------------
    state_risk: Dict[str, Dict[str, Any]] = {}
    for c in clusters:
        state = c.get("state", "Unknown")
        if state not in state_risk:
            state_risk[state] = {
                "cluster_count": 0,
                "total_events": 0,
                "max_risk": 0.0,
                "risk_sum": 0.0,
                "hotspots_active": 0,
            }
        sr = state_risk[state]
        sr["cluster_count"] += 1
        sr["total_events"] += c["member_count"]
        sr["max_risk"] = max(sr["max_risk"], c["risk_score"])
        sr["risk_sum"] += c["risk_score"]

    for ha in hotspot_activity:
        state = ha.get("state", "Unknown")
        if state not in state_risk:
            state_risk[state] = {
                "cluster_count": 0,
                "total_events": 0,
                "max_risk": 0.0,
                "risk_sum": 0.0,
                "hotspots_active": 0,
            }
        if ha["recent_events"] > 0:
            state_risk[state]["hotspots_active"] += 1

    # Finalize state scores
    for state, sr in state_risk.items():
        cc = sr["cluster_count"]
        avg_risk = sr["risk_sum"] / max(cc, 1)
        hs_active = sr["hotspots_active"]

        score = (
            min(cc / 5.0, 1.0) * 0.30
            + avg_risk * 0.40
            + min(hs_active / 3.0, 1.0) * 0.30
        )
        score = min(score, 1.0)

        if score >= 0.65:
            level = "critical"
        elif score >= 0.45:
            level = "high"
        elif score >= 0.25:
            level = "medium"
        else:
            level = "low"

        state_risk[state] = {
            "risk_level": level,
            "risk_score": round(score, 3),
            "cluster_count": cc,
            "flagged_events": sr["total_events"],
            "hotspots_active": hs_active,
            "max_cluster_risk": round(sr["max_risk"], 3),
        }

    states_at_risk = sum(1 for s in state_risk.values() if s["risk_level"] != "low")
    print(f"[Heatmap] State risk: {states_at_risk} states at elevated risk.")

    # --- Summary statistics --------------------------------------------------
    max_intensity = max((p["intensity"] for p in points), default=0)
    total_flagged = sum(1 for p in points if p["category"] != "normal")

    # Category breakdown
    category_counts: Dict[str, int] = {}
    for p in points:
        cat = p["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    summary = {
        "total_points": len(points),
        "total_flagged": total_flagged,
        "total_clusters": len(clusters),
        "max_intensity": round(max_intensity, 6),
        "supply_chain_anomalies_ingested": len(sc_anomalies),
        "known_hotspots_loaded": len(known_hotspots),
        "states_at_risk": states_at_risk,
        "category_breakdown": category_counts,
    }

    # --- Write output --------------------------------------------------------
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_time": reference_time.isoformat(),
        "decay_half_life_days": half_life_days,
        "points": points,
        "clusters": clusters,
        "state_risk": state_risk,
        "known_hotspot_activity": hotspot_activity,
        "summary": summary,
    }

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print(f"[Heatmap] Output written to {out_path}")
    print(f"[Heatmap] Summary: {json.dumps(summary, indent=2)}")

    return out_path


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate heatmap seed data from scan events.")
    parser.add_argument("--half-life", type=float, default=DEFAULT_HALF_LIFE_DAYS,
                        help=f"Time-decay half-life in days (default {DEFAULT_HALF_LIFE_DAYS}).")
    parser.add_argument("--eps", type=float, default=DBSCAN_EPS,
                        help=f"DBSCAN epsilon (default {DBSCAN_EPS}).")
    parser.add_argument("--min-samples", type=int, default=DBSCAN_MIN_SAMPLES,
                        help=f"DBSCAN min_samples (default {DBSCAN_MIN_SAMPLES}).")
    args = parser.parse_args()

    generate_heatmap_seed(
        half_life_days=args.half_life,
        dbscan_eps=args.eps,
        dbscan_min_samples=args.min_samples,
    )
    print("Done.")
