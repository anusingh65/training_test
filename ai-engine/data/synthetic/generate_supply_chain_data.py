"""
Synthetic supply-chain transaction generator v2 for MediChain.

Produces a realistic dataset of pharmaceutical supply-chain transfers across
India with all **17 features** required by the anomaly detector, plus metadata.

Reference data consumed
-----------------------
* ``indian_pharma_hubs.json``      — locations, drugs, hotspots, scanners
* ``indian_supply_chain_actors.py`` — manufacturers, distributors, pharmacies
* ``route_templates.json``          — 95 realistic route templates
* ``india_seasonal_patterns.py``    — temporal/seasonal/disease patterns

Normal flow
-----------
Manufacturer -> Distributor -> Pharmacy -> Consumer  (3 transfer legs)

Anomaly types (8)
-----------------
* velocity_violation        — speed exceeds physical possibility
* path_deviation            — skips a step in the expected role sequence
* duplicate_scan            — same medicine scanned twice at the same stage
* reverse_flow              — goods move backward in the supply chain
* geographic_impossibility  — destination outside India or impossibly far
* excessive_transfers       — too many handoffs (7-12 hops)
* suspicious_timing         — transfers at 2-5 AM on weekdays
* hotspot_routing           — drugs routed through known counterfeit hotspots

Output columns (17 features + metadata)
---------------------------------------
See FIELDNAMES below.

Usage
-----
    python -m data.synthetic.generate_supply_chain_data
    python -m data.synthetic.generate_supply_chain_data --normal 20000 --anomaly 1000
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
#  Path setup
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_AI_ENGINE_DIR = _THIS_DIR.parent.parent

if str(_AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_DIR))

from config import SYNTHETIC_DIR

# ---------------------------------------------------------------------------
#  Reference data imports
# ---------------------------------------------------------------------------
from data.synthetic.indian_supply_chain_actors import (
    MANUFACTURERS,
    DISTRIBUTORS,
    PHARMACIES,
    MANUFACTURERS_BY_TYPE,
    DISTRIBUTORS_BY_TYPE,
)
from data.synthetic.india_seasonal_patterns import (
    get_demand_multiplier,
    get_counterfeit_risk,
    get_hour_activity_weight,
    get_anomaly_hour_modifier,
)

# JSON reference data
_HUBS_DATA = json.loads((_THIS_DIR / "indian_pharma_hubs.json").read_text())
_ROUTES_DATA = json.loads((_THIS_DIR / "route_templates.json").read_text())

MANUFACTURING_HUBS: List[Dict] = _HUBS_DATA["manufacturing_hubs"]
DISTRIBUTION_HUBS: List[Dict] = _HUBS_DATA["distribution_hubs"]
PHARMACY_LOCATIONS: List[Dict] = _HUBS_DATA["pharmacy_locations"]
KNOWN_HOTSPOTS: List[Dict] = _HUBS_DATA["known_hotspots"]
DRUG_CATALOG: List[Dict] = _HUBS_DATA["drug_catalog"]
SCANNER_DEVICES: List[Dict] = _HUBS_DATA["scanner_devices"]
ROUTE_TEMPLATES: List[Dict] = _ROUTES_DATA["routes"]

# Pre-compute hotspot coords as numpy-free list for distance lookups
_HOTSPOT_COORDS = [(h["lat"], h["lng"]) for h in KNOWN_HOTSPOTS]

# Drug selection weights: higher-risk drugs appear more in anomalous chains
_DRUG_RISK_WEIGHTS = {
    "critical": 4.0,
    "high": 2.5,
    "medium": 1.5,
    "low": 1.0,
}

# Transit time ranges by leg (hours)
TRANSIT_HOURS = {
    ("Manufacturer", "Distributor"): (8, 72),
    ("Distributor", "Pharmacy"): (4, 48),
    ("Pharmacy", "Consumer"): (0.1, 4),
    ("Distributor", "Distributor"): (6, 36),
}

# Consumer jitter (km) — how far a consumer might be from a pharmacy
CONSUMER_JITTER_KM = 5

# ---------------------------------------------------------------------------
#  17 feature columns (must match anomaly_detector.py)
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "transfer_velocity_kmh",
    "time_since_last_transfer_hours",
    "transfer_count",
    "scan_frequency_24h",
    "unique_devices_24h",
    "path_deviation_score",
    "geographic_consistency",
    "hour_of_day",
    "is_weekend",
    "days_since_manufacture",
    "batch_anomaly_rate",
    "actor_reputation_score",
    "proximity_to_hotspot_km",
    "days_until_expiry",
    "route_directness_ratio",
    "distributor_hop_count",
    "price_deviation_score",
]

FIELDNAMES = [
    "medicine_id",
    "batch_id",
    "medicine_name",
    "drug_category",
    "manufacturer",
    "from_role",
    "to_role",
    "from_lat",
    "from_lng",
    "to_lat",
    "to_lng",
    "timestamp",
    "manufacture_date",
    "expiry_date",
    "mrp",
    "transaction_price",
    *FEATURE_COLUMNS,
    "path_sequence",
    "is_anomaly",
    "anomaly_type",
]


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    rlat1, rlng1 = math.radians(lat1), math.radians(lng1)
    rlat2, rlng2 = math.radians(lat2), math.radians(lng2)
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def _medicine_id() -> str:
    return f"MED-{random.getrandbits(48):012X}"


def _batch_id() -> str:
    return f"BATCH-{random.getrandbits(32):08X}"


def _jitter(lat: float, lng: float, km: float = 1.0) -> Tuple[float, float]:
    """Add random jitter (approx km) to coordinates."""
    dlat = (random.uniform(-km, km)) / 111.0
    dlng = (random.uniform(-km, km)) / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    return round(lat + dlat, 6), round(lng + dlng, 6)


def _pick_loc(locations: List[Dict]) -> Dict:
    return random.choice(locations)


def _pick_drug(anomalous: bool = False) -> Dict:
    """Pick a drug from catalog. If anomalous, weight toward high-risk drugs."""
    if anomalous:
        weights = [_DRUG_RISK_WEIGHTS.get(d.get("counterfeit_risk", "low"), 1.0) for d in DRUG_CATALOG]
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0.0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return DRUG_CATALOG[i]
        return DRUG_CATALOG[-1]
    return random.choice(DRUG_CATALOG)


def _pick_manufacturer() -> Dict:
    """Pick a manufacturer actor."""
    return random.choice(MANUFACTURERS)


def _pick_distributor() -> Dict:
    """Pick a distributor actor."""
    return random.choice(DISTRIBUTORS)


def _pick_pharmacy() -> Dict:
    """Pick a pharmacy actor."""
    return random.choice(PHARMACIES)


def _nearest_hotspot_km(lat: float, lng: float) -> float:
    """Distance to nearest known counterfeit hotspot in km."""
    if not _HOTSPOT_COORDS:
        return 999.0
    return min(_haversine(lat, lng, hlat, hlng) for hlat, hlng in _HOTSPOT_COORDS)


def _normalize_reputation(score: int) -> float:
    """Normalize reputation score (300-700 range) to 0-1."""
    return max(0.0, min(1.0, (score - 300) / 400.0))


def _geographic_consistency(from_lat: float, from_lng: float,
                            to_lat: float, to_lng: float) -> float:
    """Score 0-1 indicating if transfer is geographically consistent with India."""
    # Check both points are in India bounding box (6-37°N, 68-98°E)
    in_india_from = (6.0 <= from_lat <= 37.0) and (68.0 <= from_lng <= 98.0)
    in_india_to = (6.0 <= to_lat <= 37.0) and (68.0 <= to_lng <= 98.0)

    if not in_india_from or not in_india_to:
        return 0.0

    dist = _haversine(from_lat, from_lng, to_lat, to_lng)
    # Max reasonable distance within India ~3500 km
    if dist > 3500:
        return 0.1
    if dist > 2500:
        return 0.5
    return min(1.0, 0.7 + 0.3 * (1.0 - dist / 3500.0))


def _path_deviation_score(path_roles: List[str]) -> float:
    """Score 0-1 indicating path deviation. 0 = perfect flow, 1 = completely wrong."""
    expected = ["Manufacturer", "Distributor", "Pharmacy", "Consumer"]
    if len(path_roles) < 2:
        return 0.0
    # Check each transition
    violations = 0
    total_transitions = len(path_roles) - 1
    for i in range(total_transitions):
        fr, to = path_roles[i], path_roles[i + 1]
        # Normal forward transitions
        valid = {
            ("Manufacturer", "Distributor"),
            ("Distributor", "Pharmacy"),
            ("Distributor", "Distributor"),
            ("Pharmacy", "Consumer"),
        }
        if (fr, to) not in valid:
            violations += 1
    return round(violations / max(total_transitions, 1), 4)


def _route_directness(waypoints: List[Tuple[float, float]]) -> float:
    """Ratio of straight-line distance to cumulative distance. 1.0 = perfectly direct."""
    if len(waypoints) < 2:
        return 1.0
    straight = _haversine(waypoints[0][0], waypoints[0][1],
                          waypoints[-1][0], waypoints[-1][1])
    cumulative = sum(
        _haversine(waypoints[i][0], waypoints[i][1],
                   waypoints[i + 1][0], waypoints[i + 1][1])
        for i in range(len(waypoints) - 1)
    )
    if cumulative < 1.0:
        return 1.0
    return round(min(1.0, straight / cumulative), 4)


def _sample_hour(month: int, facility_type: str = "distribution_warehouse") -> int:
    """Sample an hour weighted by operating patterns."""
    weights = []
    for h in range(24):
        weights.append(max(0.01, get_hour_activity_weight(h, facility_type)))
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0.0
    for h, w in enumerate(weights):
        cumulative += w
        if r <= cumulative:
            return h
    return 12


# ---------------------------------------------------------------------------
#  Normal chain generator
# ---------------------------------------------------------------------------

def _generate_normal_chain(
    start_time: datetime,
    batch_id: str,
    batch_drug: Dict,
    manufacturer_actor: Dict,
    batch_anomaly_rate: float = 0.0,
) -> List[Dict[str, Any]]:
    """Generate a Manufacturer -> Distributor -> Pharmacy -> Consumer chain."""
    med_id = _medicine_id()
    drug = batch_drug
    drug_name = drug["name"]
    drug_cat = drug.get("category", "unknown")
    mrp = drug.get("mrp", 50.0)
    shelf_life = drug.get("shelf_life_months", 24)

    # Dates
    days_before = random.randint(1, 180)
    manufacture_date = start_time - timedelta(days=days_before + random.randint(30, 365))
    expiry_date = manufacture_date + timedelta(days=shelf_life * 30)

    # Actors
    mfg_actor = manufacturer_actor
    dist_actor = _pick_distributor()
    pharm_actor = _pick_pharmacy()

    # Locations
    mfg = _pick_loc(MANUFACTURING_HUBS)
    dist = _pick_loc(DISTRIBUTION_HUBS)
    pharm = _pick_loc(PHARMACY_LOCATIONS)
    cons_lat, cons_lng = _jitter(pharm["lat"], pharm["lng"], km=CONSUMER_JITTER_KM)

    chain_nodes = [
        ("Manufacturer", mfg, mfg_actor),
        ("Distributor", dist, dist_actor),
        ("Pharmacy", pharm, pharm_actor),
        ("Consumer", {"lat": cons_lat, "lng": cons_lng, "name": "Consumer"}, None),
    ]

    waypoints = [(n[1]["lat"], n[1]["lng"]) for n in chain_nodes]
    directness = _route_directness(waypoints)
    path_roles = [n[0] for n in chain_nodes]
    path_dev = _path_deviation_score(path_roles)

    rows: List[Dict[str, Any]] = []
    ts = start_time
    month = ts.month

    for i in range(1, len(chain_nodes)):
        from_role, from_loc, from_actor = chain_nodes[i - 1]
        to_role, to_loc, to_actor = chain_nodes[i]

        # Transit time
        lo, hi = TRANSIT_HOURS.get((from_role, to_role), (2, 48))
        hours = random.uniform(lo, hi)

        # Apply seasonal delay
        demand_mult = get_demand_multiplier(month, drug_cat)
        if demand_mult > 1.2:
            hours *= random.uniform(1.0, 1.3)

        # Sample a plausible hour for arrival
        facility = "pharmacy_retail" if to_role == "Pharmacy" else "distribution_warehouse"
        arrival_hour = _sample_hour(month, facility)
        ts = ts + timedelta(hours=hours)
        ts = ts.replace(hour=arrival_hour, minute=random.randint(0, 59),
                         second=random.randint(0, 59))

        dist_km = _haversine(from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"])
        velocity = dist_km / max(hours, 0.01)

        # Actor reputation (use "from" actor for the transfer)
        actor = from_actor or to_actor
        rep_score = _normalize_reputation(
            actor.get("reputation_score", 500) if actor else 500
        )

        # Scan simulation
        scan_freq = random.randint(1, 3)
        unique_devices = random.randint(1, 2)

        # Price: normal = within 5% of MRP
        price_mult = random.uniform(0.90, 1.05)
        transaction_price = round(mrp * price_mult, 2)
        price_dev = round(abs(transaction_price - mrp) / max(mrp, 0.01), 4)

        # Proximity to hotspot
        mid_lat = (from_loc["lat"] + to_loc["lat"]) / 2
        mid_lng = (from_loc["lng"] + to_loc["lng"]) / 2
        hotspot_km = round(_nearest_hotspot_km(mid_lat, mid_lng), 2)

        # Days calculations
        dsm = max(0, (ts - manufacture_date).days)
        dte = max(0, (expiry_date - ts).days)

        geo_con = _geographic_consistency(from_loc["lat"], from_loc["lng"],
                                          to_loc["lat"], to_loc["lng"])

        rows.append({
            "medicine_id": med_id,
            "batch_id": batch_id,
            "medicine_name": drug_name,
            "drug_category": drug_cat,
            "manufacturer": mfg_actor.get("name", "Unknown"),
            "from_role": from_role,
            "to_role": to_role,
            "from_lat": round(from_loc["lat"], 6),
            "from_lng": round(from_loc["lng"], 6),
            "to_lat": round(to_loc["lat"], 6),
            "to_lng": round(to_loc["lng"], 6),
            "timestamp": ts.isoformat(),
            "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "mrp": mrp,
            "transaction_price": transaction_price,
            # 17 features
            "transfer_velocity_kmh": round(velocity, 2),
            "time_since_last_transfer_hours": round(hours, 2),
            "transfer_count": i,
            "scan_frequency_24h": scan_freq,
            "unique_devices_24h": unique_devices,
            "path_deviation_score": path_dev,
            "geographic_consistency": round(geo_con, 4),
            "hour_of_day": ts.hour,
            "is_weekend": int(ts.weekday() >= 5),
            "days_since_manufacture": dsm,
            "batch_anomaly_rate": round(batch_anomaly_rate, 4),
            "actor_reputation_score": round(rep_score, 4),
            "proximity_to_hotspot_km": hotspot_km,
            "days_until_expiry": dte,
            "route_directness_ratio": directness,
            "distributor_hop_count": 1,
            "price_deviation_score": price_dev,
            "path_sequence": f"{from_role}->{to_role}",
            "is_anomaly": 0,
            "anomaly_type": "",
        })

    return rows


# ---------------------------------------------------------------------------
#  Anomaly generators
# ---------------------------------------------------------------------------

def _anomaly_velocity_violation(start_time: datetime, batch_id: str,
                                 drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Transfer speed exceeds physical possibility (>900 km/h by road)."""
    rows = _generate_normal_chain(start_time, batch_id, drug, mfg, bar)
    idx = random.randint(0, len(rows) - 1)
    r = rows[idx]
    r["time_since_last_transfer_hours"] = round(random.uniform(0.01, 0.1), 4)
    dist_km = _haversine(r["from_lat"], r["from_lng"], r["to_lat"], r["to_lng"])
    r["transfer_velocity_kmh"] = round(dist_km / r["time_since_last_transfer_hours"], 2)
    r["is_anomaly"] = 1
    r["anomaly_type"] = "velocity_violation"
    return rows


def _anomaly_path_deviation(start_time: datetime, batch_id: str,
                             drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Skip distributor: Manufacturer -> Pharmacy directly."""
    med_id = _medicine_id()
    drug_name = drug["name"]
    drug_cat = drug.get("category", "unknown")
    mrp = drug.get("mrp", 50.0)
    shelf_life = drug.get("shelf_life_months", 24)
    manufacture_date = start_time - timedelta(days=random.randint(30, 365))
    expiry_date = manufacture_date + timedelta(days=shelf_life * 30)

    mfg_loc = _pick_loc(MANUFACTURING_HUBS)
    pharm_loc = _pick_loc(PHARMACY_LOCATIONS)
    hours = random.uniform(6, 48)
    ts = start_time + timedelta(hours=hours)
    dist_km = _haversine(mfg_loc["lat"], mfg_loc["lng"], pharm_loc["lat"], pharm_loc["lng"])
    velocity = dist_km / max(hours, 0.01)
    rep = _normalize_reputation(mfg.get("reputation_score", 500))
    mid_lat = (mfg_loc["lat"] + pharm_loc["lat"]) / 2
    mid_lng = (mfg_loc["lng"] + pharm_loc["lng"]) / 2
    price = round(mrp * random.uniform(0.70, 0.95), 2)

    return [{
        "medicine_id": med_id, "batch_id": batch_id,
        "medicine_name": drug_name, "drug_category": drug_cat,
        "manufacturer": mfg.get("name", "Unknown"),
        "from_role": "Manufacturer", "to_role": "Pharmacy",
        "from_lat": mfg_loc["lat"], "from_lng": mfg_loc["lng"],
        "to_lat": pharm_loc["lat"], "to_lng": pharm_loc["lng"],
        "timestamp": ts.isoformat(),
        "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "mrp": mrp, "transaction_price": price,
        "transfer_velocity_kmh": round(velocity, 2),
        "time_since_last_transfer_hours": round(hours, 2),
        "transfer_count": 1,
        "scan_frequency_24h": random.randint(1, 2),
        "unique_devices_24h": 1,
        "path_deviation_score": 1.0,
        "geographic_consistency": round(_geographic_consistency(
            mfg_loc["lat"], mfg_loc["lng"], pharm_loc["lat"], pharm_loc["lng"]), 4),
        "hour_of_day": ts.hour,
        "is_weekend": int(ts.weekday() >= 5),
        "days_since_manufacture": max(0, (ts - manufacture_date).days),
        "batch_anomaly_rate": round(bar, 4),
        "actor_reputation_score": round(rep, 4),
        "proximity_to_hotspot_km": round(_nearest_hotspot_km(mid_lat, mid_lng), 2),
        "days_until_expiry": max(0, (expiry_date - ts).days),
        "route_directness_ratio": 1.0,
        "distributor_hop_count": 0,
        "price_deviation_score": round(abs(price - mrp) / max(mrp, 0.01), 4),
        "path_sequence": "Manufacturer->Pharmacy",
        "is_anomaly": 1, "anomaly_type": "path_deviation",
    }]


def _anomaly_duplicate_scan(start_time: datetime, batch_id: str,
                             drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Same medicine scanned twice at the same stage."""
    rows = _generate_normal_chain(start_time, batch_id, drug, mfg, bar)
    dup = dict(rows[0])
    dup_ts = datetime.fromisoformat(dup["timestamp"]) + timedelta(seconds=random.randint(5, 120))
    dup["timestamp"] = dup_ts.isoformat()
    dup["scan_frequency_24h"] = random.randint(4, 8)
    dup["unique_devices_24h"] = random.randint(2, 4)
    dup["is_anomaly"] = 1
    dup["anomaly_type"] = "duplicate_scan"
    rows.append(dup)
    return rows


def _anomaly_reverse_flow(start_time: datetime, batch_id: str,
                           drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Goods move backward: Pharmacy -> Distributor."""
    med_id = _medicine_id()
    drug_name = drug["name"]
    drug_cat = drug.get("category", "unknown")
    mrp = drug.get("mrp", 50.0)
    shelf_life = drug.get("shelf_life_months", 24)
    manufacture_date = start_time - timedelta(days=random.randint(30, 365))
    expiry_date = manufacture_date + timedelta(days=shelf_life * 30)

    pharm_loc = _pick_loc(PHARMACY_LOCATIONS)
    dist_loc = _pick_loc(DISTRIBUTION_HUBS)
    hours = random.uniform(2, 24)
    ts = start_time + timedelta(hours=hours)
    dist_km = _haversine(pharm_loc["lat"], pharm_loc["lng"], dist_loc["lat"], dist_loc["lng"])
    velocity = dist_km / max(hours, 0.01)
    rep = _normalize_reputation(mfg.get("reputation_score", 500))
    mid_lat = (pharm_loc["lat"] + dist_loc["lat"]) / 2
    mid_lng = (pharm_loc["lng"] + dist_loc["lng"]) / 2
    price = round(mrp * random.uniform(0.60, 0.85), 2)

    return [{
        "medicine_id": med_id, "batch_id": batch_id,
        "medicine_name": drug_name, "drug_category": drug_cat,
        "manufacturer": mfg.get("name", "Unknown"),
        "from_role": "Pharmacy", "to_role": "Distributor",
        "from_lat": pharm_loc["lat"], "from_lng": pharm_loc["lng"],
        "to_lat": dist_loc["lat"], "to_lng": dist_loc["lng"],
        "timestamp": ts.isoformat(),
        "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "mrp": mrp, "transaction_price": price,
        "transfer_velocity_kmh": round(velocity, 2),
        "time_since_last_transfer_hours": round(hours, 2),
        "transfer_count": 1,
        "scan_frequency_24h": random.randint(1, 3),
        "unique_devices_24h": random.randint(1, 2),
        "path_deviation_score": 1.0,
        "geographic_consistency": round(_geographic_consistency(
            pharm_loc["lat"], pharm_loc["lng"], dist_loc["lat"], dist_loc["lng"]), 4),
        "hour_of_day": ts.hour,
        "is_weekend": int(ts.weekday() >= 5),
        "days_since_manufacture": max(0, (ts - manufacture_date).days),
        "batch_anomaly_rate": round(bar, 4),
        "actor_reputation_score": round(rep, 4),
        "proximity_to_hotspot_km": round(_nearest_hotspot_km(mid_lat, mid_lng), 2),
        "days_until_expiry": max(0, (expiry_date - ts).days),
        "route_directness_ratio": 1.0,
        "distributor_hop_count": 0,
        "price_deviation_score": round(abs(price - mrp) / max(mrp, 0.01), 4),
        "path_sequence": "Pharmacy->Distributor",
        "is_anomaly": 1, "anomaly_type": "reverse_flow",
    }]


def _anomaly_geographic_impossibility(start_time: datetime, batch_id: str,
                                       drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Destination outside India or impossibly far."""
    med_id = _medicine_id()
    drug_name = drug["name"]
    drug_cat = drug.get("category", "unknown")
    mrp = drug.get("mrp", 50.0)
    shelf_life = drug.get("shelf_life_months", 24)
    manufacture_date = start_time - timedelta(days=random.randint(30, 365))
    expiry_date = manufacture_date + timedelta(days=shelf_life * 30)

    mfg_loc = _pick_loc(MANUFACTURING_HUBS)
    fake_lat = random.uniform(-10, 5)
    fake_lng = random.uniform(100, 140)
    hours = random.uniform(1, 6)
    ts = start_time + timedelta(hours=hours)
    dist_km = _haversine(mfg_loc["lat"], mfg_loc["lng"], fake_lat, fake_lng)
    velocity = dist_km / max(hours, 0.01)
    rep = _normalize_reputation(mfg.get("reputation_score", 500))
    price = round(mrp * random.uniform(0.50, 0.80), 2)

    return [{
        "medicine_id": med_id, "batch_id": batch_id,
        "medicine_name": drug_name, "drug_category": drug_cat,
        "manufacturer": mfg.get("name", "Unknown"),
        "from_role": "Manufacturer", "to_role": "Distributor",
        "from_lat": mfg_loc["lat"], "from_lng": mfg_loc["lng"],
        "to_lat": round(fake_lat, 6), "to_lng": round(fake_lng, 6),
        "timestamp": ts.isoformat(),
        "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "mrp": mrp, "transaction_price": price,
        "transfer_velocity_kmh": round(velocity, 2),
        "time_since_last_transfer_hours": round(hours, 2),
        "transfer_count": 1,
        "scan_frequency_24h": random.randint(1, 2),
        "unique_devices_24h": 1,
        "path_deviation_score": 0.0,
        "geographic_consistency": 0.0,
        "hour_of_day": ts.hour,
        "is_weekend": int(ts.weekday() >= 5),
        "days_since_manufacture": max(0, (ts - manufacture_date).days),
        "batch_anomaly_rate": round(bar, 4),
        "actor_reputation_score": round(rep, 4),
        "proximity_to_hotspot_km": 999.0,
        "days_until_expiry": max(0, (expiry_date - ts).days),
        "route_directness_ratio": 1.0,
        "distributor_hop_count": 0,
        "price_deviation_score": round(abs(price - mrp) / max(mrp, 0.01), 4),
        "path_sequence": "Manufacturer->Distributor",
        "is_anomaly": 1, "anomaly_type": "geographic_impossibility",
    }]


def _anomaly_excessive_transfers(start_time: datetime, batch_id: str,
                                  drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Too many handoffs (7-12 hops)."""
    med_id = _medicine_id()
    drug_name = drug["name"]
    drug_cat = drug.get("category", "unknown")
    mrp = drug.get("mrp", 50.0)
    shelf_life = drug.get("shelf_life_months", 24)
    manufacture_date = start_time - timedelta(days=random.randint(30, 365))
    expiry_date = manufacture_date + timedelta(days=shelf_life * 30)

    n_hops = random.randint(7, 12)
    all_locs = MANUFACTURING_HUBS + DISTRIBUTION_HUBS + PHARMACY_LOCATIONS
    roles = ["Manufacturer", "Distributor", "Distributor", "Distributor",
             "Pharmacy", "Distributor", "Pharmacy", "Distributor",
             "Pharmacy", "Distributor", "Pharmacy", "Consumer"]

    rows = []
    ts = start_time
    waypoints = []
    rep = _normalize_reputation(mfg.get("reputation_score", 500))

    for i in range(n_hops):
        from_loc = _pick_loc(all_locs)
        to_loc = _pick_loc(all_locs)
        from_role = roles[i % len(roles)]
        to_role = roles[(i + 1) % len(roles)]
        waypoints.append((from_loc["lat"], from_loc["lng"]))

        hours = random.uniform(1, 12)
        ts = ts + timedelta(hours=hours)
        dist_km = _haversine(from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"])
        velocity = dist_km / max(hours, 0.01)
        mid_lat = (from_loc["lat"] + to_loc["lat"]) / 2
        mid_lng = (from_loc["lng"] + to_loc["lng"]) / 2
        price = round(mrp * random.uniform(0.80, 1.10), 2)

        rows.append({
            "medicine_id": med_id, "batch_id": batch_id,
            "medicine_name": drug_name, "drug_category": drug_cat,
            "manufacturer": mfg.get("name", "Unknown"),
            "from_role": from_role, "to_role": to_role,
            "from_lat": from_loc["lat"], "from_lng": from_loc["lng"],
            "to_lat": to_loc["lat"], "to_lng": to_loc["lng"],
            "timestamp": ts.isoformat(),
            "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "mrp": mrp, "transaction_price": price,
            "transfer_velocity_kmh": round(velocity, 2),
            "time_since_last_transfer_hours": round(hours, 2),
            "transfer_count": i + 1,
            "scan_frequency_24h": random.randint(3, 10),
            "unique_devices_24h": random.randint(3, 8),
            "path_deviation_score": round(min(1.0, i / 5.0), 4),
            "geographic_consistency": round(_geographic_consistency(
                from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"]), 4),
            "hour_of_day": ts.hour,
            "is_weekend": int(ts.weekday() >= 5),
            "days_since_manufacture": max(0, (ts - manufacture_date).days),
            "batch_anomaly_rate": round(bar, 4),
            "actor_reputation_score": round(rep * random.uniform(0.6, 0.9), 4),
            "proximity_to_hotspot_km": round(_nearest_hotspot_km(mid_lat, mid_lng), 2),
            "days_until_expiry": max(0, (expiry_date - ts).days),
            "route_directness_ratio": round(random.uniform(0.1, 0.4), 4),
            "distributor_hop_count": min(i, 6),
            "price_deviation_score": round(abs(price - mrp) / max(mrp, 0.01), 4),
            "path_sequence": f"{from_role}->{to_role}",
            "is_anomaly": 1, "anomaly_type": "excessive_transfers",
        })

    return rows


def _anomaly_suspicious_timing(start_time: datetime, batch_id: str,
                                drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Transfers at suspicious hours (2-5 AM on weekdays)."""
    rows = _generate_normal_chain(start_time, batch_id, drug, mfg, bar)
    idx = random.randint(0, len(rows) - 1)
    r = rows[idx]
    old_ts = datetime.fromisoformat(r["timestamp"])
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


def _anomaly_hotspot_routing(start_time: datetime, batch_id: str,
                              drug: Dict, mfg: Dict, bar: float) -> List[Dict]:
    """Route drugs through a known counterfeit hotspot."""
    med_id = _medicine_id()
    drug_name = drug["name"]
    drug_cat = drug.get("category", "unknown")
    mrp = drug.get("mrp", 50.0)
    shelf_life = drug.get("shelf_life_months", 24)
    manufacture_date = start_time - timedelta(days=random.randint(30, 365))
    expiry_date = manufacture_date + timedelta(days=shelf_life * 30)

    # Pick a hotspot as waypoint
    hotspot = random.choice(KNOWN_HOTSPOTS)
    mfg_loc = _pick_loc(MANUFACTURING_HUBS)
    pharm_loc = _pick_loc(PHARMACY_LOCATIONS)
    rep = _normalize_reputation(mfg.get("reputation_score", 500))

    legs = [
        ("Manufacturer", "Distributor", mfg_loc, hotspot),
        ("Distributor", "Pharmacy", hotspot, pharm_loc),
    ]
    rows = []
    ts = start_time
    for from_role, to_role, from_loc, to_loc in legs:
        hours = random.uniform(4, 36)
        ts = ts + timedelta(hours=hours)
        dist_km = _haversine(from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"])
        velocity = dist_km / max(hours, 0.01)
        mid_lat = (from_loc["lat"] + to_loc["lat"]) / 2
        mid_lng = (from_loc["lng"] + to_loc["lng"]) / 2
        price = round(mrp * random.uniform(0.60, 0.90), 2)

        rows.append({
            "medicine_id": med_id, "batch_id": batch_id,
            "medicine_name": drug_name, "drug_category": drug_cat,
            "manufacturer": mfg.get("name", "Unknown"),
            "from_role": from_role, "to_role": to_role,
            "from_lat": from_loc["lat"], "from_lng": from_loc["lng"],
            "to_lat": to_loc["lat"], "to_lng": to_loc["lng"],
            "timestamp": ts.isoformat(),
            "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "mrp": mrp, "transaction_price": price,
            "transfer_velocity_kmh": round(velocity, 2),
            "time_since_last_transfer_hours": round(hours, 2),
            "transfer_count": len(rows) + 1,
            "scan_frequency_24h": random.randint(2, 5),
            "unique_devices_24h": random.randint(2, 4),
            "path_deviation_score": 0.0,
            "geographic_consistency": round(_geographic_consistency(
                from_loc["lat"], from_loc["lng"], to_loc["lat"], to_loc["lng"]), 4),
            "hour_of_day": ts.hour,
            "is_weekend": int(ts.weekday() >= 5),
            "days_since_manufacture": max(0, (ts - manufacture_date).days),
            "batch_anomaly_rate": round(bar, 4),
            "actor_reputation_score": round(rep * random.uniform(0.5, 0.8), 4),
            "proximity_to_hotspot_km": round(_nearest_hotspot_km(mid_lat, mid_lng), 2),
            "days_until_expiry": max(0, (expiry_date - ts).days),
            "route_directness_ratio": round(random.uniform(0.3, 0.6), 4),
            "distributor_hop_count": 1,
            "price_deviation_score": round(abs(price - mrp) / max(mrp, 0.01), 4),
            "path_sequence": f"{from_role}->{to_role}",
            "is_anomaly": 1, "anomaly_type": "hotspot_routing",
        })

    return rows


# Anomaly type -> generator
ANOMALY_GENERATORS = {
    "velocity_violation": _anomaly_velocity_violation,
    "path_deviation": _anomaly_path_deviation,
    "duplicate_scan": _anomaly_duplicate_scan,
    "reverse_flow": _anomaly_reverse_flow,
    "geographic_impossibility": _anomaly_geographic_impossibility,
    "excessive_transfers": _anomaly_excessive_transfers,
    "suspicious_timing": _anomaly_suspicious_timing,
    "hotspot_routing": _anomaly_hotspot_routing,
}


# ---------------------------------------------------------------------------
#  Main generator
# ---------------------------------------------------------------------------

def generate_supply_chain_data(
    n_normal: int = 10_000,
    n_anomaly: int = 500,
    seed: int = 42,
) -> Path:
    """Generate the full supply-chain transaction dataset with 17 features.

    Parameters
    ----------
    n_normal : int
        Number of normal end-to-end supply-chain flows (each = 3 rows).
    n_anomaly : int
        Number of anomalous chains to inject.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    Path
        Path to the output CSV file.
    """
    random.seed(seed)
    out_path = SYNTHETIC_DIR / "supply_chain_transactions.csv"

    # Time window: past 365 days
    end = datetime(2025, 6, 1)
    start = end - timedelta(days=365)

    all_rows: List[Dict[str, Any]] = []

    # Track batch-level anomaly rates
    batch_anomaly_counts: Dict[str, int] = {}
    batch_total_counts: Dict[str, int] = {}

    # --- Normal chains -------------------------------------------------------
    print(f"[SupplyChain] Generating {n_normal} normal chains (3 rows each) ...")
    batch_size = random.randint(20, 100)
    current_batch = _batch_id()
    current_drug = _pick_drug(anomalous=False)
    current_mfg = _pick_manufacturer()
    batch_count = 0

    for i in range(n_normal):
        # New batch every batch_size medicines
        if batch_count >= batch_size:
            current_batch = _batch_id()
            current_drug = _pick_drug(anomalous=False)
            current_mfg = _pick_manufacturer()
            batch_size = random.randint(20, 100)
            batch_count = 0

        t0 = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        chain = _generate_normal_chain(t0, current_batch, current_drug, current_mfg)
        all_rows.extend(chain)
        batch_count += 1

        batch_total_counts[current_batch] = batch_total_counts.get(current_batch, 0) + 1

        if (i + 1) % 2000 == 0:
            print(f"  normal: {i + 1:,} / {n_normal:,}")

    # --- Anomalous chains ----------------------------------------------------
    anomaly_types = list(ANOMALY_GENERATORS.keys())
    anomaly_counts = {k: 0 for k in anomaly_types}

    print(f"[SupplyChain] Generating {n_anomaly} anomalous chains ...")
    for i in range(n_anomaly):
        atype = random.choice(anomaly_types)
        t0 = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        anom_batch = _batch_id()
        anom_drug = _pick_drug(anomalous=True)
        anom_mfg = _pick_manufacturer()

        gen_fn = ANOMALY_GENERATORS[atype]
        rows = gen_fn(t0, anom_batch, anom_drug, anom_mfg, 0.0)
        all_rows.extend(rows)
        anomaly_counts[atype] += 1

        batch_anomaly_counts[anom_batch] = batch_anomaly_counts.get(anom_batch, 0) + 1
        batch_total_counts[anom_batch] = batch_total_counts.get(anom_batch, 0) + 1

    # --- Post-process: update batch_anomaly_rate for all rows ----------------
    print("[SupplyChain] Computing batch anomaly rates ...")
    for row in all_rows:
        bid = row["batch_id"]
        anom_ct = batch_anomaly_counts.get(bid, 0)
        total_ct = batch_total_counts.get(bid, 1)
        row["batch_anomaly_rate"] = round(anom_ct / total_ct, 4)

    # --- Sort by timestamp and write -----------------------------------------
    all_rows.sort(key=lambda r: r["timestamp"])

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    total = len(all_rows)
    anom = sum(1 for r in all_rows if r["is_anomaly"])
    print(f"[SupplyChain] Wrote {total:,} rows ({total - anom:,} normal, {anom:,} anomalous)")
    print(f"[SupplyChain] Output: {out_path}")
    print(f"[SupplyChain] Anomaly breakdown: {json.dumps(anomaly_counts, indent=2)}")
    print(f"[SupplyChain] Columns: {len(FIELDNAMES)} ({len(FEATURE_COLUMNS)} features)")

    return out_path


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic supply-chain transactions (v2).")
    parser.add_argument("--normal", type=int, default=10_000,
                        help="Number of normal chains (default 10000, each = 3 rows).")
    parser.add_argument("--anomaly", type=int, default=500,
                        help="Number of anomalous chains (default 500).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default 42).")
    args = parser.parse_args()

    generate_supply_chain_data(n_normal=args.normal, n_anomaly=args.anomaly, seed=args.seed)
    print("Done.")
