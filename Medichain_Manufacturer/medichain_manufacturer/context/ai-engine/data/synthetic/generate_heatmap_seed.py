"""
Heatmap seed-data generator for MediChain.

Reads ``scan_events.csv`` (produced by ``generate_scan_events.py``) and
computes weighted heatmap data suitable for rendering with Leaflet.heat
or Folium's ``HeatMap`` plugin on the MediChain dashboard.

Intensity mapping
-----------------
* Normal (unflagged) scan:           0.10
* Flagged -- severity ``low``:       0.30
* Flagged -- severity ``medium``:    0.50
* Flagged -- severity ``high``:      0.80
* Velocity-alert equivalent:         1.00  (injected from supply-chain data
                                             if available)

Time decay
----------
A 7-day half-life exponential decay is applied so that recent events
dominate the heatmap while older events fade.

    weight(t) = base_intensity * 2^(-(now - t) / 7)

Cluster detection
-----------------
DBSCAN (``eps=0.3`` in degree-space, ``min_samples=5``) is run on the
flagged-scan coordinates to identify geographic clusters of suspicious
activity.  Each cluster is annotated with its centroid, member count,
dominant severity, and a human-readable risk label.

Output
------
``data/synthetic/heatmap_seed.json`` with structure::

    {
        "generated_at": "...",
        "reference_time": "...",
        "decay_half_life_days": 7,
        "points": [
            {"lat": ..., "lng": ..., "intensity": ..., "timestamp": "...", "category": "..."},
            ...
        ],
        "clusters": [
            {
                "cluster_id": 0,
                "centroid_lat": ...,
                "centroid_lng": ...,
                "member_count": ...,
                "dominant_severity": "high",
                "risk_label": "High-risk cluster",
                "member_points": [...]
            },
            ...
        ],
        "summary": {
            "total_points": ...,
            "total_flagged": ...,
            "total_clusters": ...,
            "max_intensity": ...
        }
    }

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
from datetime import datetime
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
INTENSITY_VELOCITY_ALERT = 1.00

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


# ---------------------------------------------------------------------------
#  Time-decay helper
# ---------------------------------------------------------------------------


def _decay_weight(
    base_intensity: float,
    event_time: datetime,
    reference_time: datetime,
    half_life_days: float,
) -> float:
    """Apply exponential time-decay to a base intensity value.

    weight = base_intensity * 2^(-(ref - event) / half_life)
    """
    delta_days = (reference_time - event_time).total_seconds() / 86400.0
    if delta_days < 0:
        delta_days = 0.0
    return base_intensity * (2.0 ** (-delta_days / half_life_days))


# ---------------------------------------------------------------------------
#  DBSCAN implementation (pure NumPy -- avoids sklearn hard dependency)
# ---------------------------------------------------------------------------


def _dbscan_numpy(
    coords: np.ndarray,
    eps: float,
    min_samples: int,
) -> np.ndarray:
    """Minimal DBSCAN clustering using only NumPy.

    Parameters
    ----------
    coords:
        (N, 2) array of [lat, lng].
    eps:
        Neighbourhood radius (Euclidean in degree-space).
    min_samples:
        Minimum points to form a dense region.

    Returns
    -------
    np.ndarray
        Integer labels of length N.  -1 means noise.
    """
    n = len(coords)
    labels = np.full(n, -1, dtype=int)
    visited = np.zeros(n, dtype=bool)
    cluster_id = 0

    # Pre-compute pairwise distances (fine for N < 100k).
    # For very large N, a spatial index would be needed.
    if n > 50_000:
        # Fall back to chunked distance computation.
        pass  # handled below

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
            continue  # noise for now (may be claimed later)

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


def _run_dbscan(coords: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    """Run DBSCAN, using scikit-learn if available, else pure-NumPy fallback."""
    try:
        from sklearn.cluster import DBSCAN
        model = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
        return model.fit_predict(coords)
    except ImportError:
        print("[Heatmap] scikit-learn not available; using pure-NumPy DBSCAN.")
        return _dbscan_numpy(coords, eps, min_samples)


# ---------------------------------------------------------------------------
#  Velocity alerts from supply-chain data (optional enrichment)
# ---------------------------------------------------------------------------


def _load_velocity_alerts() -> List[Dict[str, Any]]:
    """Load velocity-violation anomalies from supply_chain_transactions.csv.

    Returns a list of dicts with lat, lng, timestamp for each velocity
    violation.  Returns an empty list if the file does not exist.
    """
    sc_path = SYNTHETIC_DIR / "supply_chain_transactions.csv"
    if not sc_path.exists():
        return []

    alerts: List[Dict[str, Any]] = []
    with open(sc_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("anomaly_type") == "velocity_violation":
                try:
                    alerts.append({
                        "lat": float(row["to_lat"]),
                        "lng": float(row["to_lng"]),
                        "timestamp": row["timestamp"],
                    })
                except (ValueError, KeyError):
                    continue
    return alerts


# ---------------------------------------------------------------------------
#  Main generator
# ---------------------------------------------------------------------------


def generate_heatmap_seed(
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
    dbscan_eps: float = DBSCAN_EPS,
    dbscan_min_samples: int = DBSCAN_MIN_SAMPLES,
) -> Path:
    """Read scan_events.csv and compute the heatmap seed JSON.

    Parameters
    ----------
    half_life_days:
        Half-life for exponential time-decay (days).
    dbscan_eps:
        DBSCAN epsilon in degree-space.
    dbscan_min_samples:
        DBSCAN minimum samples per cluster.

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

    # --- Compute intensity per point -----------------------------------------
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

    # --- Inject velocity alerts at max intensity -----------------------------
    velocity_alerts = _load_velocity_alerts()
    if velocity_alerts:
        print(f"[Heatmap] Enriching with {len(velocity_alerts)} velocity-violation alerts.")
        for va in velocity_alerts:
            try:
                ts = datetime.fromisoformat(va["timestamp"])
            except (ValueError, KeyError):
                ts = reference_time
            intensity = _decay_weight(INTENSITY_VELOCITY_ALERT, ts, reference_time, half_life_days)
            points.append({
                "lat": va["lat"],
                "lng": va["lng"],
                "intensity": round(intensity, 6),
                "timestamp": ts.isoformat(),
                "category": "velocity_alert",
            })

    print(f"[Heatmap] Total heatmap points: {len(points)}")

    # --- DBSCAN clustering on flagged points ---------------------------------
    flagged_points = [p for p in points if p["category"] != "normal"]
    print(f"[Heatmap] Running DBSCAN on {len(flagged_points)} flagged points "
          f"(eps={dbscan_eps}, min_samples={dbscan_min_samples}) ...")

    clusters: List[Dict[str, Any]] = []

    if len(flagged_points) >= dbscan_min_samples:
        coords = np.array([[p["lat"], p["lng"]] for p in flagged_points])
        labels = _run_dbscan(coords, dbscan_eps, dbscan_min_samples)

        unique_labels = set(labels)
        unique_labels.discard(-1)  # noise

        for cid in sorted(unique_labels):
            member_mask = labels == cid
            member_coords = coords[member_mask]
            member_indices = [i for i, m in enumerate(member_mask) if m]

            centroid_lat = float(np.mean(member_coords[:, 0]))
            centroid_lng = float(np.mean(member_coords[:, 1]))
            count = int(member_mask.sum())

            # Dominant severity.
            severities = []
            member_pts = []
            for idx in member_indices:
                fp = flagged_points[idx]
                cat = fp["category"]
                if "high" in cat or cat == "velocity_alert":
                    severities.append("high")
                elif "medium" in cat:
                    severities.append("medium")
                else:
                    severities.append("low")
                member_pts.append({"lat": fp["lat"], "lng": fp["lng"], "intensity": fp["intensity"]})

            sev_counter = Counter(severities)
            dominant = sev_counter.most_common(1)[0][0] if sev_counter else "low"

            risk_labels = {
                "high": "High-risk cluster",
                "medium": "Medium-risk cluster",
                "low": "Low-risk cluster",
            }

            clusters.append({
                "cluster_id": int(cid),
                "centroid_lat": round(centroid_lat, 6),
                "centroid_lng": round(centroid_lng, 6),
                "member_count": count,
                "dominant_severity": dominant,
                "risk_label": risk_labels.get(dominant, "Unknown risk"),
                "member_points": member_pts,
            })

        print(f"[Heatmap] Found {len(clusters)} clusters ({len(unique_labels)} labels, "
              f"{int((labels == -1).sum())} noise points).")
    else:
        print("[Heatmap] Not enough flagged points for clustering.")

    # --- Summary statistics --------------------------------------------------
    max_intensity = max((p["intensity"] for p in points), default=0)
    total_flagged = sum(1 for p in points if p["category"] != "normal")

    summary = {
        "total_points": len(points),
        "total_flagged": total_flagged,
        "total_clusters": len(clusters),
        "max_intensity": round(max_intensity, 6),
    }

    # --- Write output --------------------------------------------------------
    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "reference_time": reference_time.isoformat(),
        "decay_half_life_days": half_life_days,
        "points": points,
        "clusters": clusters,
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
