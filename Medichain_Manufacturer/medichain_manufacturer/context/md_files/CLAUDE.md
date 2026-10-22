# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MediChain** — A blockchain + AI solution for counterfeit drug prevention in Indian pharmaceutical supply chains. Team YANIZA hackathon project. GitHub: https://github.com/Madglog/MediChain

## Architecture

Two subsystems connected in a pipeline:

1. **Ethereum Smart Contracts** — Solidity contracts (PharmaChainCore, PharmaChainScanner, PharmaChainBatch) deployed via Hardhat. Handles medicine registration, custody tracking, scan logging, and drug flagging.

2. **Python AI Backend** (`ai-engine/`) — FastAPI server (port 8000) orchestrating five AI/ML models:
   - **PillVerifier** — EfficientNet-B0 CNN for authentic/counterfeit pill image classification
   - **AnomalyDetector** — Isolation Forest + Autoencoder ensemble for supply chain anomaly detection (12 engineered features)
   - **AdverseEventMonitor** — OpenFDA FAERS API client for adverse event signal mining
   - **HeatmapEngine** — DBSCAN clustering (eps=0.05 ~5km) with time-decay weighting for geographic hotspot detection
   - **RiskScorer** — Weighted ensemble (image 30%, supply chain 25%, adverse events 20%, geographic 15%, external 10%) producing 0-100 trust scores

**Frontend**: Mobile app (not part of this repo). Connects to the FastAPI backend via REST + WebSocket `/ws/alerts`.

**Data flow**: Blockchain events → AI Backend (anomaly detection, risk scoring) → auto-flag on-chain if trust_score < 50 → Mobile app displays real-time alerts via WebSocket.

## Build & Run Commands

```bash
# Setup
cd ai-engine && pip install -r requirements.txt

# Download real data (NLM C3PI, RxImage, OpenFDA)
python -m data.download_real_data

# Generate synthetic training/demo data (fallback)
python -m data.synthetic.generate_supply_chain_data
python -m data.synthetic.generate_scan_events
python -m data.synthetic.generate_heatmap_seed

# Train models
python -m models.train_pill_cnn --demo_mode   # uses augmented data if no real dataset
python -m models.train_anomaly_detector

# Run backend
SIMULATION_MODE=true uvicorn main:app --reload --port 8000

# Run full demo simulation
python demo.py
```

## API Endpoints

All prefixed with `/api`:
- `GET /health` — Service health + model availability
- `POST /verify-image` — Pill image verification (multipart file upload)
- `POST /verify-hash` — Hash-only verification
- `POST /detect-anomaly` — Single transaction anomaly detection
- `POST /detect-anomaly-batch` — Batch anomaly detection (max 500)
- `GET /heatmap-data` — Geographic heatmap with DBSCAN clusters
- `GET /heatmap-zone-risk?lat=&lng=` — Zone risk assessment
- `GET /adverse-events/{drug_name}` — OpenFDA adverse event analysis
- `GET /drug-identity/{drug_name}` — Drug identity lookup
- `GET /drug-recalls/{drug_name}` — Drug recall check
- `POST /risk-score` — Full composite risk scoring
- `GET /risk-score/{medicine_id}` — Cached risk score lookup
- `GET /dashboard-stats` — Aggregate statistics
- `WS /ws/alerts` — Real-time alert WebSocket

## Smart Contract Interface

Contracts use int256 * 1e6 for lat/lng (e.g., 19283746 = 19.283746°). Key write operations from the AI layer:
- `core.flagDrug(id, severity)` — called when trust_score < 50
- `scanner.logScan(medicineId, lat, lng, location, deviceId)` — called after image verification

ABIs are in `ai-engine/blockchain/abis/`.

## Environment Variables

Required in `.env` at project root (see `.env.example`):
- `SEPOLIA_RPC_URL` / `LOCAL_RPC_URL` — Ethereum RPC endpoints
- `PRIVATE_KEY` — wallet key for write operations
- `CORE_CONTRACT_ADDRESS`, `SCANNER_CONTRACT_ADDRESS`, `BATCH_CONTRACT_ADDRESS`
- `AI_ENGINE_PORT`, `MODEL_DIR`, `PILL_MODEL_PATH`
- `OPENFDA_BASE_URL` (https://api.fda.gov)
- `SIMULATION_MODE=true` — enables synthetic event replay for demo

## Key Design Decisions

- **Real data first**: Synthetic data is a last resort. Tier 1 = government datasets (NLM C3PI, Pillbox, FDA FAERS), Tier 2 = scrapers, Tier 3 = self-collected, Tier 4 = synthetic.
- **India-focused**: DBSCAN eps tuned for Indian latitudes, CDSCO government alerts as data source, pharma hubs JSON with real WGS84 coordinates.
- **Trust score thresholds**: low 80-100 (no action), medium 50-79 (warning), high 20-49 (auto-flag), critical 0-19 (auto-flag + alert).
- **FlagSeverity enum**: Low(0), Medium(1), High(2), Critical(3) — matches smart contract.
- **Event listener**: Runs as asyncio background task in FastAPI startup, polls blockchain every 2s, buffers events for batch processing every 10s.
- **Graceful degradation**: All models are optional at startup. If a model fails to load, endpoints return 503 and the risk scorer uses neutral 0.5 scores for unavailable signals.
