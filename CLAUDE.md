# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PharmaChain AI Systems** — A blockchain + AI solution for counterfeit drug prevention in Indian pharmaceutical supply chains. Team YANIZA hackathon project.

**Current state**: Planning phase. Two detailed design documents exist but no code has been written yet. The implementation plan (`PHARMACHAIN_AI_IMPLEMENTATION_PLAN (1).md`) is the primary reference — it contains pseudo-code, API contracts, and module specifications. The data strategy (`PHARMACHAIN_DATA_STRATEGY.md`) defines a tiered real-data-first acquisition pipeline.

## Architecture

Three subsystems connected in a pipeline:

1. **Ethereum Smart Contracts** (`pharmachain-contracts/`) — Pre-existing Solidity contracts (PharmaChainCore, PharmaChainScanner, PharmaChainBatch) deployed via Hardhat. Handles medicine registration, custody tracking, scan logging, and drug flagging.

2. **Python AI Backend** (`ai-engine/`) — FastAPI server (port 8000) orchestrating five AI/ML models:
   - **PillVerifier** — EfficientNet-B0 CNN for authentic/counterfeit pill image classification
   - **AnomalyDetector** — Isolation Forest + Autoencoder ensemble for supply chain anomaly detection (12 engineered features)
   - **AdverseEventMonitor** — OpenFDA FAERS API client for adverse event signal mining
   - **HeatmapEngine** — DBSCAN clustering (eps=0.05 ~5km) with time-decay weighting for geographic hotspot detection
   - **RiskScorer** — Weighted ensemble (image 30%, supply chain 25%, adverse events 20%, geographic 15%, external 10%) producing 0-100 trust scores

3. **React Dashboard** (`dashboard/`) — Vite + React + TailwindCSS frontend with Leaflet heatmaps, Recharts visualizations, ethers.js blockchain integration, and WebSocket real-time alerts.

**Data flow**: Blockchain events → AI Backend (anomaly detection, risk scoring) → auto-flag on-chain if trust_score < 50 → Dashboard displays real-time alerts via WebSocket `/ws/alerts`.

## Build & Run Commands

```bash
# Setup - create directory structure and install dependencies
cd ai-engine && pip install -r requirements.txt
cd ../dashboard && npm install

# Generate synthetic training/demo data
cd ai-engine
python -m data.synthetic.generate_supply_chain_data
python -m data.synthetic.generate_scan_events
python -m data.synthetic.generate_heatmap_seed

# Train models
python -m models.train_pill_cnn --demo_mode   # uses augmented data if no real dataset
python -m models.train_anomaly_detector

# Run backend
cd ai-engine && uvicorn main:app --reload --port 8000

# Run frontend (separate terminal)
cd dashboard && npm run dev

# Run full demo simulation
python demo.py
```

## Build Order

Modules must be built in this sequence due to dependencies:

1. Directory structure + dependency installation
2. Synthetic data generator (`ai-engine/data/synthetic/`) — all other modules need this
3. Blockchain bridge (`ai-engine/blockchain/`) — needed for integration
4. Pill CNN (`ai-engine/models/pill_verifier.py`)
5. Anomaly detector (`ai-engine/models/anomaly_detector.py`) — trains on synthetic data
6. Adverse event monitor (`ai-engine/models/adverse_event_monitor.py`) — API-only, no training
7. Heatmap engine (`ai-engine/models/heatmap_engine.py`)
8. Risk scorer (`ai-engine/models/risk_scorer.py`) — combines modules 4-7
9. FastAPI backend (`ai-engine/main.py` + `ai-engine/api/`) — wires up all routes
10. React dashboard (`dashboard/`)
11. Demo script + testing

Each module should work independently with mock data first, then be integrated.

## Smart Contract Interface

Contracts use int256 * 1e6 for lat/lng (e.g., 19283746 = 19.283746°). Key write operations from the AI layer:
- `core.flagDrug(id, severity)` — called when trust_score < 50
- `scanner.logScan(medicineId, lat, lng, location, deviceId)` — called after image verification

ABIs must be generated via `npx hardhat compile` in `pharmachain-contracts/` and copied from `artifacts/contracts/`.

## Environment Variables

Required in `.env` at project root:
- `SEPOLIA_RPC_URL` / `LOCAL_RPC_URL` — Ethereum RPC endpoints
- `PRIVATE_KEY` — wallet key for write operations
- `CORE_CONTRACT_ADDRESS`, `SCANNER_CONTRACT_ADDRESS`, `BATCH_CONTRACT_ADDRESS`
- `AI_ENGINE_PORT`, `MODEL_DIR`, `PILL_MODEL_PATH`
- `OPENFDA_BASE_URL` (https://api.fda.gov)
- `VITE_API_URL` (http://localhost:8000), `VITE_RPC_URL`
- `SIMULATION_MODE=true` — enables synthetic event replay for demo

## Key Design Decisions

- **Real data first**: Synthetic data is a last resort. Tier 1 = government datasets (NLM C3PI, Pillbox, FDA FAERS), Tier 2 = scrapers, Tier 3 = self-collected, Tier 4 = synthetic.
- **India-focused**: DBSCAN eps tuned for Indian latitudes, CDSCO government alerts as data source, India-centered Leaflet map [20.5937, 78.9629].
- **Trust score thresholds**: low 80-100 (no action), medium 50-79 (warning), high 20-49 (auto-flag), critical 0-19 (auto-flag + alert).
- **CORS**: Backend allows localhost:5173 (Vite) and localhost:3000.
- **Event listener**: Runs as asyncio background task in FastAPI startup, polls blockchain every 2 seconds, buffers events for batch processing every 10 seconds.
