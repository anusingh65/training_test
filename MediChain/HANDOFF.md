# MediChain AI Engine -- Handoff for Frontend & Blockchain Devs

## What's Done

The **AI backend** is fully functional. It runs as a FastAPI server on port 8000 and provides:

- Anomaly detection (IsolationForest + Autoencoder + 11 rule-based checks)
- Geographic heatmap with DBSCAN clustering, hotspot prediction, route corridor risk
- Batch backtracking (trace a drug batch to its factory, detect common origins)
- Adverse event monitoring (real FDA FAERS API)
- Composite risk scoring (3-signal weighted ensemble, 0-100 trust score)
- Pill image verification (EfficientNet-B0 CNN)
- WebSocket real-time alerts
- Blockchain bridge (read/write to Ethereum smart contracts)

A **test dashboard** exists at `dashboard/` (Next.js 14 + Leaflet). It's functional for demo purposes but is not the final frontend.

---

## Quick Start

```bash
# Backend
cd ai-engine
pip install -r requirements.txt

# Generate synthetic data (run once -- takes ~30 seconds)
python -m data.synthetic.generate_supply_chain_data
python -m data.synthetic.generate_scan_events
python -m data.synthetic.generate_heatmap_seed

# Train anomaly detector (run once -- takes ~10 seconds)
python -m models.train_anomaly_detector

# Start server
SIMULATION_MODE=true uvicorn main:app --reload --port 8000

# Test dashboard (optional)
cd ../dashboard
npm install
npm run dev  # http://localhost:3000
```

The backend auto-loads seed data on startup. All endpoints are available immediately.

---

## API Endpoints

All endpoints are prefixed with `/api`. Interactive docs at `http://localhost:8000/docs`.

### Anomaly Detection

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/detect-anomaly` | Score a single supply chain transaction |
| POST | `/api/detect-anomaly-batch` | Score up to 500 transactions at once |

**Request body** (detect-anomaly):
```json
{
  "transfer_velocity_kmh": 65.0,
  "time_since_last_transfer_hours": 10.5,
  "transfer_count": 3,
  "scan_frequency_24h": 2,
  "unique_devices_24h": 1,
  "path_deviation_score": 0.0,
  "geographic_consistency": 0.95,
  "hour_of_day": 14,
  "is_weekend": 0,
  "days_since_manufacture": 120,
  "batch_anomaly_rate": 0.0,
  "actor_reputation_score": 0.85,
  "proximity_to_hotspot_km": 150.0,
  "days_until_expiry": 400,
  "route_directness_ratio": 0.95,
  "distributor_hop_count": 2,
  "price_deviation_score": 0.03
}
```

**Response:**
```json
{
  "is_anomaly": false,
  "anomaly_score": 0.23,
  "anomaly_type": null,
  "reasons": [],
  "iforest_score": -0.15,
  "autoencoder_score": 0.08,
  "rule_violations": []
}
```

### Heatmap & Geographic Risk

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/heatmap-data?time_window=90d` | Full heatmap: points, clusters, corridors, hotspot activity, state risk |
| GET | `/api/heatmap-zone-risk?lat=28.65&lng=77.23` | Risk assessment at a GPS coordinate |
| GET | `/api/heatmap-stats` | Summary statistics |
| POST | `/api/heatmap-event` | Inject a new scan event into the heatmap |

### Batch Trace (Backtracking)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/batch-trace/batches` | List all batches with anomaly counts (500 flagged out of 671) |
| GET | `/api/batch-trace/{batch_id}` | Full backtrace: origin factory, transfer chain, risk level |
| POST | `/api/batch-trace/common-origin` | Detect if multiple flagged batches share the same factory |

**Common origin request:**
```json
{
  "batch_ids": ["BATCH-BDF4E3E4", "BATCH-2F178380", "BATCH-2EBB445A"]
}
```

**Common origin response (pattern detected):**
```json
{
  "pattern_detected": true,
  "alert": "ALERT: Glenmark Pharmaceuticals in Uttar Pradesh is the common origin for 3 flagged batches affecting Karnataka, Gujarat, Punjab...",
  "common_origins": [{
    "factory": "Glenmark Pharmaceuticals",
    "coords": [26.85, 80.95],
    "state": "Uttar Pradesh",
    "batch_count": 3,
    "batch_ids": ["BATCH-BDF4E3E4", "BATCH-2F178380", "BATCH-2EBB445A"]
  }],
  "batches": [/* individual traces */]
}
```

### Adverse Events (Real FDA Data)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/adverse-events/{drug_name}` | Adverse event analysis from OpenFDA FAERS |
| GET | `/api/drug-identity/{drug_name}` | Drug identity lookup |
| GET | `/api/drug-recalls/{drug_name}` | Drug recall check |

### Risk Scoring

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/risk-score` | Compute composite trust score (0-100) |
| GET | `/api/risk-score/{medicine_id}` | Retrieve cached score |
| GET | `/api/dashboard-stats` | Aggregate stats (total scans, flagged, model availability) |

**Trust score thresholds:**
- 80-100: **low** risk (no action)
- 50-79: **medium** risk (warning)
- 20-49: **high** risk (auto-flag on blockchain)
- 0-19: **critical** risk (auto-flag + alert)

**Signal weights:** supply_chain 45%, geographic_risk 40%, external_factors 15%

When `trust_score < 50`, the backend calls `core.flagDrug(medicineId, severity)` on-chain.

### Pill Image Verification

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/verify-image` | Upload pill image (multipart), returns confidence + prediction |
| POST | `/api/verify-hash` | Compare hash against on-chain contentHash |

### Real-Time Alerts

| Method | Path | Description |
|--------|------|-------------|
| WS | `/ws/alerts` | WebSocket stream of blockchain events (scans, flags, transfers) |

---

## Blockchain Integration Points

The backend already has a `BlockchainBridge` class (`ai-engine/blockchain/bridge.py`) that reads/writes to three contracts:

| Contract | Key Methods |
|----------|------------|
| **PharmaChainCore** | `flagDrug(id, severity)`, `getDrugDetails(id)`, `getMedicineCount()` |
| **PharmaChainScanner** | `logScan(medicineId, lat, lng, location, deviceId)` |
| **PharmaChainBatch** | `logBatchScan(medicineIds, lat, lng, location, deviceId)` |

Coordinates are stored as `int256 * 1e6` (e.g., 28613939 = 28.613939 degrees).

**What the blockchain devs need to wire up:**

1. **Trust score auto-flagging** -- When `POST /api/risk-score` returns `auto_flag: true`, call `core.flagDrug()`. The backend already has the logic in `risk_scorer.py` line 198 but the actual on-chain call depends on the bridge being connected to a live node.

2. **Scan logging** -- After a QR code scan, call `scanner.logScan()` on-chain and simultaneously `POST /api/heatmap-event` to update the heatmap.

3. **Event listener** -- The `BlockchainEventListener` in `blockchain/event_listener.py` polls the chain every 2 seconds and feeds events through the AI pipeline. It runs automatically on startup. In `SIMULATION_MODE=true`, it replays synthetic events instead.

**Environment variables needed** (see `.env.example`):
```
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
PRIVATE_KEY=0x...
CORE_CONTRACT_ADDRESS=0x...
SCANNER_CONTRACT_ADDRESS=0x...
BATCH_CONTRACT_ADDRESS=0x...
```

ABIs are in `ai-engine/blockchain/abis/`.

---

## Frontend Integration Notes

**CORS:** The backend allows `localhost:5173` and `localhost:3000`. Update in `main.py` line ~298 if your frontend runs on a different port.

**API client:** The test dashboard uses a simple fetch wrapper in `dashboard/src/lib/api.ts`. Use whatever HTTP client you prefer.

**Heatmap rendering:** The test dashboard uses Leaflet with `leaflet.heat` plugin and CARTO dark tiles. Corridors have precomputed OSRM road waypoints in the `road_waypoints` field -- render these as polylines instead of making client-side OSRM calls.

**Batch trace map:** The test dashboard has a working implementation at `dashboard/src/app/batch-trace/` showing the supply chain path on a map with a timeline sidebar. Use as reference.

---

## Data Files

The backend generates three large data files on first run. These are **not** in the git repo (gitignored). You must regenerate them:

```bash
cd ai-engine
python -m data.synthetic.generate_supply_chain_data   # -> data/synthetic/supply_chain_transactions.csv (9MB, 31K rows)
python -m data.synthetic.generate_scan_events          # -> data/synthetic/scan_events.csv (7MB, 50K rows)
python -m data.synthetic.generate_heatmap_seed         # -> data/synthetic/heatmap_seed.json (6MB, precomputed clusters + corridors)
```

The generators use `seed=42` for reproducibility. Running them produces identical output every time.

Reference data files (committed to git):
- `data/synthetic/indian_pharma_hubs.json` -- 35 manufacturing hubs, distribution centers, known hotspots with real WGS84 coordinates
- `data/synthetic/route_templates.json` -- Supply chain route templates

---

## Architecture Diagram

```
                    Blockchain (Ethereum)
                         |
                    Event Listener (polls every 2s)
                         |
                         v
    +--------------------------------------------+
    |           FastAPI Backend (:8000)            |
    |                                              |
    |  AnomalyDetector  HeatmapEngine  RiskScorer  |
    |  PillVerifier     AdverseMonitor BatchTrace  |
    |                                              |
    |  trust_score < 50 --> flagDrug() on-chain    |
    +--------------------------------------------+
                         |
                    REST API + WebSocket
                         |
                         v
                   Frontend / Mobile App
```

---

## File Structure

```
ai-engine/
  main.py                          # FastAPI app, startup, CORS, route registration
  config.py                        # Environment config, paths
  api/
    verify_routes.py               # Pill image verification
    anomaly_routes.py              # Anomaly detection (single + batch)
    heatmap_routes.py              # Heatmap data, zone risk, stats
    batch_trace_routes.py          # Batch backtracking, common origin
    risk_routes.py                 # Risk scoring, dashboard stats, WebSocket
    adverse_event_routes.py        # FDA FAERS adverse events
  models/
    pill_verifier.py               # EfficientNet-B0 CNN
    anomaly_detector.py            # IsolationForest + Autoencoder ensemble
    heatmap_engine.py              # DBSCAN, hotspot prediction, backtrace
    risk_scorer.py                 # Weighted ensemble scorer
    adverse_event_monitor.py       # OpenFDA API client
    train_anomaly_detector.py      # Training script (run once)
    train_pill_cnn.py              # Training script (run once)
  blockchain/
    bridge.py                      # Contract interaction (read/write)
    event_listener.py              # Chain event polling + simulation
    abis/                          # Contract ABIs
  data/
    synthetic/
      generate_supply_chain_data.py
      generate_scan_events.py
      generate_heatmap_seed.py
      indian_pharma_hubs.json      # Reference data (committed)
      indian_supply_chain_actors.py # Actor names + locations
      india_seasonal_patterns.py    # Temporal patterns
  utils/
    geo_utils.py                   # Coordinate encoding for Solidity
dashboard/                          # Test dashboard (Next.js 14 + Leaflet)
```
