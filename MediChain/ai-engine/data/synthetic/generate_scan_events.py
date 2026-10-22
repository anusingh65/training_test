"""
Synthetic scan-event generator for MediChain.

Produces 50 000 QR-code scan events distributed over 90 days, simulating
real-world scanning of medicine packages by pharmacists, distributors,
consumers, and inspectors across India.

Distribution
------------
* **90 %** -- scans from legitimate pharmaceutical hubs and distribution
              centres (normal baseline).
* **7 %**  -- scans from known counterfeit-risk zones listed in
              ``indian_pharma_hubs.json`` (elevated flag rates).
* **3 %**  -- deliberately anomalous scans (random locations, device
              spoofing indicators, off-hours patterns).

Hotspot emergence
-----------------
A synthetic "emerging hotspot" pattern is injected in the final 15 days of
the window: a previously quiet city (Varanasi) suddenly sees a concentrated
burst of flagged scans, simulating a newly discovered counterfeit ring.

Output
------
``data/synthetic/scan_events.csv``

Columns
-------
medicine_id, scanner_address, latitude, longitude, timestamp,
location_name, device_id, is_flagged, flag_severity

Usage
-----
    python -m data.synthetic.generate_scan_events
    python -m data.synthetic.generate_scan_events --count 100000 --days 180
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
#  Path setup
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_AI_ENGINE_DIR = _THIS_DIR.parent.parent

if str(_AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_DIR))

from config import SYNTHETIC_DIR

# ---------------------------------------------------------------------------
#  Load Indian pharma hub reference data
# ---------------------------------------------------------------------------
_HUBS_PATH = _THIS_DIR / "indian_pharma_hubs.json"

with open(_HUBS_PATH, "r", encoding="utf-8") as _fh:
    _HUBS_DATA: Dict[str, Any] = json.load(_fh)

MANUFACTURING_HUBS: List[Dict[str, Any]] = _HUBS_DATA["manufacturing_hubs"]
DISTRIBUTION_HUBS: List[Dict[str, Any]] = _HUBS_DATA["distribution_hubs"]
KNOWN_HOTSPOTS: List[Dict[str, Any]] = _HUBS_DATA["known_hotspots"]

# Combine legit locations into a single pool.
LEGIT_LOCATIONS: List[Dict[str, Any]] = MANUFACTURING_HUBS + DISTRIBUTION_HUBS

# Tier-2/3 Indian towns for scattering anomalous scans on land (not ocean).
# These are real coordinates of smaller cities, rural towns, highway stops, etc.
_SCATTER_TOWNS: List[Tuple[float, float, str]] = [
    (26.85, 80.91, "Lucknow Outskirts"), (25.43, 81.85, "Allahabad Rural"),
    (23.26, 77.41, "Bhopal Bypass"), (21.15, 79.09, "Nagpur Highway"),
    (22.72, 75.86, "Indore Periphery"), (24.58, 73.69, "Udaipur Rural"),
    (26.92, 75.79, "Jaipur Outskirts"), (28.41, 77.04, "Gurgaon Industrial"),
    (30.73, 76.78, "Chandigarh Suburb"), (31.63, 74.87, "Amritsar Road"),
    (19.07, 72.88, "Mumbai Suburb"), (15.36, 75.12, "Hubli Town"),
    (12.97, 77.59, "Bangalore Rural"), (13.08, 80.27, "Chennai Outskirts"),
    (17.39, 78.49, "Hyderabad Highway"), (11.02, 76.97, "Coimbatore Road"),
    (9.93, 76.27, "Kochi Periphery"), (22.57, 88.36, "Kolkata Suburb"),
    (25.61, 85.14, "Patna Road"), (26.14, 91.74, "Guwahati Outskirts"),
    (23.35, 85.33, "Ranchi Town"), (21.25, 81.63, "Raipur Highway"),
    (20.30, 85.83, "Bhubaneswar Rural"), (27.18, 78.02, "Agra Road"),
    (29.95, 78.16, "Dehradun Bypass"), (32.27, 75.64, "Jammu Outskirts"),
    (24.80, 85.01, "Gaya Town"), (23.81, 86.44, "Dhanbad Road"),
    (19.88, 75.32, "Aurangabad Highway"), (16.70, 74.24, "Kolhapur Rural"),
    (18.52, 73.86, "Pune Periphery"), (14.68, 77.60, "Anantapur Road"),
    (10.79, 79.14, "Thanjavur Town"), (8.52, 76.94, "Trivandrum Rural"),
    (27.88, 78.08, "Aligarh Outskirts"), (28.98, 77.71, "Meerut Road"),
    (26.45, 74.64, "Ajmer Highway"), (24.18, 72.83, "Palanpur Town"),
    (22.31, 73.19, "Vadodara Rural"), (21.17, 72.83, "Surat Periphery"),
    (23.02, 72.57, "Ahmedabad Outskirts"), (20.46, 85.88, "Cuttack Road"),
    (25.59, 91.88, "Shillong Town"), (27.34, 88.61, "Gangtok Road"),
    (24.81, 93.95, "Imphal Outskirts"), (23.73, 92.72, "Aizawl Rural"),
    (25.67, 94.11, "Kohima Highway"), (26.12, 91.79, "Guwahati Market"),
    (12.30, 76.66, "Mysore Road"), (15.83, 78.04, "Kurnool Town"),
]

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

# Emerging-hotspot injection point (quiet city that suddenly lights up).
EMERGING_HOTSPOT = {
    "name": "Varanasi Emerging Hotspot",
    "city": "Varanasi",
    "state": "Uttar Pradesh",
    "lat": 25.3176,
    "lng": 83.0064,
}

SEVERITIES = ["low", "medium", "high"]

# Flag probabilities per scan category.
FLAG_PROB_LEGIT    = 0.02   # 2 % of legit scans trigger a flag
FLAG_PROB_PROBLEM  = 0.35   # 35 % of problem-zone scans trigger a flag
FLAG_PROB_ANOMALY  = 0.70   # 70 % of anomalous scans trigger a flag
FLAG_PROB_HOTSPOT  = 0.55   # 55 % of emerging-hotspot scans trigger a flag

# Severity distribution weights per flag type.
SEV_WEIGHTS_LEGIT   = {"low": 0.70, "medium": 0.25, "high": 0.05}
SEV_WEIGHTS_PROBLEM = {"low": 0.30, "medium": 0.45, "high": 0.25}
SEV_WEIGHTS_ANOMALY = {"low": 0.10, "medium": 0.30, "high": 0.60}
SEV_WEIGHTS_HOTSPOT = {"low": 0.15, "medium": 0.40, "high": 0.45}


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------


def _jitter(lat: float, lng: float, km: float = 2.0) -> Tuple[float, float]:
    """Add small random geographic noise around a point."""
    delta_lat = random.uniform(-km, km) / 111.0
    delta_lng = random.uniform(-km, km) / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    return round(lat + delta_lat, 6), round(lng + delta_lng, 6)


def _eth_address() -> str:
    """Generate a realistic Ethereum-style hex address."""
    return "0x" + uuid.uuid4().hex[:40]


def _device_id() -> str:
    """Generate a device identifier."""
    prefixes = ["ANDROID", "IOS", "SCANNER", "KIOSK", "HANDHELD"]
    return f"{random.choice(prefixes)}-{uuid.uuid4().hex[:8].upper()}"


def _medicine_id() -> str:
    return "MED-" + uuid.uuid4().hex[:12].upper()


def _pick_severity(weights: Dict[str, float]) -> str:
    """Weighted random severity pick."""
    choices = list(weights.keys())
    probs = [weights[c] for c in choices]
    return random.choices(choices, weights=probs, k=1)[0]


def _random_timestamp_in_window(
    start: datetime,
    end: datetime,
    business_bias: bool = True,
) -> datetime:
    """Return a random timestamp, optionally biased toward business hours."""
    ts = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
    if business_bias and random.random() < 0.75:
        # Shift toward 8 AM -- 8 PM.
        ts = ts.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
    return ts


# ---------------------------------------------------------------------------
#  Scan event generators (by category)
# ---------------------------------------------------------------------------


def _generate_legit_scan(start: datetime, end: datetime) -> Dict[str, Any]:
    """Normal scan from a legitimate pharma hub or distribution centre."""
    loc = random.choice(LEGIT_LOCATIONS)
    lat, lng = _jitter(loc["lat"], loc["lng"], km=3.0)
    ts = _random_timestamp_in_window(start, end, business_bias=True)

    flagged = random.random() < FLAG_PROB_LEGIT
    severity = _pick_severity(SEV_WEIGHTS_LEGIT) if flagged else ""

    return {
        "medicine_id":     _medicine_id(),
        "scanner_address": _eth_address(),
        "latitude":        lat,
        "longitude":       lng,
        "timestamp":       ts.isoformat(),
        "location_name":   loc.get("name", loc.get("city", "Unknown")),
        "device_id":       _device_id(),
        "is_flagged":      int(flagged),
        "flag_severity":   severity,
    }


def _generate_problem_zone_scan(start: datetime, end: datetime) -> Dict[str, Any]:
    """Scan originating from a known counterfeit-risk hotspot."""
    loc = random.choice(KNOWN_HOTSPOTS)
    lat, lng = _jitter(loc["lat"], loc["lng"], km=5.0)
    ts = _random_timestamp_in_window(start, end, business_bias=True)

    flagged = random.random() < FLAG_PROB_PROBLEM
    severity = _pick_severity(SEV_WEIGHTS_PROBLEM) if flagged else ""

    return {
        "medicine_id":     _medicine_id(),
        "scanner_address": _eth_address(),
        "latitude":        lat,
        "longitude":       lng,
        "timestamp":       ts.isoformat(),
        "location_name":   loc.get("name", loc.get("city", "Unknown")),
        "device_id":       _device_id(),
        "is_flagged":      int(flagged),
        "flag_severity":   severity,
    }


def _generate_anomalous_scan(start: datetime, end: datetime) -> Dict[str, Any]:
    """Deliberately suspicious scan: random town, off-hours, spoofed device."""
    # Pick a real Indian town and jitter around it (stays on land).
    town_lat, town_lng, _ = random.choice(_SCATTER_TOWNS)
    lat, lng = _jitter(town_lat, town_lng, km=8.0)
    # Bias toward off-hours (midnight -- 5 AM).
    ts = _random_timestamp_in_window(start, end, business_bias=False)
    ts = ts.replace(hour=random.randint(0, 5), minute=random.randint(0, 59))

    flagged = random.random() < FLAG_PROB_ANOMALY
    severity = _pick_severity(SEV_WEIGHTS_ANOMALY) if flagged else ""

    location_name = random.choice([
        "Unknown Location",
        "Unregistered Facility",
        "Roadside Scan",
        "Rural Outpost",
        "Unverified Address",
    ])

    return {
        "medicine_id":     _medicine_id(),
        "scanner_address": _eth_address(),
        "latitude":        lat,
        "longitude":       lng,
        "timestamp":       ts.isoformat(),
        "location_name":   location_name,
        "device_id":       _device_id(),
        "is_flagged":      int(flagged),
        "flag_severity":   severity,
    }


def _generate_emerging_hotspot_scan(ts_start: datetime, ts_end: datetime) -> Dict[str, Any]:
    """Scan from the emerging-hotspot cluster (Varanasi, final 15 days)."""
    lat, lng = _jitter(EMERGING_HOTSPOT["lat"], EMERGING_HOTSPOT["lng"], km=4.0)
    ts = _random_timestamp_in_window(ts_start, ts_end, business_bias=True)

    flagged = random.random() < FLAG_PROB_HOTSPOT
    severity = _pick_severity(SEV_WEIGHTS_HOTSPOT) if flagged else ""

    return {
        "medicine_id":     _medicine_id(),
        "scanner_address": _eth_address(),
        "latitude":        lat,
        "longitude":       lng,
        "timestamp":       ts.isoformat(),
        "location_name":   EMERGING_HOTSPOT["name"],
        "device_id":       _device_id(),
        "is_flagged":      int(flagged),
        "flag_severity":   severity,
    }


# ---------------------------------------------------------------------------
#  Main generator
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "medicine_id", "scanner_address", "latitude", "longitude",
    "timestamp", "location_name", "device_id", "is_flagged", "flag_severity",
]


def generate_scan_events(
    total_events: int = 50_000,
    days: int = 90,
    seed: int = 42,
) -> Path:
    """Generate the scan-events dataset.

    Parameters
    ----------
    total_events:
        Total number of scan events to produce.
    days:
        Duration of the observation window in calendar days.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    Path
        Path to the output CSV.
    """
    random.seed(seed)

    out_path = SYNTHETIC_DIR / "scan_events.csv"

    end = datetime(2025, 6, 1)
    start = end - timedelta(days=days)
    hotspot_start = end - timedelta(days=15)

    # Budget allocation.
    n_legit   = int(total_events * 0.90)
    n_problem = int(total_events * 0.07)
    n_anomaly = int(total_events * 0.03)

    # Additionally inject ~500 emerging-hotspot scans inside the final 15 days.
    n_hotspot = 500

    rows: List[Dict[str, Any]] = []

    # --- Legit scans ---------------------------------------------------------
    print(f"[ScanEvents] Generating {n_legit} legitimate scans ...")
    for i in range(n_legit):
        rows.append(_generate_legit_scan(start, end))
        if (i + 1) % 10000 == 0:
            print(f"  legit: {i + 1} / {n_legit}")

    # --- Problem-zone scans --------------------------------------------------
    print(f"[ScanEvents] Generating {n_problem} problem-zone scans ...")
    for i in range(n_problem):
        rows.append(_generate_problem_zone_scan(start, end))

    # --- Anomalous scans -----------------------------------------------------
    print(f"[ScanEvents] Generating {n_anomaly} anomalous scans ...")
    for i in range(n_anomaly):
        rows.append(_generate_anomalous_scan(start, end))

    # --- Emerging-hotspot burst (last 15 days) --------------------------------
    print(f"[ScanEvents] Injecting {n_hotspot} emerging-hotspot scans (last 15 days) ...")
    for i in range(n_hotspot):
        rows.append(_generate_emerging_hotspot_scan(hotspot_start, end))

    # --- Sort by timestamp and write -----------------------------------------
    rows.sort(key=lambda r: r["timestamp"])

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    flagged = sum(1 for r in rows if r["is_flagged"])
    print(f"[ScanEvents] Wrote {total} rows ({flagged} flagged) to {out_path}")

    # Quick stats.
    sev_counts = {"low": 0, "medium": 0, "high": 0}
    for r in rows:
        s = r["flag_severity"]
        if s in sev_counts:
            sev_counts[s] += 1
    print(f"[ScanEvents] Severity breakdown: {json.dumps(sev_counts)}")

    return out_path


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic scan events.")
    parser.add_argument("--count", type=int, default=50_000, help="Total events (default 50000).")
    parser.add_argument("--days", type=int, default=90, help="Observation window in days (default 90).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    args = parser.parse_args()

    generate_scan_events(total_events=args.count, days=args.days, seed=args.seed)
    print("Done.")
