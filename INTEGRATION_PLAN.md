# MediChain Full Integration Plan

## Context

Three independently-working subsystems need to be wired together:
- **AI Backend** (FastAPI, port 8000) — fully functional, correct API routes at `/api/*`
- **Smart Contracts** (Solidity on Sepolia) — deployed, correct ABIs, Flutter app uses them correctly
- **Next.js Dashboard** — has broken/placeholder integration code pointing to wrong endpoints, wrong ABIs, wrong network (Polygon Amoy instead of Sepolia)

The dashboard is the primary component that needs changes. The AI backend and smart contracts are production-ready and must NOT be modified.

---

## Architecture Overview

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Smart Contracts  │────▶│   AI Backend      │────▶│  Next.js Dashboard│
│  (Sepolia)        │     │  (FastAPI :8000)   │     │  (:3000)          │
│                   │     │                    │     │                   │
│  PharmaChainCore  │◀────│  BlockchainBridge  │     │  contract.ts      │
│  PharmaChainScan  │     │  EventListener     │────▶│  WS /ws/alerts    │
│  PharmaChainBatch │     │  RiskScorer        │     │  API proxy routes │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │                                                  │
        └──────────────────────────────────────────────────┘
                    Flutter Pharmacy App (Sepolia)
```

## Deployed Contract Addresses (Sepolia Testnet)

| Contract | Address |
|----------|---------|
| PharmaChainCore | `0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A` |
| PharmaChainScanner | `0x710a91E26754c126C3A1b8C0E0c5b06568d85493` |
| PharmaChainBatch | `0x555d8aFe7FD29eC64D84e930b1Bf0265D1cC68A8` |

---

## Integration Gaps Found

### 1. Dashboard `contract.ts` — WRONG ABIs
- **Current:** Uses `getDrug(string drugId)`, `getCustodyChain(string drugId)`, `scanCount(string)` — these functions don't exist
- **Actual:** Contracts use `medicines(uint256)`, `getCustodyHistory(uint256)`, `getScanCount(uint256)` with **uint256 IDs, not strings**
- **Current:** Single `NEXT_PUBLIC_CONTRACT_ADDRESS` — needs 3 separate addresses
- **Current:** Points to Polygon Amoy RPC — needs Sepolia

### 2. Dashboard API Proxy — WRONG Endpoints
- **Current:** POST proxies to `${ML_API_URL}/predict/risk` — doesn't exist
- **Actual:** AI backend serves `POST /api/risk-score`
- **Current:** GET proxies to `${ML_API_URL}/heatmap` and `${ML_API_URL}/analytics/summary` — don't exist
- **Actual:** AI backend serves `GET /api/heatmap-data` and `GET /api/dashboard-stats`

### 3. Heatmap Data Format Mismatch
- **Dashboard expects:** `{ regions: [{city, latitude, longitude, total_scans, counterfeit_count, risk_ratio}] }`
- **AI backend returns:** `{ heatmap_points, clusters, predicted_hotspots, corridors, state_risk, stats }`
- Needs a transformer in the proxy route

### 4. Block Explorer Links — WRONG Network
- 3 files link to `amoy.polygonscan.com` — should be `sepolia.etherscan.io`

### 5. No WebSocket Connection
- AI backend broadcasts real-time alerts via `WS /api/ws/alerts`
- Dashboard uses Supabase Realtime only — no connection to AI backend WebSocket

### 6. No Blockchain Verification Bridge
- `verify-hash/route.ts` only checks Supabase — doesn't call `core.verifyHash()` on-chain
- `register-drug/route.ts` only stores in Supabase — doesn't notify AI backend

---

## Changes (in execution order)

### 1. Update `.env.local.example` with correct config
**File:** `apps/dashboard/.env.local.example`
- Replace single `NEXT_PUBLIC_CONTRACT_ADDRESS` → 3 contract address env vars
- Replace Polygon Amoy RPC → `NEXT_PUBLIC_SEPOLIA_RPC`
- Pre-fill with deployed Sepolia addresses
- Add `NEXT_PUBLIC_AI_BACKEND_WS=ws://localhost:8000`

### 2. Rewrite `contract.ts` with correct ABIs and 3 contracts
**File:** `apps/dashboard/src/lib/contract.ts`

Replace wrong ABI with real ABIs matching Solidity:

**PharmaChainCore:**
```typescript
"function medicines(uint256) view returns (uint256 id, uint256 batchId, string ipfsHash, bytes32 contentHash, address currentOwner, address manufacturer, uint8 status, uint256 transferCount, uint256 scanCount, uint256 flagCount, bool isFlagged)"
"function isMedicineRegistered(uint256) view returns (bool)"
"function getCustodyHistory(uint256 _id) view returns (address[], uint256[])"
"function getActorRole(address _actor) view returns (uint8)"
"function verifyHash(uint256 _id, bytes32 _hash) view returns (bool)"
"function totalMedicines() view returns (uint256)"
"function flagDrug(uint256 _id, uint8 _severity)"
"function registerMedicine(uint256 _id, uint256 _batchId, string _ipfsHash, bytes32 _contentHash)"
"function transferCustody(uint256 _id, address _to)"
```

**PharmaChainScanner:**
```typescript
"function logScan(uint256, int256, int256, string, string)"
"function getScanHistory(uint256) view returns (tuple(address,int256,int256,uint256,string,string)[])"
"function getScanCount(uint256) view returns (uint256)"
"function getStats() view returns (uint256, uint256)"
```

**PharmaChainBatch:**
```typescript
"function getBatch(uint256) view returns (string, address, uint256, uint256, bool)"
"function getBatchMedicines(uint256) view returns (uint256[])"
```

Export: `getCoreContract()`, `getScannerContract()`, `getBatchContract()`, `getContract()` (backward-compat alias)

### 3. Fix AI backend API proxy routes
**File:** `apps/dashboard/src/app/api/risk-score/route.ts`
- POST: `${ML_API_URL}/predict/risk` → `${ML_API_URL}/api/risk-score`
- GET heatmap: `${ML_API_URL}/heatmap` → `${ML_API_URL}/api/heatmap-data`
- GET stats: `${ML_API_URL}/analytics/summary` → `${ML_API_URL}/api/dashboard-stats`
- Add `transformHeatmapData()` function to convert AI backend clusters → dashboard Region format
- Update fallback response to match real schema (`trust_score`, not `risk_score`)

### 4. Bridge hash verification to blockchain
**File:** `apps/dashboard/src/app/api/verify-hash/route.ts`
- After Supabase lookup, also POST to `${ML_API_URL}/api/verify-hash` for on-chain check
- Merge `blockchainMatch` into response
- try/catch fallback to Supabase-only

### 5. Notify AI backend on drug registration
**File:** `apps/dashboard/src/app/api/register-drug/route.ts`
- After Supabase insert, fire non-blocking POST to `${ML_API_URL}/api/risk-score` to prime AI
- `.catch(() => {})` so Supabase flow never breaks

### 6. Fix block explorer links (3 files)
- `apps/dashboard/src/app/dashboard/drugs/[drugId]/page.tsx`
- `apps/dashboard/src/app/dashboard/register/page.tsx`
- `apps/dashboard/src/components/SupplyChainTimeline.tsx`
- Change `amoy.polygonscan.com` → `sepolia.etherscan.io`

### 7. Create WebSocket alerts hook
**New file:** `apps/dashboard/src/hooks/useWebSocketAlerts.ts`
- Connect to `ws://localhost:8000/api/ws/alerts`
- Auto-reconnect (5s backoff), heartbeat (30s)
- Returns `{ alerts, connected }`

### 8. Integrate WebSocket alerts into Alerts page
**File:** `apps/dashboard/src/app/dashboard/alerts/page.tsx`
- Import `useWebSocketAlerts` alongside Supabase alerts
- Show real-time blockchain events in the alert feed
- Connection status indicator

### 9. Augment dashboard stats with AI backend
**File:** `apps/dashboard/src/hooks/useDrugStats.ts`
- After Supabase fetch, also call `/api/risk-score?type=stats`
- Merge `active_hotspots` → `highRiskZones`, `total_flags` → `activeFlags`
- try/catch fallback

---

## Files Modified Summary

| # | File | Action |
|---|------|--------|
| 1 | `apps/dashboard/.env.local.example` | Edit |
| 2 | `apps/dashboard/src/lib/contract.ts` | Rewrite |
| 3 | `apps/dashboard/src/app/api/risk-score/route.ts` | Edit |
| 4 | `apps/dashboard/src/app/api/verify-hash/route.ts` | Edit |
| 5 | `apps/dashboard/src/app/api/register-drug/route.ts` | Edit |
| 6 | `apps/dashboard/src/app/dashboard/drugs/[drugId]/page.tsx` | Edit (1 line) |
| 7 | `apps/dashboard/src/app/dashboard/register/page.tsx` | Edit (1 line) |
| 8 | `apps/dashboard/src/components/SupplyChainTimeline.tsx` | Edit (1 line) |
| 9 | `apps/dashboard/src/hooks/useWebSocketAlerts.ts` | New file |
| 10 | `apps/dashboard/src/hooks/useDrugStats.ts` | Edit |
| 11 | `apps/dashboard/src/app/dashboard/alerts/page.tsx` | Edit |

## Files NOT Modified
- AI backend (`MediChain/ai-engine/`) — no changes needed
- Smart contracts (`pharmachain-contracts/`) — deployed, no changes
- Flutter apps (`medichain_pharmacy/`, `Medichain_Manufacturer/`, `Medichain_Distributor/`, `Flutter_MediChain_Customer/`) — already correctly integrated

## Safety

Every integration change is wrapped in try/catch with graceful fallback:
- If AI backend is down → mock data or Supabase-only results
- If blockchain is unreachable → dashboard still works with Supabase
- `isMockMode()` path is never touched — demo mode always works
- `getContract()` backward-compat alias preserved

## Verification

After implementation:
1. `cd apps/dashboard && npm run dev` — dashboard starts on port 3000
2. `cd MediChain/ai-engine && SIMULATION_MODE=true uvicorn main:app --port 8000` — AI backend with simulated events
3. Dashboard at localhost:3000 should show:
   - Heatmap data from AI backend (or mock fallback)
   - Real-time WebSocket alerts (if AI backend running)
   - Risk scores proxied correctly to `/api/risk-score`
   - Block explorer links to `sepolia.etherscan.io`
4. Without Supabase, mock mode displays all 25 drugs, alerts, and heatmap regions unchanged

## AI Backend API Reference (for implementor)

All endpoints prefixed with `/api`:
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + model status |
| POST | `/risk-score` | Composite risk scoring |
| GET | `/risk-score/{medicine_id}` | Cached risk score |
| GET | `/dashboard-stats` | Aggregate statistics |
| GET | `/heatmap-data` | Full heatmap with clusters |
| GET | `/heatmap-zone-risk?lat=&lng=` | Zone risk assessment |
| POST | `/verify-image` | Pill image verification |
| POST | `/verify-hash` | Hash verification |
| POST | `/detect-anomaly` | Anomaly detection |
| GET | `/adverse-events/{drug_name}` | Adverse event analysis |
| GET | `/drug-recalls/{drug_name}` | Recall check |
| GET | `/batch-trace/batches` | Flagged batches |
| GET | `/batch-trace/{batch_id}` | Batch trace |
| WS | `/ws/alerts` | Real-time alerts |
