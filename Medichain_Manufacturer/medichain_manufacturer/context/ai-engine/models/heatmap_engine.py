"""
Geographic heatmap and hotspot-detection engine for MediChain.

Uses DBSCAN clustering on flagged scan events to identify geographic
concentrations of suspicious pharmaceutical activity, and a simple
linear-regression extrapolation to predict emerging hotspots.

Design notes
------------
* **DBSCAN parameters** -- ``eps=0.05`` degrees (~5.5 km at Indian
  latitudes around 20 degN) and ``min_samples=3``.  These defaults
  balance sensitivity against noise for the expected density of
  pharmacy-scan events in urban India.
* **Time decay** -- An exponential decay with a 7-day half-life ensures
  that recent events dominate the heatmap while older events fade
  gracefully rather than vanishing abruptly.
* **Intensity mapping** -- Each event contributes a base intensity that
  depends on its flag type (normal scans contribute a small ambient
  signal, while high-severity flags and velocity anomalies contribute
  much more).

Dependencies: ``numpy``, ``scikit-learn`` (DBSCAN).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
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
    "normal": 0.1,
    "flagged_low": 0.3,
    "flagged_medium": 0.5,
    "flagged_high": 0.8,
    "velocity_anomaly": 1.0,
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


# --------------------------------------------------------------------------- #
#  Main engine class                                                           #
# --------------------------------------------------------------------------- #


class HeatmapEngine:
    """Hotspot detection and prediction engine.

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
            ``datetime.utcnow()``.

        Returns
        -------
        dict
            ``heatmap_points`` -- list of ``[lat, lng, intensity]`` triples.
            ``clusters`` -- list of cluster dicts (see ``_find_clusters``).
            ``predicted_hotspots`` -- list of prediction dicts.
            ``stats`` -- summary statistics.
        """

        if reference_time is None:
            reference_time = datetime.utcnow()

        if not scan_events:
            empty: Dict[str, Any] = {
                "heatmap_points": [],
                "clusters": [],
                "predicted_hotspots": [],
                "stats": {
                    "total_events": 0,
                    "flagged_events": 0,
                    "cluster_count": 0,
                    "hotspot_predictions": 0,
                },
            }
            self.heatmap_points = []
            self.clusters = []
            return empty

        # -- 1. Compute time-decayed intensity for every event ---------------
        heatmap_points: List[List[float]] = []
        flagged_events: List[Dict[str, Any]] = []

        for event in scan_events:
            intensity = self._compute_intensity(event, reference_time)
            lat = float(event["lat"])
            lng = float(event["lng"])
            heatmap_points.append([lat, lng, intensity])

            flag_type = event.get("flag_type", "normal")
            if flag_type != "normal":
                flagged_events.append(event)

        # -- 2. DBSCAN clustering on flagged events --------------------------
        clusters = self._find_clusters(flagged_events)

        # -- 3. Compute cluster growth rates across 4 weekly windows ---------
        weekly_cluster_data = self._weekly_cluster_snapshots(
            flagged_events, reference_time, num_weeks=4
        )

        # -- 4. Predict emerging hotspots ------------------------------------
        predicted_hotspots = self._predict_hotspots(clusters, weekly_cluster_data)

        # -- 5. Cache and return ---------------------------------------------
        self.heatmap_points = heatmap_points
        self.clusters = clusters

        return {
            "heatmap_points": heatmap_points,
            "clusters": clusters,
            "predicted_hotspots": predicted_hotspots,
            "stats": {
                "total_events": len(scan_events),
                "flagged_events": len(flagged_events),
                "cluster_count": len(clusters),
                "hotspot_predictions": len(predicted_hotspots),
            },
        }

    def get_zone_risk_level(
        self,
        lat: float,
        lng: float,
    ) -> Dict[str, Any]:
        """Assess the risk level at a given coordinate.

        The risk level is determined by proximity to the nearest cached
        cluster:

        * **critical** -- within the cluster radius.
        * **high** -- within 2x the cluster radius (or < 5 km if no radius).
        * **medium** -- within 10 km.
        * **low** -- farther than 10 km from any cluster.

        Returns
        -------
        dict
            ``risk_level`` (str), ``nearest_cluster`` (dict or None),
            ``distance_km`` (float or None).
        """

        if not self.clusters:
            return {
                "risk_level": "low",
                "nearest_cluster": None,
                "distance_km": None,
            }

        best_distance: float = float("inf")
        best_cluster: Optional[Dict[str, Any]] = None

        for cluster in self.clusters:
            c_lat = cluster["center_lat"]
            c_lng = cluster["center_lng"]
            dist = _haversine_km(lat, lng, c_lat, c_lng)
            if dist < best_distance:
                best_distance = dist
                best_cluster = cluster

        if best_cluster is None:
            return {
                "risk_level": "low",
                "nearest_cluster": None,
                "distance_km": None,
            }

        cluster_radius_km = best_cluster.get("radius_km", 5.0)

        if best_distance <= cluster_radius_km:
            risk = "critical"
        elif best_distance <= cluster_radius_km * 2.0:
            risk = "high"
        elif best_distance <= 10.0:
            risk = "medium"
        else:
            risk = "low"

        return {
            "risk_level": risk,
            "nearest_cluster": best_cluster,
            "distance_km": round(best_distance, 3),
        }

    def load_seed_data(self, filepath: str) -> None:
        """Load precomputed heatmap data from a JSON file.

        The file should contain a JSON object with optional keys
        ``heatmap_points`` (list of ``[lat, lng, intensity]``) and
        ``clusters`` (list of cluster dicts as returned by
        ``_find_clusters``).

        Parameters
        ----------
        filepath:
            Path to the JSON seed file.

        Raises
        ------
        FileNotFoundError
            If *filepath* does not exist.
        json.JSONDecodeError
            If the file is not valid JSON.
        """

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Seed data file not found: {filepath}")

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        self.heatmap_points = data.get("heatmap_points", [])
        self.clusters = data.get("clusters", [])

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

        timestamp = event.get("timestamp")
        if timestamp is None:
            # No timestamp -- assume "now" (no decay).
            return base_intensity

        if isinstance(timestamp, str):
            # Try common ISO formats.
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
                try:
                    timestamp = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:
                # Unparseable -- no decay.
                return base_intensity

        days_old = max((reference_time - timestamp).total_seconds() / 86400.0, 0.0)
        decay = math.exp(
            -math.log(2) * days_old / max(self.time_decay_halflife_days, 1e-9)
        )
        return round(base_intensity * decay, 6)

    def _find_clusters(
        self,
        flagged_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Run DBSCAN on flagged events and return cluster summaries.

        Returns
        -------
        list[dict]
            Each cluster dict has keys: ``cluster_id``, ``center_lat``,
            ``center_lng``, ``radius_km``, ``event_count``,
            ``avg_severity``, ``max_severity``, ``flag_types``.
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
        }

        clusters: List[Dict[str, Any]] = []
        for label in sorted(unique_labels):
            member_mask = labels == label
            member_coords = coords[member_mask]
            member_events = [
                e for e, m in zip(flagged_events, member_mask) if m
            ]

            center_lat = float(np.mean(member_coords[:, 0]))
            center_lng = float(np.mean(member_coords[:, 1]))

            # Cluster radius: max distance from center to any member.
            if len(member_coords) > 1:
                distances = np.array([
                    _haversine_km(center_lat, center_lng, float(c[0]), float(c[1]))
                    for c in member_coords
                ])
                radius_km = float(np.max(distances))
            else:
                radius_km = 0.0

            severities = [
                severity_map.get(e.get("flag_type", "flagged_low"), 0.3)
                for e in member_events
            ]
            flag_types = list(set(
                e.get("flag_type", "flagged_low") for e in member_events
            ))

            clusters.append({
                "cluster_id": int(label),
                "center_lat": round(center_lat, 6),
                "center_lng": round(center_lng, 6),
                "radius_km": round(radius_km, 3),
                "event_count": int(np.sum(member_mask)),
                "avg_severity": round(float(np.mean(severities)), 4),
                "max_severity": round(float(np.max(severities)), 4),
                "flag_types": flag_types,
            })

        return clusters

    def _weekly_cluster_snapshots(
        self,
        flagged_events: List[Dict[str, Any]],
        reference_time: datetime,
        num_weeks: int = 4,
    ) -> List[List[Dict[str, Any]]]:
        """Run DBSCAN on cumulative weekly windows to observe cluster growth.

        Returns a list of ``num_weeks`` cluster lists, where index 0 is the
        oldest window (``num_weeks`` weeks ago up to ``(num_weeks-1)`` weeks
        ago, cumulative) and the last element covers all time up to
        ``reference_time``.
        """

        weekly_snapshots: List[List[Dict[str, Any]]] = []

        for week_idx in range(num_weeks):
            # Cumulative: include all events from the beginning up to the
            # end of this week window.
            cutoff = reference_time - timedelta(weeks=num_weeks - 1 - week_idx)

            windowed_events: List[Dict[str, Any]] = []
            for event in flagged_events:
                ts = event.get("timestamp")
                if ts is None:
                    windowed_events.append(event)
                    continue
                if isinstance(ts, str):
                    for fmt in (
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y-%m-%d",
                    ):
                        try:
                            ts = datetime.strptime(ts, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        windowed_events.append(event)
                        continue
                if ts <= cutoff:
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

        For each current cluster, we look back through the weekly snapshots
        and find the matching cluster (nearest center within ``eps_degrees``).
        We then perform a simple linear regression on the event count over
        the weekly windows.  If the extrapolated count 2 weeks ahead is at
        least double the current count, the cluster is flagged as a
        predicted hotspot.

        Returns
        -------
        list[dict]
            Each entry: ``cluster_id``, ``center_lat``, ``center_lng``,
            ``current_count``, ``predicted_count_2w``, ``growth_rate``,
            ``alert``.
        """

        if not current_clusters or not weekly_cluster_data:
            return []

        num_weeks = len(weekly_cluster_data)
        predictions: List[Dict[str, Any]] = []

        for cluster in current_clusters:
            c_lat = cluster["center_lat"]
            c_lng = cluster["center_lng"]

            # Build a time series of event counts for this cluster across
            # weekly snapshots.
            counts: List[float] = []
            for snapshot in weekly_cluster_data:
                # Find the closest cluster in this snapshot.
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
                # Only match if reasonably close.
                if best_dist <= self.eps_degrees * 3:
                    counts.append(float(matched_count))
                else:
                    counts.append(0.0)

            # Linear regression:  y = a + b * x  where x is the week index.
            n = len(counts)
            if n < 2:
                continue

            xs = np.arange(n, dtype=np.float64)
            ys = np.array(counts, dtype=np.float64)

            x_mean = np.mean(xs)
            y_mean = np.mean(ys)

            ss_xx = float(np.sum((xs - x_mean) ** 2))
            ss_xy = float(np.sum((xs - x_mean) * (ys - y_mean)))

            if ss_xx == 0.0:
                # All x values identical (shouldn't happen with arange).
                continue

            slope = ss_xy / ss_xx
            intercept = y_mean - slope * x_mean

            # Predict 2 weeks ahead (x = n - 1 + 2).
            predicted_count_2w = max(intercept + slope * (n - 1 + 2), 0.0)
            current_count = cluster["event_count"]

            # Growth rate per week.
            growth_rate = slope

            # Flag if predicted to at least double.
            will_double = (
                predicted_count_2w >= current_count * 2.0 and current_count > 0
            )

            alert = (
                f"Cluster near ({c_lat:.4f}, {c_lng:.4f}) is predicted to "
                f"grow from {current_count} to ~{predicted_count_2w:.0f} "
                f"events in 2 weeks (growth rate: {growth_rate:+.1f}/week)."
                if will_double
                else ""
            )

            if will_double or growth_rate > 0:
                predictions.append({
                    "cluster_id": cluster["cluster_id"],
                    "center_lat": c_lat,
                    "center_lng": c_lng,
                    "current_count": current_count,
                    "predicted_count_2w": round(predicted_count_2w, 1),
                    "growth_rate_per_week": round(growth_rate, 2),
                    "alert": alert,
                })

        return predictions

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
