"""
Synthetic supply-chain transaction generator for MediChain.

Produces a realistic dataset of pharmaceutical supply-chain transfers
across India, with both **normal** and **anomalous** transactions.
Locations are drawn from ``indian_pharma_hubs.json`` so the geographic
distribution is plausible.

Normal flow
-----------
Manufacturer -> Distributor -> Pharmacy -> Consumer

Anomaly types
-------------
* **velocity_violation**       -- transfer speed exceeds physical possibility
* **path_deviation**           -- skips a step in the expected role sequence
* **duplicate_scan**           -- same medicine scanned twice at the same stage
* **reverse_flow**             -- goods move backward in the supply chain
* **geographic_impossibility** -- origin / destination outside India or impossibly far
* **excessive_transfers**      -- too many handoffs for a single batch
* **suspicious_timing**        -- transfers at unusual hours (2-5 AM on weekdays)

Output
------
``data/synthetic/supply_chain_transactions.csv``

Usage
-----
    python -m data.synthetic.generate_supply_chain_data
    python -m data.synthetic.generate_supply_chain_data --normal 20000 --anomaly 1000
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

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------
EARTH_RADIUS_KM = 6371.0

ROLES_ORDERED = ["Manufacturer", "Distributor", "Pharmacy", "Consumer"]

# Realistic pharmacy / consumer locations scattered across India.
PHARMACY_LOCATIONS = [
    {"name": "Apollo Pharmacy, Delhi",      "lat": 28.6300, "lng": 77.2200},
    {"name": "MedPlus, Hyderabad",          "lat": 17.4400, "lng": 78.4900},
    {"name": "Netmeds Store, Chennai",      "lat": 13.0600, "lng": 80.2500},
    {"name": "Jan Aushadhi, Lucknow",       "lat": 26.8500, "lng": 80.9500},
    {"name": "Wellness Forever, Mumbai",    "lat": 19.0800, "lng": 72.8800},
    {"name": "Apollo Pharmacy, Bengaluru",  "lat": 12.9800, "lng": 77.5900},
    {"name": "MedPlus, Pune",               "lat": 18.5200, "lng": 73.8600},
    {"name": "PharmEasy Hub, Ahmedabad",    "lat": 23.0400, "lng": 72.5700},
    {"name": "Jan Aushadhi, Patna",         "lat": 25.6200, "lng": 85.1400},
    {"name": "1mg Store, Jaipur",           "lat": 26.9200, "lng": 75.7900},
    {"name": "Netmeds Store, Kolkata",      "lat": 22.5700, "lng": 88.3700},
    {"name": "Apollo Pharmacy, Chandigarh", "lat": 30.7300, "lng": 76.7800},
    {"name": "MedPlus, Visakhapatnam",      "lat": 17.7000, "lng": 83.3000},
    {"name": "Wellness Forever, Goa",       "lat": 15.5000, "lng": 73.8300},
    {"name": "Jan Aushadhi, Bhopal",        "lat": 23.2600, "lng": 77.4100},
    {"name": "PharmEasy Hub, Nagpur",       "lat": 21.1500, "lng": 79.0900},
    {"name": "1mg Store, Indore",           "lat": 22.7200, "lng": 75.8600},
    {"name": "Apollo Pharmacy, Kochi",      "lat": 9.9300,  "lng": 76.2700},
    {"name": "Netmeds Store, Coimbatore",   "lat": 11.0200, "lng": 76.9600},
    {"name": "MedPlus, Varanasi",           "lat": 25.3200, "lng": 83.0100},
]

CONSUMER_JITTER_KM = 5.0  # consumers are near a pharmacy

MEDICINE_NAMES = [
    "Paracetamol 500mg", "Amoxicillin 250mg", "Metformin 500mg",
    "Atorvastatin 10mg", "Omeprazole 20mg", "Azithromycin 500mg",
    "Ciprofloxacin 500mg", "Ibuprofen 400mg", "Losartan 50mg",
    "Amlodipine 5mg", "Cetirizine 10mg", "Pantoprazole 40mg",
    "Clopidogrel 75mg", "Glimepiride 2mg", "Montelukast 10mg",
    "Telmisartan 40mg", "Doxycycline 100mg", "Ranitidine 150mg",
    "Levofloxacin 500mg", "Metoprolol 50mg",
]

# Typical inter-step transit time ranges (hours).
TRANSIT_HOURS = {
    ("Manufacturer", "Distributor"):  (12, 96),
    ("Distributor", "Pharmacy"):      (6, 72),
    ("Pharmacy", "Consumer"):         (0.25, 4),
}


# ---------------------------------------------------------------------------
#  Geo helpers
# ---------------------------------------------------------------------------


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _jitter(lat: float, lng: float, km: float = 0.5) -> Tuple[float, float]:
    """Add small random geographic noise."""
    delta_lat = random.uniform(-km, km) / 111.0
    delta_lng = random.uniform(-km, km) / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    return round(lat + delta_lat, 6), round(lng + delta_lng, 6)


def _pick_location(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    loc = random.choice(locations)
    lat, lng = _jitter(loc["lat"], loc["lng"])
    return {"name": loc.get("name", loc.get("city", "Unknown")), "lat": lat, "lng": lng}


# ---------------------------------------------------------------------------
#  Medicine / batch ID helpers
# ---------------------------------------------------------------------------


def _medicine_id() -> str:
    return "MED-" + uuid.uuid4().hex[:12].upper()


def _batch_id() -> str:
    return "BATCH-" + uuid.uuid4().hex[:8].upper()


# ---------------------------------------------------------------------------
#  Normal transaction chain
# ---------------------------------------------------------------------------


def _generate_normal_chain(
    start_time: datetime,
) -> List[Dict[str, Any]]:
    """Generate a full Manufacturer -> Distributor -> Pharmacy -> Consumer chain."""
    med_id = _medicine_id()
    batch_id = _batch_id()
    medicine_name = random.choice(MEDICINE_NAMES)

    mfg = _pick_location(MANUFACTURING_HUBS)
    dist = _pick_location(DISTRIBUTION_HUBS)
    pharm = _pick_location(PHARMACY_LOCATIONS)
    cons_lat, cons_lng = _jitter(pharm["lat"], pharm["lng"], km=CONSUMER_JITTER_KM)
    cons = {"name": "Consumer", "lat": cons_lat, "lng": cons_lng}

    chain_nodes = [
        ("Manufacturer", mfg),
        ("Distributor", dist),
        ("Pharmacy", pharm),
        ("Consumer", cons),
    ]

    rows: List[Dict[str, Any]] = []
    ts = start_time
    prev_lat, prev_lng = mfg["lat"], mfg["lng"]
    prev_ts = ts

    for i in range(1, len(chain_nodes)):
        from_role, from_loc = chain_nodes[i - 1]
        to_role, to_loc = chain_nodes[i]

        # Transit time.
        lo, hi = TRANSIT_HOURS.get((from_role, to_role), (1, 48))
        hours = random.uniform(lo, hi)
        ts = ts + timedelta(hours=hours)

        dist_km = _haversine(from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"])
        speed = dist_km / max(hours, 0.01)

        rows.append({
            "medicine_id":                    med_id,
            "batch_id":                       batch_id,
            "medicine_name":                  medicine_name,
            "from_role":                      from_role,
            "to_role":                        to_role,
            "from_lat":                       from_loc["lat"],
            "from_lng":                       from_loc["lng"],
            "to_lat":                         to_loc["lat"],
            "to_lng":                         to_loc["lng"],
            "timestamp":                      ts.isoformat(),
            "transfer_number":                i,
            "time_since_last_transfer_hours": round(hours, 2),
            "distance_km":                    round(dist_km, 2),
            "speed_kmh":                      round(speed, 2),
            "hour_of_day":                    ts.hour,
            "is_weekend":                     int(ts.weekday() >= 5),
            "path_sequence":                  f"{from_role}->{to_role}",
            "is_anomaly":                     0,
            "anomaly_type":                   "",
        })

        prev_lat, prev_lng = to_loc["lat"], to_loc["lng"]
        prev_ts = ts

    return rows


# ---------------------------------------------------------------------------
#  Anomalous transaction generators
# ---------------------------------------------------------------------------


def _anomaly_velocity_violation(start_time: datetime) -> List[Dict[str, Any]]:
    """Speed physically impossible (> 900 km/h by road)."""
    rows = _generate_normal_chain(start_time)
    # Pick one leg and shrink transit time to make speed impossible.
    idx = random.randint(0, len(rows) - 1)
    r = rows[idx]
    # Force the transfer to happen in < 0.1 hours regardless of distance.
    r["time_since_last_transfer_hours"] = round(random.uniform(0.01, 0.1), 4)
    r["speed_kmh"] = round(r["distance_km"] / r["time_since_last_transfer_hours"], 2)
    r["is_anomaly"] = 1
    r["anomaly_type"] = "velocity_violation"
    return rows


def _anomaly_path_deviation(start_time: datetime) -> List[Dict[str, Any]]:
    """Skip a supply-chain step (e.g. Manufacturer -> Pharmacy)."""
    med_id = _medicine_id()
    batch_id = _batch_id()
    medicine_name = random.choice(MEDICINE_NAMES)

    mfg = _pick_location(MANUFACTURING_HUBS)
    pharm = _pick_location(PHARMACY_LOCATIONS)

    hours = random.uniform(6, 48)
    ts = start_time + timedelta(hours=hours)
    dist_km = _haversine(mfg["lat"], mfg["lng"], pharm["lat"], pharm["lng"])
    speed = dist_km / max(hours, 0.01)

    return [{
        "medicine_id":                    med_id,
        "batch_id":                       batch_id,
        "medicine_name":                  medicine_name,
        "from_role":                      "Manufacturer",
        "to_role":                        "Pharmacy",
        "from_lat":                       mfg["lat"],
        "from_lng":                       mfg["lng"],
        "to_lat":                         pharm["lat"],
        "to_lng":                         pharm["lng"],
        "timestamp":                      ts.isoformat(),
        "transfer_number":                1,
        "time_since_last_transfer_hours": round(hours, 2),
        "distance_km":                    round(dist_km, 2),
        "speed_kmh":                      round(speed, 2),
        "hour_of_day":                    ts.hour,
        "is_weekend":                     int(ts.weekday() >= 5),
        "path_sequence":                  "Manufacturer->Pharmacy",
        "is_anomaly":                     1,
        "anomaly_type":                   "path_deviation",
    }]


def _anomaly_duplicate_scan(start_time: datetime) -> List[Dict[str, Any]]:
    """Same medicine scanned twice at the same stage."""
    rows = _generate_normal_chain(start_time)
    dup = dict(rows[0])
    dup["timestamp"] = (datetime.fromisoformat(dup["timestamp"]) + timedelta(seconds=random.randint(5, 120))).isoformat()
    dup["is_anomaly"] = 1
    dup["anomaly_type"] = "duplicate_scan"
    rows.append(dup)
    return rows


def _anomaly_reverse_flow(start_time: datetime) -> List[Dict[str, Any]]:
    """Goods move backward: Pharmacy -> Distributor."""
    med_id = _medicine_id()
    batch_id = _batch_id()
    medicine_name = random.choice(MEDICINE_NAMES)

    pharm = _pick_location(PHARMACY_LOCATIONS)
    dist = _pick_location(DISTRIBUTION_HUBS)

    hours = random.uniform(2, 24)
    ts = start_time + timedelta(hours=hours)
    dist_km = _haversine(pharm["lat"], pharm["lng"], dist["lat"], dist["lng"])
    speed = dist_km / max(hours, 0.01)

    return [{
        "medicine_id":                    med_id,
        "batch_id":                       batch_id,
        "medicine_name":                  medicine_name,
        "from_role":                      "Pharmacy",
        "to_role":                        "Distributor",
        "from_lat":                       pharm["lat"],
        "from_lng":                       pharm["lng"],
        "to_lat":                         dist["lat"],
        "to_lng":                         dist["lng"],
        "timestamp":                      ts.isoformat(),
        "transfer_number":                1,
        "time_since_last_transfer_hours": round(hours, 2),
        "distance_km":                    round(dist_km, 2),
        "speed_kmh":                      round(speed, 2),
        "hour_of_day":                    ts.hour,
        "is_weekend":                     int(ts.weekday() >= 5),
        "path_sequence":                  "Pharmacy->Distributor",
        "is_anomaly":                     1,
        "anomaly_type":                   "reverse_flow",
    }]


def _anomaly_geographic_impossibility(start_time: datetime) -> List[Dict[str, Any]]:
    """Destination outside India or impossibly far."""
    med_id = _medicine_id()
    batch_id = _batch_id()
    medicine_name = random.choice(MEDICINE_NAMES)

    mfg = _pick_location(MANUFACTURING_HUBS)
    # Random point way outside India.
    fake_lat = random.uniform(-10, 5)
    fake_lng = random.uniform(100, 140)

    hours = random.uniform(1, 6)
    ts = start_time + timedelta(hours=hours)
    dist_km = _haversine(mfg["lat"], mfg["lng"], fake_lat, fake_lng)
    speed = dist_km / max(hours, 0.01)

    return [{
        "medicine_id":                    med_id,
        "batch_id":                       batch_id,
        "medicine_name":                  medicine_name,
        "from_role":                      "Manufacturer",
        "to_role":                        "Distributor",
        "from_lat":                       mfg["lat"],
        "from_lng":                       mfg["lng"],
        "to_lat":                         round(fake_lat, 6),
        "to_lng":                         round(fake_lng, 6),
        "timestamp":                      ts.isoformat(),
        "transfer_number":                1,
        "time_since_last_transfer_hours": round(hours, 2),
        "distance_km":                    round(dist_km, 2),
        "speed_kmh":                      round(speed, 2),
        "hour_of_day":                    ts.hour,
        "is_weekend":                     int(ts.weekday() >= 5),
        "path_sequence":                  "Manufacturer->Distributor",
        "is_anomaly":                     1,
        "anomaly_type":                   "geographic_impossibility",
    }]


def _anomaly_excessive_transfers(start_time: datetime) -> List[Dict[str, Any]]:
    """Too many handoffs (7-12 hops instead of normal 3)."""
    med_id = _medicine_id()
    batch_id = _batch_id()
    medicine_name = random.choice(MEDICINE_NAMES)

    n_hops = random.randint(7, 12)
    all_locs = MANUFACTURING_HUBS + DISTRIBUTION_HUBS + PHARMACY_LOCATIONS
    roles_cycle = ["Manufacturer", "Distributor", "Distributor", "Distributor",
                   "Pharmacy", "Distributor", "Pharmacy", "Distributor",
                   "Pharmacy", "Distributor", "Pharmacy", "Consumer"]

    rows: List[Dict[str, Any]] = []
    ts = start_time

    for i in range(n_hops):
        from_loc = _pick_location(all_locs)
        to_loc = _pick_location(all_locs)
        from_role = roles_cycle[i % len(roles_cycle)]
        to_role = roles_cycle[(i + 1) % len(roles_cycle)]

        hours = random.uniform(1, 12)
        ts = ts + timedelta(hours=hours)
        dist_km = _haversine(from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"])
        speed = dist_km / max(hours, 0.01)

        rows.append({
            "medicine_id":                    med_id,
            "batch_id":                       batch_id,
            "medicine_name":                  medicine_name,
            "from_role":                      from_role,
            "to_role":                        to_role,
            "from_lat":                       from_loc["lat"],
            "from_lng":                       from_loc["lng"],
            "to_lat":                         to_loc["lat"],
            "to_lng":                         to_loc["lng"],
            "timestamp":                      ts.isoformat(),
            "transfer_number":                i + 1,
            "time_since_last_transfer_hours": round(hours, 2),
            "distance_km":                    round(dist_km, 2),
            "speed_kmh":                      round(speed, 2),
            "hour_of_day":                    ts.hour,
            "is_weekend":                     int(ts.weekday() >= 5),
            "path_sequence":                  f"{from_role}->{to_role}",
            "is_anomaly":                     1,
            "anomaly_type":                   "excessive_transfers",
        })

    return rows


def _anomaly_suspicious_timing(start_time: datetime) -> List[Dict[str, Any]]:
    """Transfers happening at suspicious hours (2-5 AM on weekdays)."""
    rows = _generate_normal_chain(start_time)
    idx = random.randint(0, len(rows) - 1)
    r = rows[idx]

    # Force to a weekday 2-5 AM.
    old_ts = datetime.fromisoformat(r["timestamp"])
    # Move to next weekday.
    while old_ts.weekday() >= 5:
        old_ts += timedelta(days=1)
    suspicious_hour = random.randint(2, 4)
    new_ts = old_ts.replace(hour=suspicious_hour, minute=random.randint(0, 59))
    r["timestamp"] = new_ts.isoformat()
    r["hour_of_day"] = new_ts.hour
    r["is_weekend"] = 0
    r["is_anomaly"] = 1
    r["anomaly_type"] = "suspicious_timing"
    return rows


# Map anomaly type to generator function.
ANOMALY_GENERATORS = {
    "velocity_violation":       _anomaly_velocity_violation,
    "path_deviation":           _anomaly_path_deviation,
    "duplicate_scan":           _anomaly_duplicate_scan,
    "reverse_flow":             _anomaly_reverse_flow,
    "geographic_impossibility": _anomaly_geographic_impossibility,
    "excessive_transfers":      _anomaly_excessive_transfers,
    "suspicious_timing":        _anomaly_suspicious_timing,
}


# ---------------------------------------------------------------------------
#  Main generator
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "medicine_id", "batch_id", "medicine_name",
    "from_role", "to_role",
    "from_lat", "from_lng", "to_lat", "to_lng",
    "timestamp", "transfer_number",
    "time_since_last_transfer_hours", "distance_km", "speed_kmh",
    "hour_of_day", "is_weekend", "path_sequence",
    "is_anomaly", "anomaly_type",
]


def generate_supply_chain_data(
    n_normal: int = 10_000,
    n_anomaly: int = 500,
    seed: int = 42,
) -> Path:
    """Generate the full supply-chain transaction dataset.

    Parameters
    ----------
    n_normal:
        Number of normal end-to-end supply-chain flows to generate.
        Each flow produces 3 transfer rows (Mfg->Dist->Pharm->Consumer).
    n_anomaly:
        Number of anomalous chains to inject.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    Path
        Path to the output CSV file.
    """
    random.seed(seed)

    out_path = SYNTHETIC_DIR / "supply_chain_transactions.csv"

    # Time window: past 180 days.
    end = datetime(2025, 6, 1)
    start = end - timedelta(days=180)

    all_rows: List[Dict[str, Any]] = []

    # --- Normal chains -------------------------------------------------------
    print(f"[SupplyChain] Generating {n_normal} normal chains ...")
    for i in range(n_normal):
        t0 = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        chain = _generate_normal_chain(t0)
        all_rows.extend(chain)
        if (i + 1) % 2000 == 0:
            print(f"  normal: {i + 1} / {n_normal}")

    # --- Anomalous chains ----------------------------------------------------
    anomaly_types = list(ANOMALY_GENERATORS.keys())
    anomaly_counts = {k: 0 for k in anomaly_types}

    print(f"[SupplyChain] Generating {n_anomaly} anomalous chains ...")
    for i in range(n_anomaly):
        atype = random.choice(anomaly_types)
        t0 = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        gen_fn = ANOMALY_GENERATORS[atype]
        rows = gen_fn(t0)
        all_rows.extend(rows)
        anomaly_counts[atype] += 1

    # --- Sort by timestamp and write -----------------------------------------
    all_rows.sort(key=lambda r: r["timestamp"])

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    total = len(all_rows)
    anom = sum(1 for r in all_rows if r["is_anomaly"])
    print(f"[SupplyChain] Wrote {total} rows ({total - anom} normal, {anom} anomalous) to {out_path}")
    print(f"[SupplyChain] Anomaly breakdown: {json.dumps(anomaly_counts, indent=2)}")

    return out_path


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic supply-chain transactions.")
    parser.add_argument("--normal", type=int, default=10_000, help="Number of normal chains (default 10000).")
    parser.add_argument("--anomaly", type=int, default=500, help="Number of anomalous chains (default 500).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    args = parser.parse_args()

    generate_supply_chain_data(n_normal=args.normal, n_anomaly=args.anomaly, seed=args.seed)
    print("Done.")
