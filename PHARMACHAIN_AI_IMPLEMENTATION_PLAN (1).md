# PharmaChain AI Systems — Complete Implementation Plan

> **Purpose**: This document is a comprehensive, step-by-step implementation plan for building the AI layer of the PharmaChain hackathon project. Hand this entire document to Claude Code and it should be able to execute each module sequentially.
>
> **Team**: YANIZA
> **Problem Statement**: Blockchain and AI System for Counterfeit Drug Prevention
> **What exists already**: Smart contracts (PharmaChainCore, PharmaChainScanner, PharmaChainBatch) deployed on Ethereum/Sepolia — see `/pharmachain-contracts/` directory

---

## TABLE OF CONTENTS

1. [Project Architecture Overview](#1-project-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Global Dependencies & Environment Setup](#3-global-dependencies--environment-setup)
4. [MODULE 1: Synthetic Data Generator](#4-module-1-synthetic-data-generator)
5. [MODULE 2: Pill Image Verification (CNN)](#5-module-2-pill-image-verification-cnn)
6. [MODULE 3: Supply Chain Anomaly Detection](#6-module-3-supply-chain-anomaly-detection)
7. [MODULE 4: Adverse Event Signal Mining (NLP/API)](#7-module-4-adverse-event-signal-mining-nlpapi)
8. [MODULE 5: Counterfeit Hotspot Heatmap](#8-module-5-counterfeit-hotspot-heatmap)
9. [MODULE 6: Composite Risk Scoring Engine](#9-module-6-composite-risk-scoring-engine)
10. [MODULE 7: FastAPI Backend (AI Orchestrator)](#10-module-7-fastapi-backend-ai-orchestrator)
11. [MODULE 8: Blockchain Bridge (Web3 Integration)](#11-module-8-blockchain-bridge-web3-integration)
12. [MODULE 9: React Dashboard Frontend](#12-module-9-react-dashboard-frontend)
13. [Testing & Demo Script](#13-testing--demo-script)
14. [Datasets to Download](#14-datasets-to-download)

---

## 1. Project Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        REACT DASHBOARD                              │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────────────┐   │
│  │ Pill Scan│ │ Supply Chain │ │ Heatmap  │ │  Risk Score     │   │
│  │ Upload   │ │ Monitor      │ │ (Leaflet)│ │  Dashboard      │   │
│  └────┬─────┘ └──────┬───────┘ └────┬─────┘ └───────┬─────────┘   │
└───────┼──────────────┼──────────────┼───────────────┼──────────────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (AI Orchestrator)                │
│                     Port: 8000                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ /api/verify  │ │ /api/anomaly │ │ /api/heatmap│ │ /api/risk  │ │
│  │  -image      │ │  -detect     │ │  -data      │ │  -score    │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬──────┘ └─────┬──────┘ │
│         │                │                │               │        │
│  ┌──────▼───────┐ ┌──────▼───────┐ ┌──────▼──────┐ ┌─────▼──────┐ │
│  │ CNN Model    │ │ Isolation    │ │ DBSCAN      │ │ Ensemble   │ │
│  │ EfficientNet │ │ Forest +     │ │ Clustering  │ │ Weighted   │ │
│  │ (PyTorch)    │ │ Autoencoder  │ │ + Heatmap   │ │ Scoring    │ │
│  └──────────────┘ └──────────────┘ └─────────────┘ └────────────┘ │
│         │                │                │               │        │
│  ┌──────▼────────────────▼────────────────▼───────────────▼──────┐ │
│  │              BLOCKCHAIN BRIDGE (Web3.py)                       │ │
│  │  • Listen to DrugScanned, DrugFlagged, VelocityAlert events   │ │
│  │  • Call flagDrug() when AI detects anomaly                    │ │
│  │  • Read scan history, custody history                         │ │
│  └───────────────────────────────────────────────────────────────┘ │
│         │                │                                         │
│  ┌──────▼────────────────▼───────────────────────────────────────┐ │
│  │              OPENFDA API CLIENT                                │ │
│  │  • Adverse event queries                                      │ │
│  │  • Drug shortage monitoring                                   │ │
│  │  • Recall cross-referencing                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│               ETHEREUM BLOCKCHAIN (Sepolia / Local Hardhat)         │
│  ┌──────────────────┐ ┌─────────────────┐ ┌─────────────────────┐  │
│  │ PharmaChainCore  │ │ PharmaChainScan │ │ PharmaChainBatch    │  │
│  │ (Medicine CRUD,  │ │ (Scan logging,  │ │ (Batch mgmt,        │  │
│  │  Custody, Flags) │ │  Velocity alerts│ │  Bulk registration) │  │
│  └──────────────────┘ └─────────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

Create this exact structure:

```
pharmachain/
├── pharmachain-contracts/          # ALREADY EXISTS — do not modify
│   ├── PharmaChainCore.sol
│   ├── PharmaChainScanner.sol
│   ├── PharmaChainBatch.sol
│   ├── scripts/deploy.js
│   ├── hardhat.config.js
│   └── package.json
│
├── ai-engine/                      # NEW — Python AI backend
│   ├── requirements.txt
│   ├── config.py                   # Shared configuration
│   ├── main.py                     # FastAPI app entry point
│   │
│   ├── data/                       # Datasets & synthetic data
│   │   ├── synthetic/
│   │   │   ├── generate_supply_chain_data.py
│   │   │   ├── generate_scan_events.py
│   │   │   ├── generate_heatmap_seed.py
│   │   │   └── indian_pharma_hubs.json
│   │   ├── pill_images/            # Downloaded datasets go here
│   │   └── models/                 # Saved model weights
│   │       ├── pill_cnn.pth
│   │       ├── anomaly_iforest.pkl
│   │       └── anomaly_autoencoder.pth
│   │
│   ├── models/                     # AI model definitions
│   │   ├── __init__.py
│   │   ├── pill_verifier.py        # CNN pill image verification
│   │   ├── anomaly_detector.py     # Isolation Forest + Autoencoder
│   │   ├── adverse_event_monitor.py # OpenFDA API + NLP
│   │   ├── heatmap_engine.py       # DBSCAN clustering + heatmap data
│   │   └── risk_scorer.py          # Composite risk scoring
│   │
│   ├── blockchain/                 # Web3 integration
│   │   ├── __init__.py
│   │   ├── bridge.py               # Web3.py contract interaction
│   │   ├── event_listener.py       # Listen to on-chain events
│   │   └── abis/                   # Contract ABIs (from Hardhat compile)
│   │       ├── PharmaChainCore.json
│   │       ├── PharmaChainScanner.json
│   │       └── PharmaChainBatch.json
│   │
│   ├── api/                        # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── verify_routes.py        # Pill verification endpoints
│   │   ├── anomaly_routes.py       # Anomaly detection endpoints
│   │   ├── heatmap_routes.py       # Heatmap data endpoints
│   │   ├── risk_routes.py          # Risk scoring endpoints
│   │   └── adverse_event_routes.py # Adverse event endpoints
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_processing.py     # Image preprocessing utilities
│       └── geo_utils.py            # Geographic calculations
│
├── dashboard/                      # NEW — React frontend
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── PillScanner.jsx     # Camera/upload pill image
│   │   │   ├── SupplyChainGraph.jsx # D3/Recharts supply chain viz
│   │   │   ├── HeatmapView.jsx     # Leaflet heatmap
│   │   │   ├── RiskDashboard.jsx   # Risk scores + alerts
│   │   │   ├── DrugTimeline.jsx    # Custody history timeline
│   │   │   └── AlertsFeed.jsx      # Real-time alert stream
│   │   ├── hooks/
│   │   │   ├── useBlockchain.js    # Web3 hooks
│   │   │   └── useAIEngine.js      # API hooks
│   │   └── utils/
│   │       └── api.js              # Axios client
│   └── public/
│
└── README.md                       # Project overview
```

---

## 3. Global Dependencies & Environment Setup

### Python (ai-engine/requirements.txt)

```txt
# Core
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.0

# AI/ML
torch==2.1.0
torchvision==0.16.0
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.4
Pillow==10.1.0
scipy==1.11.4

# Blockchain
web3==6.13.0

# HTTP & Data
httpx==0.25.2
aiohttp==3.9.1
python-dotenv==1.0.0

# Visualization/Geo
folium==0.15.1
geopy==2.4.1

# CORS
fastapi-cors==0.0.6
```

### Node.js (dashboard/package.json key dependencies)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "leaflet.heat": "^0.2.0",
    "recharts": "^2.10.3",
    "axios": "^1.6.2",
    "ethers": "^6.9.0",
    "lucide-react": "^0.294.0",
    "tailwindcss": "^3.3.6"
  }
}
```

### Environment File (.env in project root)

```bash
# Blockchain
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
LOCAL_RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=your_wallet_private_key
CORE_CONTRACT_ADDRESS=0x...
SCANNER_CONTRACT_ADDRESS=0x...
BATCH_CONTRACT_ADDRESS=0x...

# AI Engine
AI_ENGINE_PORT=8000
MODEL_DIR=./ai-engine/data/models
PILL_MODEL_PATH=./ai-engine/data/models/pill_cnn.pth

# OpenFDA
OPENFDA_BASE_URL=https://api.fda.gov

# Frontend
VITE_API_URL=http://localhost:8000
VITE_RPC_URL=http://127.0.0.1:8545
```

---

## 4. MODULE 1: Synthetic Data Generator

> **Priority**: BUILD FIRST — all other modules depend on this data
> **Time estimate**: 2–3 hours
> **Location**: `ai-engine/data/synthetic/`

### 4.1 Indian Pharma Hubs Reference Data

Create `ai-engine/data/synthetic/indian_pharma_hubs.json`:

```json
{
  "legitimate_hubs": [
    {"name": "Hyderabad Pharma City", "lat": 17.3850, "lng": 78.4867, "type": "manufacturer", "density": "high"},
    {"name": "Ahmedabad GIDC", "lat": 23.0225, "lng": 72.5714, "type": "manufacturer", "density": "high"},
    {"name": "Mumbai Parel", "lat": 19.0760, "lng": 72.8777, "type": "manufacturer", "density": "high"},
    {"name": "Baddi Himachal", "lat": 30.9578, "lng": 76.7914, "type": "manufacturer", "density": "high"},
    {"name": "Sikkim Pharma Zone", "lat": 27.3389, "lng": 88.6065, "type": "manufacturer", "density": "medium"},
    {"name": "Goa Pharma Hub", "lat": 15.4909, "lng": 73.8278, "type": "manufacturer", "density": "medium"},
    {"name": "Vizag SEZ", "lat": 17.6868, "lng": 83.2185, "type": "manufacturer", "density": "medium"},
    {"name": "Chennai Guindy", "lat": 13.0067, "lng": 80.2206, "type": "distributor", "density": "high"},
    {"name": "Delhi Bhagirath Palace", "lat": 28.6562, "lng": 77.2321, "type": "distributor", "density": "high"},
    {"name": "Kolkata Burrabazar", "lat": 22.5726, "lng": 88.3639, "type": "distributor", "density": "high"},
    {"name": "Bangalore Chickpet", "lat": 12.9716, "lng": 77.5946, "type": "distributor", "density": "medium"},
    {"name": "Pune Camp", "lat": 18.5204, "lng": 73.8567, "type": "distributor", "density": "medium"}
  ],
  "known_problem_zones": [
    {"name": "Badi Indore", "lat": 22.7196, "lng": 75.8577, "risk": "critical", "reason": "Known spurious drug manufacturing hub"},
    {"name": "Kashmere Gate Delhi", "lat": 28.6669, "lng": 77.2278, "risk": "high", "reason": "Unregulated wholesale market"},
    {"name": "Kalbadevi Mumbai", "lat": 18.9548, "lng": 72.8304, "risk": "high", "reason": "Large unregulated wholesale market"},
    {"name": "Agra UP", "lat": 27.1767, "lng": 78.0081, "risk": "high", "reason": "CDSCO flagged multiple units"},
    {"name": "Aligarh UP", "lat": 27.8974, "lng": 78.0880, "risk": "high", "reason": "Agra-Aligarh counterfeit corridor"},
    {"name": "Raxaul Bihar", "lat": 26.9789, "lng": 84.8510, "risk": "medium", "reason": "India-Nepal border entry point"},
    {"name": "Petrapole WB", "lat": 23.1791, "lng": 88.9990, "risk": "medium", "reason": "India-Bangladesh border entry"},
    {"name": "Moreh Manipur", "lat": 24.2533, "lng": 94.2983, "risk": "medium", "reason": "India-Myanmar border entry"},
    {"name": "Lucknow UP", "lat": 26.8467, "lng": 80.9462, "risk": "medium", "reason": "High NSQ detection volume"},
    {"name": "Patna Bihar", "lat": 25.6093, "lng": 85.1376, "risk": "medium", "reason": "Frequent CDSCO alerts"}
  ],
  "pharmacy_cities": [
    {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777, "population_weight": 10},
    {"name": "Delhi", "lat": 28.7041, "lng": 77.1025, "population_weight": 10},
    {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946, "population_weight": 8},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707, "population_weight": 8},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639, "population_weight": 8},
    {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867, "population_weight": 7},
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567, "population_weight": 6},
    {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "population_weight": 6},
    {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873, "population_weight": 5},
    {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462, "population_weight": 5},
    {"name": "Bhopal", "lat": 23.2599, "lng": 77.4126, "population_weight": 4},
    {"name": "Indore", "lat": 22.7196, "lng": 75.8577, "population_weight": 4},
    {"name": "Nagpur", "lat": 21.1458, "lng": 79.0882, "population_weight": 4},
    {"name": "Coimbatore", "lat": 11.0168, "lng": 76.9558, "population_weight": 3},
    {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739, "population_weight": 3}
  ]
}
```

### 4.2 Supply Chain Event Generator

Create `ai-engine/data/synthetic/generate_supply_chain_data.py`:

**Purpose**: Generate realistic supply chain transaction data that mimics what the smart contracts would emit. This feeds the anomaly detection model.

**Requirements**:
- Generate 10,000 normal transactions and 500 anomalous ones
- Each transaction has: `medicine_id`, `batch_id`, `from_address`, `to_address`, `from_role`, `to_role`, `from_location` (lat/lng), `to_location` (lat/lng), `timestamp`, `transfer_number`, `time_since_last_transfer` (seconds)
- Normal transactions follow these patterns:
  - Manufacturer → Distributor: 1–7 days
  - Distributor → Pharmacy: 1–5 days
  - Pharmacy → Consumer: same day to 30 days
  - Geographic movement is realistic (from manufacturing hubs to distribution cities to pharmacy cities)
  - One medicine follows a single linear path
- Anomalous transactions (label `is_anomaly=1`) should include these types:
  - **Velocity anomaly**: Transfer happens impossibly fast (e.g., Mumbai to Delhi in 10 minutes)
  - **Path deviation**: Medicine skips a step (Manufacturer directly to Consumer)
  - **Duplicate scan**: Same medicine scanned by 2+ pharmacies simultaneously
  - **Reverse flow**: Medicine goes backward (Pharmacy → Distributor)
  - **Geographic impossibility**: Location jumps > 1000km in < 1 hour
  - **Excessive transfers**: More than 5 transfers for a single medicine
  - **Time anomaly**: Transfers happening at unusual hours (2–5 AM consistently)

**Output**: Save as `ai-engine/data/synthetic/supply_chain_transactions.csv` with columns:
```
medicine_id, batch_id, from_role, to_role, from_lat, from_lng, to_lat, to_lng, 
timestamp, transfer_number, time_since_last_transfer_hours, distance_km, 
speed_kmh, hour_of_day, is_weekend, path_sequence, is_anomaly, anomaly_type
```

### 4.3 Scan Event Generator

Create `ai-engine/data/synthetic/generate_scan_events.py`:

**Purpose**: Generate scan events that match the `PharmaChainScanner.logScan()` event format. Feeds the heatmap and time-series analysis.

**Requirements**:
- Generate 50,000 scan events over a 90-day period
- Each event: `medicine_id`, `scanner_address`, `latitude`, `longitude`, `timestamp`, `location_name`, `device_id`, `is_flagged`, `flag_severity`
- 90% of scans come from legitimate pharma hubs and pharmacy cities
- 7% of scans come from known problem zones (higher flag rate)
- 3% are truly anomalous (velocity violations, duplicate scans, unknown locations)
- Generate some "hotspot emergence" patterns: a problem zone that starts with 1–2 flags in week 1 and escalates to 10+ by week 4

**Output**: Save as `ai-engine/data/synthetic/scan_events.csv`

### 4.4 Heatmap Seed Data

Create `ai-engine/data/synthetic/generate_heatmap_seed.py`:

**Purpose**: Pre-compute heatmap data from scan events with proper intensity weighting.

**Requirements**:
- Read scan_events.csv
- For each event, compute intensity:
  - Normal scan: intensity = 0.1
  - Flagged (Low): intensity = 0.3
  - Flagged (Medium): intensity = 0.5
  - Flagged (High): intensity = 0.8
  - Velocity alert: intensity = 1.0
- Apply time decay: recent events weighted higher (exponential decay, half-life = 7 days)
- Output: JSON array of `[lat, lng, intensity]` tuples + DBSCAN cluster centers

**Output**: Save as `ai-engine/data/synthetic/heatmap_data.json`

---

## 5. MODULE 2: Pill Image Verification (CNN)

> **Priority**: HIGH — most impressive for demo
> **Time estimate**: 4–6 hours
> **Location**: `ai-engine/models/pill_verifier.py`

### 5.1 Dataset Setup

Download one of these (in order of preference):

1. **ePillID benchmark** — Clone from `https://github.com/usuyama/ePillID-benchmark`
   - Contains ~13,000 images, 9,804 appearance classes
   - Already has metric learning framework
   
2. **Roboflow Counterfeit Detection** — Download from `https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection`
   - 1,555 YOLO-annotated images
   - Export in "folder" format for PyTorch ImageFolder

3. **If neither downloadable in time**, use the Kaggle Pharmaceutical Tablets Dataset:
   - `https://www.kaggle.com/datasets/trumedicines/pharmaceutical-tablets-dataset`
   - 252 → 20,000 augmented images

Place downloaded data in `ai-engine/data/pill_images/`

### 5.2 Model Architecture

```python
# ai-engine/models/pill_verifier.py

"""
Pill Image Verification Module
Uses pretrained EfficientNet-B0 for feature extraction + cosine similarity matching.

Two modes:
1. CLASSIFICATION: Is this pill authentic or counterfeit? (binary)
2. EMBEDDING: Extract a feature vector, compare against registered drug embedding 
   stored on IPFS (referenced by contentHash in smart contract)

For hackathon: Use mode 1 with transfer learning.
"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import numpy as np
from pathlib import Path

class PillVerifier:
    """
    CNN-based pill verification model.
    
    Architecture: EfficientNet-B0 (pretrained on ImageNet)
    - Freeze all layers except last 2 blocks + classifier
    - Replace classifier head: 1280 → 512 → 128 → 2 (authentic/counterfeit)
    - Also expose 128-dim embedding for similarity matching
    
    Input: RGB image (224x224)
    Output: 
      - confidence: float 0-1 (probability of authentic)
      - embedding: 128-dim vector for on-chain hash comparison
      - prediction: "authentic" | "suspicious" | "counterfeit"
    
    Thresholds:
      - confidence >= 0.85 → "authentic"
      - 0.50 <= confidence < 0.85 → "suspicious" 
      - confidence < 0.50 → "counterfeit"
    """
    
    def __init__(self, model_path=None, num_classes=2, device=None):
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.num_classes = num_classes
        self.transform = self._get_transforms()
        self.model = self._build_model()
        if model_path and Path(model_path).exists():
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
    
    def _get_transforms(self):
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def _build_model(self):
        """EfficientNet-B0 with custom head for pill verification."""
        base = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        
        # Freeze early layers
        for param in list(base.parameters())[:-20]:
            param.requires_grad = False
        
        # Custom classification head
        in_features = base.classifier[1].in_features  # 1280
        base.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(512, 128),  # embedding layer
            nn.ReLU(),
            nn.Linear(128, self.num_classes)
        )
        return base.to(self.device)
    
    def get_embedding(self, image: Image.Image) -> np.ndarray:
        """Extract 128-dim embedding for similarity comparison."""
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        # Hook into the 128-dim layer
        embedding = None
        def hook_fn(module, input, output):
            nonlocal embedding
            embedding = output.detach().cpu().numpy()
        
        handle = self.model.classifier[4].register_forward_hook(hook_fn)  # 128-dim layer
        with torch.no_grad():
            self.model(tensor)
        handle.remove()
        return embedding[0]
    
    def verify(self, image: Image.Image) -> dict:
        """
        Verify a pill image.
        Returns: {confidence, prediction, embedding_hash, embedding}
        """
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence = probabilities[0][1].item()  # prob of class "authentic"
        
        embedding = self.get_embedding(image)
        embedding_hash = self._hash_embedding(embedding)
        
        if confidence >= 0.85:
            prediction = "authentic"
        elif confidence >= 0.50:
            prediction = "suspicious"
        else:
            prediction = "counterfeit"
        
        return {
            "confidence": round(confidence, 4),
            "prediction": prediction,
            "embedding_hash": embedding_hash,
            "embedding": embedding.tolist()
        }
    
    def _hash_embedding(self, embedding: np.ndarray) -> str:
        """Hash embedding to bytes32 for on-chain comparison with contentHash."""
        import hashlib
        return "0x" + hashlib.sha256(embedding.tobytes()).hexdigest()
    
    def compare_embeddings(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Cosine similarity between two pill embeddings."""
        from numpy.linalg import norm
        return float(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2)))
```

### 5.3 Training Script

Create `ai-engine/models/train_pill_cnn.py`:

```python
"""
Training script for PillVerifier.

Usage: python -m models.train_pill_cnn --data_dir data/pill_images --epochs 15 --batch_size 32

Expected directory structure:
  data/pill_images/
    train/
      authentic/   ← images of genuine pills
      counterfeit/ ← images of counterfeit/defective pills
    val/
      authentic/
      counterfeit/

If using ePillID dataset:
  - Use all reference images as "authentic"
  - Apply heavy augmentation (color jitter, blur, noise) to create "counterfeit" class
  - This simulates what counterfeits might look like: slightly off colors, blurred prints

If dataset not available, create a DEMO MODE that:
  - Downloads 100 random pill images from NLM RxImage API
  - Splits 80/20 for train/val
  - Applies augmentation for counterfeit class (blur, color shift, add noise)
  - This won't be a real counterfeit detector but WILL demo the pipeline correctly
"""

# Standard PyTorch training loop:
# - Adam optimizer, lr=1e-4 with ReduceLROnPlateau
# - CrossEntropyLoss
# - Data augmentation: RandomHorizontalFlip, RandomRotation(30), ColorJitter, RandomAffine
# - Early stopping on val loss (patience=5)
# - Save best model to data/models/pill_cnn.pth
# - Log training metrics (loss, accuracy per epoch)
```

---

## 6. MODULE 3: Supply Chain Anomaly Detection

> **Priority**: HIGH — plugs directly into existing smart contract events
> **Time estimate**: 3–4 hours
> **Location**: `ai-engine/models/anomaly_detector.py`

### 6.1 Feature Engineering

The model takes raw supply chain transaction data and engineers these features:

| Feature | Description | Normal Range |
|---|---|---|
| `transfer_velocity_kmh` | Distance / time between transfers | 20–80 km/h (truck) |
| `time_since_last_transfer_hours` | Hours between consecutive transfers | 24–168 |
| `transfer_count` | Total transfers for this medicine | 2–4 |
| `scan_frequency_24h` | Scans in last 24h for this medicine | 1–3 |
| `unique_devices_24h` | Unique scanners in 24h | 1–2 |
| `path_deviation_score` | 0=correct sequence, 1=skipped step | 0 |
| `geographic_consistency` | Avg distance between consecutive scans (km) | 50–500 |
| `hour_of_day` | Hour when transfer occurred | 8–20 (business hours) |
| `is_weekend` | Boolean | mostly 0 |
| `days_since_manufacture` | Days from registration to current scan | 7–365 |
| `batch_anomaly_rate` | % of flagged medicines in same batch | 0–0.02 |
| `actor_reputation_score` | From smart contract | 400–1000 |

### 6.2 Model Implementation

```python
# ai-engine/models/anomaly_detector.py

"""
Supply Chain Anomaly Detection Module

Two models in ensemble:
1. Isolation Forest (fast, interpretable, good baseline)
2. Shallow Autoencoder (learns complex patterns, better at novel anomalies)

Combine predictions: flag as anomaly if EITHER model flags it.
This gives high recall (catches more counterfeits) at cost of some precision.
For pharma, high recall is more important — false positives just mean extra checks.

Training: Fit on NORMAL transactions only (unsupervised anomaly detection).
"""

import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn

FEATURE_COLUMNS = [
    'transfer_velocity_kmh',
    'time_since_last_transfer_hours',
    'transfer_count',
    'scan_frequency_24h',
    'unique_devices_24h',
    'path_deviation_score',
    'geographic_consistency',
    'hour_of_day',
    'is_weekend',
    'days_since_manufacture',
    'batch_anomaly_rate',
    'actor_reputation_score'
]

class SupplyChainAutoencoder(nn.Module):
    """
    Shallow autoencoder for anomaly detection.
    Architecture: 12 → 8 → 4 → 8 → 12
    High reconstruction error = anomaly.
    """
    def __init__(self, input_dim=12):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AnomalyDetector:
    """
    Ensemble anomaly detection for supply chain transactions.
    
    Usage:
        detector = AnomalyDetector()
        detector.train(normal_transactions_df)
        result = detector.detect(new_transaction_dict)
        # result = {
        #   "is_anomaly": True/False,
        #   "anomaly_score": 0.0–1.0,
        #   "iforest_score": float,
        #   "autoencoder_score": float,
        #   "anomaly_reasons": ["velocity_violation", "path_deviation"],
        #   "recommended_severity": "Low" | "Medium" | "High" | "Critical"
        # }
    
    Integration with smart contract:
        If is_anomaly and recommended_severity >= "High":
            Call core.flagDrug(medicineId, severity) on-chain
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(
            contamination=0.05,  # expect 5% anomalies
            n_estimators=200,
            max_samples='auto',
            random_state=42
        )
        self.autoencoder = SupplyChainAutoencoder(input_dim=len(FEATURE_COLUMNS))
        self.ae_threshold = None  # Set during training (95th percentile of normal reconstruction error)
        self.is_trained = False
    
    def train(self, df: pd.DataFrame):
        """Train on normal (non-anomalous) transactions only."""
        # Implementation: 
        # 1. Scale features with StandardScaler
        # 2. Fit IsolationForest on scaled data
        # 3. Train autoencoder (50 epochs, MSE loss, Adam lr=1e-3)
        # 4. Compute reconstruction error threshold (95th percentile on training data)
        # 5. Save both models
        pass
    
    def detect(self, transaction: dict) -> dict:
        """
        Detect anomaly in a single transaction.
        Also run rule-based checks for interpretable reasons.
        """
        # Implementation:
        # 1. Extract and scale features
        # 2. Get IsolationForest prediction (-1=anomaly, 1=normal)
        # 3. Get autoencoder reconstruction error
        # 4. Run rule-based checks for anomaly_reasons list:
        #    - transfer_velocity_kmh > 500 → "velocity_violation"
        #    - path_deviation_score > 0 → "path_deviation"
        #    - transfer_count > 5 → "excessive_transfers"
        #    - hour_of_day between 2-5 and is_weekend → "suspicious_timing"
        #    - batch_anomaly_rate > 0.1 → "batch_contamination"
        #    - actor_reputation_score < 300 → "low_reputation_actor"
        # 5. Combine scores: anomaly if EITHER model flags OR 2+ rule violations
        # 6. Map to severity based on anomaly score
        pass
    
    def detect_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies in a batch of transactions."""
        pass
    
    def save(self, model_dir: str):
        """Save both models and scaler."""
        pass
    
    def load(self, model_dir: str):
        """Load both models and scaler."""
        pass
```

### 6.3 Training Script

Create `ai-engine/models/train_anomaly_detector.py`:

```python
"""
Train the anomaly detection model on synthetic supply chain data.

Usage: python -m models.train_anomaly_detector

Steps:
1. Load supply_chain_transactions.csv
2. Filter to is_anomaly=0 rows only (train on normal data)
3. Train IsolationForest + Autoencoder
4. Evaluate on full dataset (including anomalies) — print precision/recall/F1
5. Save models to data/models/
"""
```

---

## 7. MODULE 4: Adverse Event Signal Mining (NLP/API)

> **Priority**: MEDIUM — impressive but OpenFDA API approach is fast
> **Time estimate**: 2–3 hours (API-first approach)
> **Location**: `ai-engine/models/adverse_event_monitor.py`

### 7.1 Implementation

```python
# ai-engine/models/adverse_event_monitor.py

"""
Adverse Event Signal Mining Module

TWO approaches (implement both, API-first):

Approach A — OpenFDA API (NO model training needed, implement first):
  Query FDA FAERS database for adverse events related to a specific drug.
  Look for counterfeit signals:
  - Spike in "drug ineffective" reactions
  - "product quality problem" reports
  - Unexpected ADR patterns for a known drug
  - Geographic clustering of adverse events
  
  Endpoint: https://api.fda.gov/drug/event.json
  
Approach B — NLP Classifier (if time permits):
  Fine-tune DistilBERT on FAERS narrative text to classify:
  - Class 0: Normal ADR report
  - Class 1: Suspected quality/counterfeiting issue
  - Class 2: Therapeutic failure (drug didn't work)
  
  For hackathon: Use keyword-based heuristic as fallback if no time for fine-tuning.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional

class AdverseEventMonitor:
    """
    Monitor FDA adverse event data for counterfeit drug signals.
    
    Usage:
        monitor = AdverseEventMonitor()
        
        # Check a specific drug
        result = monitor.analyze_drug("metformin")
        # result = {
        #   "drug_name": "metformin",
        #   "total_reports": 15234,
        #   "recent_reports_30d": 127,
        #   "quality_complaints": 8,
        #   "therapeutic_failures": 23,
        #   "counterfeit_risk_score": 0.35,  # 0-1
        #   "top_reactions": [{"reaction": "drug ineffective", "count": 23}, ...],
        #   "signal_alerts": [
        #       "Elevated therapeutic failure rate (3.2x baseline)",
        #       "3 product quality complaints in last 30 days"
        #   ]
        # }
    
    Counterfeit risk signals (weighted):
        - "product quality problem" reports: weight 5.0
        - "drug ineffective" above baseline: weight 3.0  
        - "therapeutic response unexpected": weight 2.0
        - Sudden spike in any ADR (>2 std dev from 6-month avg): weight 2.0
        - Geographic clustering of reports: weight 1.5
    """
    
    BASE_URL = "https://api.fda.gov/drug/event.json"
    
    COUNTERFEIT_SIGNAL_REACTIONS = [
        "PRODUCT QUALITY ISSUE",
        "DRUG INEFFECTIVE", 
        "THERAPEUTIC RESPONSE UNEXPECTED",
        "PRODUCT CONTAMINATION",
        "PRODUCT ADULTERATION",
        "WRONG TECHNIQUE IN DRUG USAGE PROCESS",
        "SUSPECTED COUNTERFEIT PRODUCT",
        "PRODUCT PACKAGING QUANTITY ERROR"
    ]
    
    async def analyze_drug(self, drug_name: str, days_back: int = 90) -> dict:
        """
        Query OpenFDA for adverse events and compute counterfeit risk signals.
        """
        # Implementation:
        # 1. Query total reports for this drug
        # 2. Query reports in last N days
        # 3. Count COUNTERFEIT_SIGNAL_REACTIONS specifically
        # 4. Compare recent rate vs historical baseline
        # 5. Compute counterfeit_risk_score as weighted sum of signals
        pass
    
    async def check_drug_shortage(self, drug_name: str) -> dict:
        """
        Check if drug is in shortage (shortages increase counterfeiting risk).
        Endpoint: https://api.fda.gov/drug/shortages.json (if available)
        Fallback: search enforcement actions
        """
        pass
    
    async def check_recalls(self, drug_name: str) -> list:
        """
        Check recent recalls for this drug.
        Endpoint: https://api.fda.gov/drug/enforcement.json
        """
        pass
    
    async def get_drug_identity(self, drug_name: str) -> dict:
        """
        Get ground truth drug identity from NDC Directory.
        Returns: manufacturer, active ingredients, dosage form, route, packaging.
        Endpoint: https://api.fda.gov/drug/ndc.json
        """
        pass
```

---

## 8. MODULE 5: Counterfeit Hotspot Heatmap

> **Priority**: HIGH — visually stunning for demo
> **Time estimate**: 3–4 hours
> **Location**: `ai-engine/models/heatmap_engine.py`

### 8.1 Backend Heatmap Engine

```python
# ai-engine/models/heatmap_engine.py

"""
Counterfeit Hotspot Heatmap Engine

Three layers (all served via API):

Layer 1 — Current heatmap: 
  Weighted scan events (normal=0.1, flagged=0.3-1.0)
  with time decay (exponential, half-life=7 days)

Layer 2 — Cluster analysis:
  DBSCAN on flagged events to identify discrete hotspots
  Track cluster growth over time windows (1w, 2w, 4w)
  
Layer 3 — Predicted hotspots:
  Simple linear extrapolation of cluster growth rates
  Flag clusters where growth rate > 2x as "emerging threats"

API output format for frontend:
{
  "heatmap_points": [[lat, lng, intensity], ...],
  "clusters": [
    {
      "center_lat": 22.71,
      "center_lng": 75.85,
      "radius_km": 15,
      "event_count": 47,
      "severity": "critical",
      "growth_rate": 2.3,  // events per week trend
      "top_anomaly_types": ["velocity_violation", "path_deviation"],
      "label": "Badi-Indore Cluster"
    }
  ],
  "predicted_hotspots": [
    {
      "center_lat": 26.84,
      "center_lng": 80.94,
      "predicted_severity": "high",
      "confidence": 0.72,
      "eta_days": 14,  // estimated days until critical
      "reason": "Flag rate increasing 3x week-over-week"
    }
  ],
  "stats": {
    "total_scans": 50000,
    "total_flags": 1200,
    "total_velocity_alerts": 89,
    "active_hotspots": 5,
    "emerging_threats": 2
  }
}
"""

from sklearn.cluster import DBSCAN
import numpy as np
from datetime import datetime, timedelta

class HeatmapEngine:
    """
    Hotspot detection and prediction engine.
    
    Uses DBSCAN (eps=0.05 ≈ 5km, min_samples=3) for clustering.
    Tracks clusters across time windows for growth prediction.
    """
    
    def __init__(self):
        self.eps_degrees = 0.05  # ~5km at Indian latitudes
        self.min_samples = 3
        self.time_decay_halflife_days = 7
    
    def compute_heatmap(self, scan_events: list, reference_time: datetime = None) -> dict:
        """
        Compute full heatmap response from scan events.
        
        Each scan_event dict has:
          lat, lng, timestamp, is_flagged, flag_severity, 
          is_velocity_alert, anomaly_score
        
        Steps:
        1. Apply time decay weighting to all events
        2. Compute intensity per event based on severity + decay
        3. Run DBSCAN on flagged events to find clusters
        4. Compute cluster growth rates across 4 weekly windows
        5. Predict emerging hotspots from growth trends
        6. Return full response object
        """
        pass
    
    def _compute_intensity(self, event: dict, reference_time: datetime) -> float:
        """Compute intensity weight for a single event."""
        # Base intensity by type
        # Time decay: intensity * exp(-ln(2) * days_old / halflife)
        pass
    
    def _find_clusters(self, flagged_events: list) -> list:
        """DBSCAN clustering on flagged events."""
        pass
    
    def _predict_hotspots(self, clusters: list, weekly_cluster_data: list) -> list:
        """Predict which clusters will escalate based on growth trends."""
        # Simple linear regression on cluster size over weekly windows
        # Flag if predicted to double in next 2 weeks
        pass
    
    def get_zone_risk_level(self, lat: float, lng: float) -> dict:
        """
        For a given location, return the risk level based on proximity to hotspots.
        Used by risk scorer module.
        """
        pass
```

### 8.2 Frontend Heatmap Component

Create `dashboard/src/components/HeatmapView.jsx`:

```jsx
/**
 * Interactive heatmap built with React-Leaflet + leaflet.heat
 * 
 * Features:
 * - Multi-layer heatmap (scans, flags, velocity alerts)
 * - Toggle layers independently
 * - Cluster markers with popup details
 * - Pulsing circles for predicted hotspots
 * - Auto-refresh every 30 seconds
 * - Click on cluster → show detailed stats + affected medicines
 * - India-centered view with zoom to state level
 * 
 * Gradient:
 *   0.2 → #00ff00 (green, normal activity)
 *   0.4 → #ffff00 (yellow, elevated flags)
 *   0.6 → #ff8c00 (orange, multiple flags)
 *   0.8 → #ff0000 (red, velocity alerts + convergence)
 *   1.0 → #8b0000 (dark red, confirmed hotspot)
 * 
 * Data source: GET /api/heatmap-data from FastAPI backend
 * 
 * Dependencies:
 *   - react-leaflet
 *   - leaflet
 *   - leaflet.heat (import as side effect)
 */
```

---

## 9. MODULE 6: Composite Risk Scoring Engine

> **Priority**: MEDIUM — ties everything together
> **Time estimate**: 2 hours
> **Location**: `ai-engine/models/risk_scorer.py`

```python
# ai-engine/models/risk_scorer.py

"""
Composite Risk Scoring Engine

Combines ALL AI signals into a single 0-100 Trust Score per medicine.
This is the central intelligence output that drives the dashboard.

Input signals and weights:
  1. Image verification confidence (30%)
     - Source: PillVerifier.verify()
     - Range: 0-1 (inverted: 1-confidence = risk)
     
  2. Supply chain anomaly score (25%)
     - Source: AnomalyDetector.detect()
     - Range: 0-1
     
  3. Adverse event risk score (20%)
     - Source: AdverseEventMonitor.analyze_drug()
     - Range: 0-1
     
  4. Geographic risk (hotspot proximity) (15%)
     - Source: HeatmapEngine.get_zone_risk_level()
     - Range: 0-1 (1 = inside critical hotspot)
     
  5. External risk factors (10%)
     - Drug shortage status (from OpenFDA)
     - Recent recall history
     - Actor reputation score (from smart contract)
     - Range: 0-1

Output:
{
  "medicine_id": 12345,
  "trust_score": 73,        # 0-100 (higher = more trustworthy)
  "risk_level": "medium",   # low (80-100), medium (50-79), high (20-49), critical (0-19)
  "flag_severity": 1,       # Maps to FlagSeverity enum: 0=Low, 1=Medium, 2=High, 3=Critical
  "signals": {
    "image_verification": {"score": 0.92, "status": "pass"},
    "supply_chain": {"score": 0.15, "status": "warning", "reasons": ["velocity_near_threshold"]},
    "adverse_events": {"score": 0.35, "status": "elevated", "alerts": ["2x therapeutic failures"]},
    "geographic_risk": {"score": 0.7, "status": "high", "nearest_hotspot": "Badi-Indore (12km)"},
    "external_factors": {"score": 0.2, "status": "normal"}
  },
  "recommendation": "Flag for manual inspection — elevated adverse event signals in high-risk zone",
  "auto_flag": true,         # Should smart contract auto-flag this?
  "timestamp": "2024-01-15T10:30:00Z"
}

Smart contract integration:
  If trust_score < 50 → auto-call core.flagDrug(medicineId, FlagSeverity.High)
  If trust_score < 20 → auto-call core.flagDrug(medicineId, FlagSeverity.Critical)
  If trust_score 50-70 → emit warning event only (don't flag)
"""

class RiskScorer:
    
    WEIGHTS = {
        "image_verification": 0.30,
        "supply_chain": 0.25,
        "adverse_events": 0.20,
        "geographic_risk": 0.15,
        "external_factors": 0.10
    }
    
    TRUST_THRESHOLDS = {
        "low": (80, 100),     # FlagSeverity.Low (no action)
        "medium": (50, 79),   # FlagSeverity.Medium (warning)
        "high": (20, 49),     # FlagSeverity.High (auto-flag)
        "critical": (0, 19)   # FlagSeverity.Critical (auto-flag + alert)
    }
    
    def __init__(self, pill_verifier, anomaly_detector, adverse_monitor, heatmap_engine):
        self.pill_verifier = pill_verifier
        self.anomaly_detector = anomaly_detector
        self.adverse_monitor = adverse_monitor
        self.heatmap_engine = heatmap_engine
    
    async def score_medicine(self, medicine_id: int, image=None, 
                              transaction_data=None, drug_name=None,
                              location=None, actor_reputation=None) -> dict:
        """
        Compute composite risk score for a medicine.
        Any signal can be None (missing signals get neutral score 0.5).
        """
        pass
    
    def _compute_trust_score(self, signal_scores: dict) -> int:
        """Weighted average, inverted to trust scale (0-100)."""
        # risk = weighted sum of signal scores (each 0-1)
        # trust = int((1 - risk) * 100)
        pass
    
    def _map_to_severity(self, trust_score: int) -> int:
        """Map trust score to FlagSeverity enum value."""
        pass
    
    def _generate_recommendation(self, signals: dict, trust_score: int) -> str:
        """Human-readable recommendation text."""
        pass
```

---

## 10. MODULE 7: FastAPI Backend (AI Orchestrator)

> **Priority**: HIGH — glues everything together
> **Time estimate**: 3–4 hours
> **Location**: `ai-engine/main.py` and `ai-engine/api/`

### 10.1 Main App

```python
# ai-engine/main.py

"""
FastAPI application — AI Orchestrator for PharmaChain

Endpoints:
  POST /api/verify-image          → Pill image verification
  POST /api/detect-anomaly        → Single transaction anomaly check
  POST /api/detect-anomaly-batch  → Batch anomaly detection
  GET  /api/adverse-events/{drug} → Adverse event analysis
  GET  /api/heatmap-data          → Full heatmap data (points + clusters + predictions)
  GET  /api/heatmap-zone-risk     → Risk level for a specific lat/lng
  POST /api/risk-score            → Composite risk score for a medicine
  GET  /api/risk-score/{med_id}   → Get cached risk score
  GET  /api/dashboard-stats       → Summary statistics for dashboard
  GET  /api/health                → Health check

  WebSocket /ws/alerts            → Real-time alert stream

Startup:
  1. Load all models (pill CNN, anomaly detector)
  2. Load heatmap seed data
  3. Start blockchain event listener in background
  4. Initialize OpenFDA client

CORS: Allow localhost:5173 (Vite) and localhost:3000 (CRA)
"""

from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="PharmaChain AI Engine", version="1.0.0")

# Register all route handlers from api/ directory
# Start background tasks for event listening
```

### 10.2 Route Files

Each route file in `ai-engine/api/` handles one domain:

**verify_routes.py**:
```
POST /api/verify-image
  - Accept: multipart/form-data with image file
  - Optional query param: medicine_id (to compare with on-chain contentHash)
  - Returns: PillVerifier.verify() result
  - If medicine_id provided: also fetch on-chain contentHash and compare embeddings
```

**anomaly_routes.py**:
```
POST /api/detect-anomaly
  - Accept: JSON transaction data (matches FEATURE_COLUMNS schema)
  - Returns: AnomalyDetector.detect() result
  
POST /api/detect-anomaly-batch
  - Accept: JSON array of transactions
  - Returns: Array of detection results + summary stats
```

**heatmap_routes.py**:
```
GET /api/heatmap-data?time_window=7d&min_severity=low
  - Returns: Full heatmap JSON (points, clusters, predictions, stats)
  - Cached for 60 seconds, refreshed by blockchain events

GET /api/heatmap-zone-risk?lat=22.71&lng=75.85
  - Returns: Risk level for specific location
```

**adverse_event_routes.py**:
```
GET /api/adverse-events/{drug_name}?days_back=90
  - Returns: AdverseEventMonitor.analyze_drug() result
  
GET /api/drug-identity/{drug_name}
  - Returns: NDC ground truth data

GET /api/drug-recalls/{drug_name}
  - Returns: Recent recalls
```

**risk_routes.py**:
```
POST /api/risk-score
  - Accept: JSON with medicine_id, optional image, transaction_data, drug_name, location
  - Returns: Full RiskScorer.score_medicine() result
  - Side effect: If auto_flag=true, triggers blockchain flagDrug() call

GET /api/risk-score/{medicine_id}
  - Returns: Cached latest risk score
  
GET /api/dashboard-stats
  - Returns: Aggregate stats for dashboard header
    {
      total_scans, total_flags, total_anomalies, active_hotspots,
      avg_trust_score, highest_risk_medicines (top 10), 
      recent_alerts (last 20)
    }
```

---

## 11. MODULE 8: Blockchain Bridge (Web3 Integration)

> **Priority**: HIGH — connects AI to smart contracts
> **Time estimate**: 2–3 hours
> **Location**: `ai-engine/blockchain/`

### 11.1 Bridge Module

```python
# ai-engine/blockchain/bridge.py

"""
Web3.py bridge to interact with PharmaChain smart contracts.

Capabilities:
  READ:
    - Get medicine details (id, batchId, status, owner, flags)
    - Get custody history (addresses + timestamps)
    - Get scan history from Scanner contract
    - Get scan count and stats
    - Get actor details (role, name, location, reputation)
    - Check if medicine is registered
    - Verify content hash
    
  WRITE:
    - Flag drug (when AI detects anomaly): core.flagDrug(id, severity)
    - Log scan (when image verified): scanner.logScan(id, lat, lng, location, deviceId)

Setup:
  - Load ABIs from blockchain/abis/ directory
  - Connect to provider (local Hardhat or Sepolia)
  - Use admin private key for write operations
  
NOTE: ABI files must be generated first by running `npx hardhat compile` 
in the pharmachain-contracts directory and copying the ABI JSON from 
artifacts/contracts/PharmaChainCore.sol/PharmaChainCore.json (the "abi" field)
"""
```

### 11.2 Event Listener

```python
# ai-engine/blockchain/event_listener.py

"""
Background event listener that feeds real-time blockchain events into the AI pipeline.

Listens for:
  1. DrugScanned → feed to anomaly detector + update heatmap
  2. VelocityAlert → immediate high-severity heatmap update + alert
  3. DrugFlagged → update heatmap + recalculate batch risk scores
  4. CustodyTransferred → update supply chain graph + anomaly check
  5. MedicineRegistered → add to known medicines cache

Architecture:
  - Runs as asyncio background task in FastAPI startup
  - Uses web3.py event filters with polling (every 2 seconds)
  - Emits events to WebSocket connections for real-time dashboard updates
  - Buffers events for batch processing (flush every 10 seconds)
  
For hackathon demo:
  - Also support a "simulation mode" that replays synthetic events
    at accelerated speed to show the full pipeline in action
  - Toggle via ENV: SIMULATION_MODE=true
"""
```

---

## 12. MODULE 9: React Dashboard Frontend

> **Priority**: MEDIUM-HIGH — needed for demo
> **Time estimate**: 4–6 hours
> **Location**: `dashboard/`

### 12.1 Create with Vite

```bash
npm create vite@latest dashboard -- --template react
cd dashboard
npm install react-leaflet leaflet leaflet.heat recharts axios ethers lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 12.2 Component Specifications

**App.jsx** — Main layout:
```
- Top header bar: "PharmaChain AI" logo + connection status + stats summary
- Left sidebar: Navigation (Dashboard, Scan, Supply Chain, Heatmap, Alerts)
- Main content area: Renders active page component
- Bottom: Real-time alert ticker (WebSocket-fed)
```

**RiskDashboard.jsx** — Main dashboard page:
```
- Row 1: 4 stat cards (Total Scans, Active Flags, Trust Score Avg, Active Hotspots)
  Use lucide-react icons, color-coded (green/yellow/red)
- Row 2: Left = Risk score distribution chart (Recharts BarChart, x=score buckets, y=count)
         Right = Recent alerts feed (scrollable list, color by severity)
- Row 3: Left = Top 10 highest-risk medicines table
         Right = Hotspot mini-map (small Leaflet map)
```

**PillScanner.jsx** — Image verification page:
```
- Upload zone: Drag & drop or click to upload pill image
- Camera button: Use navigator.mediaDevices.getUserMedia for mobile
- After upload: Show image preview + loading spinner
- Result card: 
  - Circular trust score gauge (green/yellow/red)
  - Prediction label: "Authentic" / "Suspicious" / "Counterfeit"
  - Confidence percentage
  - Embedding hash (truncated)
  - "Log to Blockchain" button → calls scanner.logScan()
  - "Flag Drug" button (if suspicious) → calls core.flagDrug()
```

**HeatmapView.jsx** — Full-page heatmap:
```
- Full-width Leaflet map centered on India [20.5937, 78.9629], zoom 5
- Heatmap layer using leaflet.heat plugin
- Toggle controls: Show/hide scan layer, flag layer, alert layer
- Cluster markers: Circle markers with popup showing cluster stats
- Predicted hotspot markers: Pulsing animated circles (CSS animation)
- Sidebar panel: List of active hotspots ranked by severity
- Time range selector: 24h, 7d, 30d, 90d
- Auto-refresh toggle (every 30s)
```

**SupplyChainGraph.jsx** — Supply chain visualization:
```
- Medicine ID input field
- On search: Fetch custody history from blockchain
- Display: Vertical timeline showing each custody transfer
  Each node: Actor name, role (icon), location, timestamp
  Edges: Show time elapsed between transfers
  Color: Green (normal), Yellow (slow), Red (anomaly detected)
- Side panel: Anomaly detection result for this medicine's chain
```

**AlertsFeed.jsx** — Real-time alerts:
```
- WebSocket connection to /ws/alerts
- Each alert card shows: timestamp, medicine_id, alert type, severity, location
- Filter by severity (Low/Medium/High/Critical)
- Click alert → navigate to relevant medicine detail
- Sound notification for Critical alerts (optional)
```

---

## 13. Testing & Demo Script

### 13.1 Demo Flow Script

Create `demo.py` in project root — a script that simulates the full end-to-end flow for hackathon presentation:

```python
"""
PharmaChain Demo Script
Run this during the hackathon presentation to demonstrate the full pipeline.

Demo Flow (5 minutes):

PHASE 1 — Setup (30 sec)
  - Show dashboard with initial state (no data)
  - Show smart contracts deployed on Hardhat local node

PHASE 2 — Normal Operations (1 min)
  - Register 3 manufacturers, 5 distributors, 10 pharmacies
  - Register 100 medicines across 5 batches
  - Simulate normal supply chain flow (transfers + scans)
  - Heatmap shows green — all normal

PHASE 3 — Introduce Counterfeits (2 min)
  - Upload a "suspicious" pill image → CNN flags it (confidence 0.42)
  - Simulate velocity anomaly: medicine scanned in Mumbai, then Chennai 30 min later
  - VelocityAlert fires on-chain
  - Anomaly detector flags the transaction
  - Heatmap starts turning yellow → orange in Mumbai corridor
  - Risk score drops from 85 to 32

PHASE 4 — AI Intelligence Layer (1 min)
  - Query OpenFDA: show spike in "drug ineffective" for batch drug
  - DBSCAN identifies emerging hotspot near Indore
  - Predicted hotspot appears in neighboring Bhopal (pulsing circle)
  - Composite risk score triggers auto-flag on blockchain
  - Smart contract emits DrugFlagged event

PHASE 5 — Resolution (30 sec)
  - Show full audit trail: every scan, transfer, AI decision on-chain
  - Regulator resolves flag after investigation
  - Reputation scores adjusted
"""
```

### 13.2 Quick Test Commands

```bash
# 1. Generate synthetic data
cd ai-engine
python -m data.synthetic.generate_supply_chain_data
python -m data.synthetic.generate_scan_events
python -m data.synthetic.generate_heatmap_seed

# 2. Train models
python -m models.train_pill_cnn --demo_mode  # uses augmented data if no dataset
python -m models.train_anomaly_detector

# 3. Start backend
uvicorn main:app --reload --port 8000

# 4. Start frontend
cd ../dashboard
npm run dev

# 5. Run demo simulation
cd ..
python demo.py
```

---

## 14. Datasets to Download

### Must-have (download these first):

| Dataset | URL | Size | Use |
|---|---|---|---|
| ePillID Benchmark | `https://github.com/usuyama/ePillID-benchmark` | ~2GB | CNN training |
| Roboflow Counterfeit Detection | `https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection` | ~200MB | YOLO annotations |

### Good to have (use if time permits):

| Dataset | URL | Use |
|---|---|---|
| Kaggle Pharmaceutical Tablets | `https://www.kaggle.com/datasets/trumedicines/pharmaceutical-tablets-dataset` | Additional pill images |
| Kaggle A-Z Medicine Dataset India | `https://www.kaggle.com/datasets/shudhanshusingh/az-medicine-dataset-of-india` | Indian drug reference data |
| Pill Defects (GitHub) | `https://github.com/PerceptiLabs/Pill-Defects` | Normal vs defective classification |
| SupplyGraph GNN Benchmark | `https://github.com/ciol-researchlab/SupplyGraph` | GNN supply chain model |
| IoT Pharma Supply Chain (Kaggle) | `https://www.kaggle.com/datasets/hennryprince/iot-enabled-pharmaceutical-supply-chain` | IoT sensor data |

### API-based (no download needed):

| Source | Endpoint | Use |
|---|---|---|
| OpenFDA FAERS | `https://api.fda.gov/drug/event.json` | Adverse event mining |
| OpenFDA NDC | `https://api.fda.gov/drug/ndc.json` | Drug identity verification |
| OpenFDA Recalls | `https://api.fda.gov/drug/enforcement.json` | Recall cross-referencing |
| OpenFDA Drug Labels | `https://api.fda.gov/drug/label.json` | Drug label data |

---

## BUILD ORDER (for Claude Code)

Execute modules in this exact order:

```
Step 1  → Directory structure setup + dependencies install
Step 2  → MODULE 1: Synthetic data generator (all other modules need this)
Step 3  → MODULE 8: Blockchain bridge (needed by most modules for integration)
Step 4  → MODULE 2: Pill CNN (train with --demo_mode if no dataset)
Step 5  → MODULE 3: Anomaly detector (train on synthetic data from step 2)
Step 6  → MODULE 4: Adverse event monitor (API-only, no training)
Step 7  → MODULE 5: Heatmap engine (uses synthetic data from step 2)
Step 8  → MODULE 6: Risk scorer (combines modules 4-7)
Step 9  → MODULE 7: FastAPI backend (wire up all routes)
Step 10 → MODULE 9: React dashboard (connect to FastAPI endpoints)
Step 11 → Demo script + testing
```

**Each module should be built so it works independently first (with mock data/inputs), then integrated.**

---

## KEY SMART CONTRACT INTERFACE REFERENCE

For the blockchain bridge, these are the exact function signatures and events to integrate with:

### PharmaChainCore
```
// READ
medicines(uint256 id) → Medicine struct
custodyHistory(uint256 id) → address[]
timestampHistory(uint256 id) → uint256[]
isMedicineRegistered(uint256 id) → bool
actors(address) → Actor struct
getActorRole(address) → Role enum
getCustodyHistory(uint256 id) → (address[], uint256[])
verifyHash(uint256 id, bytes32 hash) → bool

// WRITE
flagDrug(uint256 id, FlagSeverity severity)
resolveFlag(uint256 id)

// EVENTS
MedicineRegistered(uint256 indexed id, uint256 indexed batchId, address indexed manufacturer, bytes32 contentHash, uint256 timestamp)
CustodyTransferred(uint256 indexed id, address indexed from, address indexed to, State newStatus, uint256 timestamp)
DrugFlagged(uint256 indexed id, address indexed flagger, FlagSeverity severity, uint256 timestamp)

// ENUMS
State: Manufactured(0), InTransit(1), AtDistributor(2), AtPharmacy(3), Dispensed(4), Flagged(5)
Role: None(0), Manufacturer(1), Distributor(2), Pharmacy(3), Consumer(4), Regulator(5), Admin(6)
FlagSeverity: Low(0), Medium(1), High(2), Critical(3)
```

### PharmaChainScanner
```
// READ
scanHistory(uint256 medicineId) → ScanRecord[]
scanCount(uint256 medicineId) → uint256
getScanHistory(uint256 medicineId) → ScanRecord[]
getLastScan(uint256 medicineId) → (address, int256, int256, uint256, string)
getStats() → (uint256 totalScans, uint256 totalAlerts)

// WRITE
logScan(uint256 medicineId, int256 latitude, int256 longitude, string location, string deviceId)
logBatchScan(uint256[] medicineIds, int256 latitude, int256 longitude, string location, string deviceId)

// EVENTS
DrugScanned(uint256 indexed medicineId, address indexed scanner, int256 latitude, int256 longitude, uint256 scanNumber, uint256 timestamp)
VelocityAlert(uint256 indexed medicineId, address indexed scanner, string currentLocation, string previousLocation, uint256 timeDelta, uint256 timestamp)

// NOTE: latitude/longitude are stored as int256 * 1e6 (e.g., 19283746 = 19.283746°)
```

### PharmaChainBatch
```
// WRITE  
createBatch(uint256 batchId, string batchNumber, uint256 totalUnits, string ipfsHash, bytes32 contentHash)
completeBatch(uint256 batchId)

// EVENTS
BatchCreated(uint256 indexed batchId, string batchNumber, uint256 totalUnits, address indexed manufacturer, uint256 timestamp)
BatchCompleted(uint256 indexed batchId, uint256 registeredUnits, uint256 timestamp)
```
