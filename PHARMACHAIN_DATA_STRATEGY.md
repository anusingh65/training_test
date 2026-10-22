# PharmaChain — Real Data Strategy

> **Philosophy**: Real data first → Scrape it ourselves second → Label it ourselves third → Synthetic ONLY as last resort
>
> Hand this to Claude Code alongside the main implementation plan. This replaces MODULE 1 (Synthetic Data Generator) with a tiered real-data acquisition pipeline.

---

## DATA TIER SYSTEM

For every module, we follow this priority:

```
TIER 1 → Direct download (government/research datasets, APIs)
TIER 2 → Scrape it ourselves (write scrapers for public sources)
TIER 3 → Collect & label it ourselves (take photos, manually annotate)
TIER 4 → Synthetic generation (ONLY if Tiers 1-3 fail or for augmentation)
```

---

## MODULE A: PILL IMAGE VERIFICATION DATA

### TIER 1 — Direct Downloads

#### 1. NLM C3PI / RxIMAGE Pill Image Collection (BEST SOURCE)
- **What**: 4,000+ high-quality reference images + 133,000 consumer-grade images of US prescription pills. Lab-controlled photography, segmented backgrounds, with NDC codes, shape, color, imprint metadata.
- **Download links**:
  - Reference images (6.8 GB): `https://data.lhncbc.nlm.nih.gov/public/Pills/PillProjectDisc1.zip`
  - Sample data (493 MB): `https://data.lhncbc.nlm.nih.gov/public/Pills/sampleData.zip`
  - Training images: `https://data.lhncbc.nlm.nih.gov/public/Pills/`
  - Data catalog page: `https://catalog.data.gov/dataset/computational-photography-project-for-pill-identification-c3pi-82201`
- **Format**: JPEG images + XML/CSV metadata (NDC, brand name, shape, color, imprint, size)
- **License**: Public domain (US government)
- **How to use**: These are all AUTHENTIC pills. Use as the "authentic" class for the CNN.

#### 2. NLM Pillbox Dataset
- **What**: 8,693 high-resolution pill photos with 83,925 rows of drug info (shape, color, imprint, active ingredients, manufacturer)
- **Download**: `https://datadiscovery.nlm.nih.gov/Drugs-and-Supplements/Pillbox/crzr-uvwg`
- **Format**: Images (JPEG on gray background) + CSV database
- **How to use**: Additional authentic pill images. Cross-reference with C3PI.

#### 3. ePillID Benchmark (CVPR 2020)
- **What**: ~13,000 images across 9,804 appearance classes. Comes with a multi-head metric learning framework already built.
- **Download**: `git clone https://github.com/usuyama/ePillID-benchmark`
- **Note**: Dataset itself must be downloaded from NLM (it uses C3PI data), but the code/splits/framework are on GitHub
- **How to use**: Use their train/test splits and metric learning code directly. Saves days of work.

#### 4. Roboflow Counterfeit Medicine Detection
- **What**: 1,555 annotated images specifically for counterfeit detection with bounding box annotations
- **Download**: `https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection`
  - Export in "Folder" format for PyTorch, or YOLO/COCO format
  - Requires free Roboflow account
- **Format**: Images + annotations (YOLO txt, COCO JSON, Pascal VOC XML)
- **How to use**: This is the ONLY dataset that has actual authentic vs counterfeit labels. Use as primary training set.

#### 5. Kaggle Datasets
Download all of these — each adds something different:

| Dataset | URL | What it adds |
|---|---|---|
| Pharmaceutical Tablets | `kaggle.com/datasets/trumedicines/pharmaceutical-tablets-dataset` | 20K augmented surface-pattern images |
| OGYEIv2 | `kaggle.com/datasets/richardradli/ogyeiv2` | 112 pill classes, multi-class |
| Pill Defects | `github.com/PerceptiLabs/Pill-Defects` | Normal vs defective binary classification |
| Drug Name Detection | `kaggle.com/datasets/pkdarabi/the-drug-name-detection-dataset` | YOLO-annotated packaging text |
| Medicine Tablet Packs | `kaggle.com/datasets/nitesh31mishra/medicine-tablet-pack-image-dataset` | Blister pack images |
| Mobile Pharma Packages | `kaggle.com/datasets/aryashah2k/mobile-captured-pharmaceutical-medication-packages` | Real mobile-captured packaging |

### TIER 2 — Scrape It Ourselves

#### 6. RxImage API Bulk Scraper

Write a Python script to systematically download pill images via the RxImage API:

```python
"""
RxImage API Bulk Downloader
Downloads all available pill images with metadata.

API Base: https://rximage.nlm.nih.gov/api/rximage/1/rxnav
Documentation: https://rxnav.nlm.nih.gov/RxImageAPIs.html

Strategy:
  - Iterate through all colors: blue, brown, gray, green, orange, pink, purple, red, white, yellow
  - For each color, paginate through all results
  - Download both rxnav (with info panel) and rxbase (clean) versions
  - Save metadata (NDC, brand name, generic name, shape, imprint, size) to CSV
  - Rate limit: 1 request per second (be respectful to NIH servers)

Example API call:
  https://rximage.nlm.nih.gov/api/rximage/1/rxnav?color=blue&resolution=600&rLimit=100&rStart=0

Response includes imageUrl field — download from that URL.
"""

import requests
import time
import csv
import os
from pathlib import Path

COLORS = ["blue", "brown", "gray", "green", "orange", "pink", "purple", "red", "white", "yellow"]
BASE_URL = "https://rximage.nlm.nih.gov/api/rximage/1/rxnav"
OUTPUT_DIR = "data/pill_images/rximage_scraped"
METADATA_FILE = "data/pill_images/rximage_metadata.csv"

def scrape_all_pills():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    metadata_rows = []
    
    for color in COLORS:
        offset = 0
        while True:
            params = {
                "color": color,
                "resolution": 600,  # high res
                "rLimit": 100,
                "rStart": offset,
                "includeIngredients": "true"
            }
            resp = requests.get(BASE_URL, params=params)
            data = resp.json()
            
            if not data.get("nlmRxImages"):
                break
            
            for pill in data["nlmRxImages"]:
                image_url = pill.get("imageUrl", "")
                if not image_url:
                    continue
                
                # Download image
                ndc = pill.get("ndc11", "unknown")
                filename = f"{ndc}_{pill.get('id', '')}.jpg"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                if not os.path.exists(filepath):
                    img_resp = requests.get(image_url)
                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)
                
                # Save metadata
                metadata_rows.append({
                    "filename": filename,
                    "ndc": ndc,
                    "brand_name": pill.get("name", ""),
                    "generic_name": pill.get("genericName", ""),
                    "shape": pill.get("shape", ""),
                    "color": pill.get("color", ""),
                    "imprint": pill.get("imprint", ""),
                    "size_mm": pill.get("size", ""),
                    "manufacturer": pill.get("labeler", ""),
                    "active_ingredients": pill.get("activeIngredients", "")
                })
                
                time.sleep(0.5)  # rate limit
            
            offset += 100
            if len(data["nlmRxImages"]) < 100:
                break
    
    # Write metadata CSV
    with open(METADATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
        writer.writeheader()
        writer.writerows(metadata_rows)
    
    print(f"Downloaded {len(metadata_rows)} pill images to {OUTPUT_DIR}")

if __name__ == "__main__":
    scrape_all_pills()
```

#### 7. DailyMed SPL Image Scraper

DailyMed (dailymed.nlm.nih.gov) has drug label images submitted by manufacturers as part of FDA labeling requirements.

```python
"""
DailyMed Image Scraper
Downloads drug packaging/label images from FDA's DailyMed.

API: https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json
Image API: https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setId}/media.json

These are OFFICIAL manufacturer-submitted images — perfect ground truth for packaging verification.

Strategy:
  1. Get list of all SPLs (paginate, ~100K total)
  2. For each SPL, fetch media list
  3. Download images that are drug product photos (not chemical structures)
  4. Save with SPL setId + NDC linkage
"""
```

### TIER 3 — Collect & Label It Ourselves

#### 8. Self-Photographed Indian Medicine Dataset

This is the most valuable dataset for an India-focused hackathon because NO dataset above covers Indian pill strips/blisters.

**Collection protocol** (can be done in 2-3 hours):

```
WHAT TO PHOTOGRAPH:
  - Go to any pharmacy. Buy 10-15 common OTC medicines (Crocin, Dolo 650, 
    Azithral, Pan-D, Allegra, Combiflam, Zincovit, Shelcal, etc.)
  - For each medicine, photograph:
    1. Full blister strip (front) — good lighting, plain background
    2. Full blister strip (back) — showing batch no, mfg date, exp date
    3. Individual tablet/capsule out of strip — on white paper
    4. Box/carton front — showing brand name, composition
    5. Box/carton back — showing manufacturer, batch, barcodes
    6. QR code closeup (if Schedule H2 drug)
  
  CAMERA: Phone camera is fine. Natural daylight or desk lamp. 
  Avoid flash. Keep distance consistent (~30cm).
  
  Take 5-10 photos per angle (slightly different positions/rotations) 
  for augmentation diversity.

HOW MANY:
  - 15 medicines × 6 angles × 5 shots = 450 photos
  - This is your "authentic" Indian medicine dataset

LABELING:
  Create a CSV file: filename, medicine_name, brand, composition, 
  manufacturer, batch_no, mfg_date, exp_date, mrp, photo_type 
  (strip_front, strip_back, tablet, box_front, box_back, qr_code), 
  label (authentic)

CREATING "COUNTERFEIT" TRAINING DATA FROM AUTHENTIC IMAGES:
  DO NOT fake medicines. Instead, apply realistic corruption augmentations:
  
  - Color shift: Slightly off-color tablets (hue shift ±15°)
  - Print quality degradation: Gaussian blur on text (simulates bad printing)
  - Font mismatch: Use OCR to extract text, re-render with slightly wrong font
  - Missing elements: Mask out batch number or manufacturer logo
  - Wrong packaging: Swap tablet images between different brands
  - Damage simulation: Add spots, discoloration patches
  
  Label these as "suspicious" (not "counterfeit" — they're augmented, not real fakes)
  
  This gives you:
    450 authentic + 450 augmented-suspicious = 900 labeled images
  
  Combined with NLM C3PI (4000+) + Roboflow (1555) + Kaggle datasets = 
  plenty for transfer learning with EfficientNet
```

### TIER 4 — Synthetic (only for augmentation)

Only generate synthetic data to AUGMENT the real datasets above, not replace them:
- Standard augmentations: rotation, flip, color jitter, random crop, Gaussian noise
- CutMix / MixUp for regularization during training
- Style transfer to simulate different lighting conditions

---

## MODULE B: SUPPLY CHAIN ANOMALY DETECTION DATA

### TIER 1 — Real Datasets

#### 1. Kaggle IoT Pharma Supply Chain
- **What**: Real IoT sensor data from pharma companies (Abbott, Pfizer, Getz Pharma) including temperature monitoring, shipment tracking, environmental conditions
- **Download**: `https://www.kaggle.com/datasets/hennryprince/iot-enabled-pharmaceutical-supply-chain`
- **How to use**: Temperature excursions and environmental anomalies are strong signals for counterfeit detection (counterfeits don't maintain cold chain)

#### 2. Kaggle Pharmaceutical Supply Chain Optimization
- **What**: Inventory, demand, distribution data across pharmaceutical supply networks
- **Download**: `https://www.kaggle.com/datasets/mohammedashraf000/pharmaceutical-supply-chain-optimization`
- **How to use**: Train demand forecasting models. Unexpected demand spikes for shortage drugs = counterfeit insertion signal

#### 3. Kaggle Smart Logistics Supply Chain
- **What**: Shipment tracking, delivery times, route data, logistics metrics
- **Download**: `https://www.kaggle.com/datasets/ziya07/smart-logistics-supply-chain-dataset`
- **How to use**: Learn normal shipment velocity patterns. Deviations = anomaly features

#### 4. SupplyGraph GNN Benchmark
- **What**: Real-world supply chain graph dataset with node features and temporal data
- **Download**: `git clone https://github.com/ciol-researchlab/SupplyGraph`
- **How to use**: If you have time, train a GNN. The benchmark includes node classification and link prediction tasks that directly map to "find suspicious nodes in supply network"

### TIER 2 — Scrape from Blockchain Events

If you deploy your contracts to a local Hardhat node and run the demo script (which simulates real supply chain flow), you get REAL blockchain event data:

```python
"""
Blockchain Event Harvester

After deploying contracts and running demo transactions on local Hardhat:
1. Query all past DrugScanned events
2. Query all CustodyTransferred events  
3. Query all VelocityAlert events
4. Query all DrugFlagged events

Export to CSV with engineered features.
This is REAL data from YOUR smart contracts — not synthetic.

The demo.py script should create realistic flows:
  - 50 legitimate supply chains (Manufacturer→Distributor→Pharmacy→Consumer)
  - 10 anomalous chains (skipped steps, velocity violations, duplicates)
  - Run over simulated 30-day period using Hardhat time manipulation
"""

# Use hardhat's evm_increaseTime and evm_mine to simulate time passing
# This creates a realistic event dataset from your own contracts
```

### TIER 3 — Augment Real Data with Realistic Anomalies

Take the real Kaggle supply chain data and INJECT known anomaly patterns into copies of it:

```python
"""
Anomaly Injection Script

Takes real supply chain data (Kaggle datasets) and creates an anomaly-labeled version.

DO NOT modify the original data. Create copies and inject:
  - Velocity anomalies: Change timestamps to make transitions impossibly fast
  - Path deviations: Remove intermediate steps
  - Geographic impossibilities: Swap destination coordinates
  - Duplicate serial numbers: Copy rows with same product ID at different locations
  - Time anomalies: Shift timestamps to 2-5 AM
  
Label: is_anomaly=1, anomaly_type="velocity" | "path_skip" | "geo_impossible" etc.

This is MUCH better than fully synthetic data because:
  - The normal patterns are REAL (real distances, real timings, real routes)
  - Only the anomalies are injected
  - Model learns real-world normal distribution, not your assumptions about it
"""
```

---

## MODULE C: ADVERSE EVENT / PHARMACOVIGILANCE DATA

### TIER 1 — Direct Downloads & APIs (ALL REAL DATA)

This module uses 100% real data — no synthetic needed at all.

#### 1. FDA FAERS (Adverse Event Reports)
- **What**: 18+ million adverse event reports (2004–present). Includes drug names, reactions, outcomes, reporter type, dates.
- **Bulk download** (quarterly ASCII/XML ZIPs):
  - Portal: `https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html`
  - Each quarter is ~60-75 MB (ASCII) or ~110-140 MB (XML)
  - NBER has pre-cleaned CSV/Stata versions: `https://www.nber.org/research/data/fda-adverse-event-reporting-system`
- **OpenFDA API** (real-time queries, no download needed):
  - `https://api.fda.gov/drug/event.json?search=patient.drug.openfda.brand_name:"metformin"&count=patient.reaction.reactionmeddrapt.exact&limit=25`
  - `https://api.fda.gov/drug/event.json?search=reporttype:"2"+AND+patient.drug.drugcharacterization:"1"&count=patient.reaction.reactionmeddrapt.exact`
  - Report type 2 = Follow-up. Drugcharacterization 1 = Suspect drug.
  - Key reactions for counterfeit signals: `"DRUG INEFFECTIVE"`, `"PRODUCT QUALITY ISSUE"`, `"THERAPEUTIC RESPONSE UNEXPECTED"`
- **7 relational tables**: DEMO (demographics), DRUG, REAC (reactions), OUTC (outcomes), RPSR (report sources), THER (therapy), INDI (indications)
- **How to use**: Download 2-3 recent quarters. Filter for `"PRODUCT QUALITY ISSUE"` and `"DRUG INEFFECTIVE"` reactions. These are REAL counterfeit signals.

#### 2. OpenFDA Drug Reference APIs (Ground Truth)
All free, no API key needed (but rate limited to 240 req/min with key):

```
Drug NDC Directory:
  https://api.fda.gov/drug/ndc.json?search=brand_name:"Lipitor"&limit=5
  → Returns: manufacturer, active ingredients, dosage form, route, packaging

Drug Recalls/Enforcement:  
  https://api.fda.gov/drug/enforcement.json?search=report_date:[20240101+TO+20241231]&limit=100
  → Returns: recall reason, distribution, classification, status

Drug Labels:
  https://api.fda.gov/drug/label.json?search=openfda.brand_name:"metformin"&limit=1
  → Returns: Full prescribing info, warnings, ingredients

Drug Shortages (scrape from):
  https://www.accessdata.fda.gov/scripts/drugshortages/default.cfm
```

Bulk JSON downloads for all OpenFDA datasets: `https://open.fda.gov/apis/drug/event/download/`

#### 3. CDSCO Not-of-Standard-Quality Alerts (INDIA-SPECIFIC — GOLD MINE)

This is the single most important Indian dataset for your project.

CDSCO publishes monthly PDF lists of substandard and spurious drugs. Each contains:
- Drug name, batch number, manufacturing date, expiry date
- Manufacturer name and address (gives you geographic coordinates)
- Specific quality failure reason (dissolution, assay, identification)
- Whether declared "spurious" (fake) vs "NSQ" (substandard)
- Which lab tested it and which inspector drew the sample

**PDF URLs** (monthly, predictable pattern):

```
https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2018/UploadAlertsFiles/alert%20August-2024.pdf
https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2018/UploadAlertsFiles/NSQ%20Alert%20For%20the%20month%20of%20%20Sept-2024.pdf
```

Main alerts index page: `https://cdsco.gov.in/opencms/opencms/en/Notifications/Alerts/`
Latest alerts page: `https://cdsco.gov.in/opencms/opencms/en/Latest-Alerts/`

**Write a scraper/parser**:

```python
"""
CDSCO NSQ/Spurious Drug Alert PDF Parser

This is REAL Indian counterfeit/substandard drug data published by the government.

Steps:
1. Download all monthly alert PDFs from CDSCO (Jan 2023 – present)
2. Parse PDF tables using tabula-py or pdfplumber
3. Extract structured data: drug_name, batch_no, mfg_date, exp_date, 
   manufacturer_name, manufacturer_address, nsq_reason, 
   is_spurious (boolean), reporting_lab, reporting_inspector
4. Geocode manufacturer addresses using Google Maps / Nominatim API
5. Output: CSV with all fields + lat/lng coordinates

This gives you:
  - ~100-170 NSQ drugs per month × 24 months = 2,400-4,000 real records
  - ~4-10 spurious drugs per month = 100-240 confirmed fake drug records
  - Geographic distribution of real problem areas in India
  - Specific drugs/batches/manufacturers involved in counterfeiting
  
USE FOR:
  - Heatmap seed data (real hotspot locations!)
  - Training the anomaly detector (what batch patterns look suspicious)
  - Risk scoring (drugs from these manufacturers get higher base risk)
  - Demo narrative ("here's a real CDSCO alert, here's how our system catches it")
"""

import requests
import pdfplumber  # pip install pdfplumber
import re
import csv
from geopy.geocoders import Nominatim  # for geocoding manufacturer addresses

ALERT_URLS = [
    # Add URLs for each month — check the CDSCO alerts page for exact URLs
    # Pattern: https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2018/UploadAlertsFiles/...
]

def parse_cdsco_pdf(pdf_path):
    """Extract drug alert data from CDSCO PDF."""
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table[1:]:  # skip header
                    if len(row) >= 7:
                        records.append({
                            "drug_name": row[1],
                            "batch_no": row[2],
                            "mfg_date": row[3],
                            "exp_date": row[4],
                            "manufacturer": row[5],
                            "nsq_reason": row[6],
                            "reporting_lab": row[7] if len(row) > 7 else "",
                            "is_spurious": "spurious" in str(row[6]).lower()
                        })
    return records

def geocode_manufacturer(address):
    """Convert manufacturer address to lat/lng."""
    geolocator = Nominatim(user_agent="pharmachain-research")
    try:
        location = geolocator.geocode(address + ", India")
        if location:
            return location.latitude, location.longitude
    except:
        pass
    return None, None
```

#### 4. India PvPI (Pharmacovigilance Programme of India) 
- **ADRMS Portal**: `https://www.ipc.gov.in/` (launched Aug 2024)
- **ADR PvPI mobile app** data — India's 270+ ADR monitoring centres feed into this
- While the raw database isn't publicly downloadable, you can reference it and use CDSCO alert data as a proxy

#### 5. Kaggle A-Z Medicine Dataset of India
- **What**: Comprehensive list of Indian medicines with name, composition, uses, side effects, manufacturer
- **Download**: `https://www.kaggle.com/datasets/shudhanshusingh/az-medicine-dataset-of-india`
- **How to use**: Drug reference database. Cross-reference with CDSCO alerts to identify which types of drugs are most commonly counterfeited.

---

## MODULE D: HEATMAP / GEOGRAPHIC DATA

### TIER 1 — Real Geographic Data

#### 1. CDSCO Alert Data (geocoded) — from Module C scraper above
This IS your heatmap. Real locations of real drug quality failures across India. 

#### 2. WHO Global Surveillance & Monitoring System
- **What**: WHO tracks substandard/falsified medicine reports globally
- **Access**: Summary reports at `https://www.who.int/teams/regulation-prequalification/incidents-and-sf-alerts`
- **How to use**: WHO publishes alerts with country and product info. India-specific alerts feed heatmap.

#### 3. Indian State Drug Controller Data
Several states publish their own testing results:
- Karnataka FDA: `https://drugs.karnataka.gov.in`
- Maharashtra FDA: `https://fdamfg.maharashtra.gov.in`  
- Tamil Nadu: `https://www.tnhealth.tn.gov.in/drugcontrol.htm`

Parse these for state-level quality failure data.

#### 4. India Pharmacy/Hospital Location Data
For understanding normal drug distribution patterns:
- OpenStreetMap Overpass API — query all pharmacies in India:
  ```
  [out:json];node["amenity"="pharmacy"](6.5,68.0,35.5,97.5);out;
  ```
  This returns ~50,000+ pharmacy locations with lat/lng
- Jan Aushadhi store list: `https://janaushadhi.gov.in/StoreLocator.aspx`

### TIER 2 — Scrape Real Incident Reports

```python
"""
News Scraper for Indian Drug Counterfeiting Incidents

Search Google News / Times of India / Economic Times for:
  "spurious drugs seized India"
  "fake medicine India"
  "drug inspector raid"
  "CDSCO action counterfeit"

For each article, extract:
  - Date
  - City/State mentioned
  - Drug names mentioned
  - Manufacturer (if mentioned)
  - Quantity seized (if mentioned)
  
Geocode the city → lat/lng → heatmap datapoint

This gives you REAL news-based incident data that supplements CDSCO alerts.
Even 50-100 geocoded incidents make a compelling heatmap.
"""
```

---

## MODULE E: DRUG REFERENCE / IDENTITY DATA

### TIER 1 — All Real, All Free

These are reference databases for drug identity verification — the "ground truth" your system checks against.

#### Indian Drug References

| Source | URL | What You Get |
|---|---|---|
| CDSCO Approved Drugs | `https://cdscoonline.gov.in/CDSCO/Drugs` | All approved drugs in India, searchable |
| CDSCO New Drug Approvals | `https://cdsco.gov.in/opencms/opencms/en/Approval_new/Approved-New-Drugs/` | Year-wise lists (1971–present) |
| NPPA Ceiling Prices | `https://nppa.gov.in/ceiling-price` | Prices for 882+ scheduled drugs (DPCO 2013) |
| Jan Aushadhi Product List | `https://janaushadhi.gov.in/Data/PMBJP%20Product.pdf` | 2,000+ generic medicine list with MRP |
| NRCeS Drug Codes | `https://nrces.in/services/national-releases` | SNOMED CT drug identifiers for India |
| A-Z Medicine India (Kaggle) | `https://kaggle.com/datasets/shudhanshusingh/az-medicine-dataset-of-india` | Name, composition, uses, side effects |

#### US/Global Drug References

| Source | URL | What You Get |
|---|---|---|
| OpenFDA NDC | `https://api.fda.gov/drug/ndc.json` | Drug identity, ingredients, labeler |
| OpenFDA Labels | `https://api.fda.gov/drug/label.json` | Full prescribing info |
| DailyMed API | `https://dailymed.nlm.nih.gov/dailymed/services/` | SPL labels + images |
| Orange Book | `https://www.fda.gov/drugs/drug-approvals-and-databases/approved-drug-products-therapeutic-equivalence-evaluations-orange-book` | Therapeutic equivalence |
| FDA Bulk Downloads | `https://open.fda.gov/apis/drug/ndc/download/` | Entire NDC directory as JSON |

---

## COMPLETE DATA ACQUISITION SCRIPT

Run this in order. Claude Code should execute each step:

```bash
#!/bin/bash
# PharmaChain Data Acquisition Pipeline
# Run from ai-engine/ directory

echo "=== STEP 1: Create directory structure ==="
mkdir -p data/pill_images/{c3pi,rximage_scraped,roboflow,kaggle,self_collected}
mkdir -p data/supply_chain/{iot_pharma,logistics,supply_graph}
mkdir -p data/adverse_events/{faers_quarterly,openfda_cache}
mkdir -p data/india/{cdsco_alerts,cdsco_parsed,drug_reference,pharmacy_locations}
mkdir -p data/heatmap/{geocoded_incidents,news_scraped}
mkdir -p data/models

echo "=== STEP 2: Download C3PI Sample Data (493MB) ==="
cd data/pill_images/c3pi
wget -c https://data.lhncbc.nlm.nih.gov/public/Pills/sampleData.zip
unzip -o sampleData.zip
cd ../../..

echo "=== STEP 3: Clone ePillID Benchmark ==="
cd data/pill_images
git clone https://github.com/usuyama/ePillID-benchmark
cd ../..

echo "=== STEP 4: Download Kaggle Datasets ==="
# Requires: pip install kaggle, and ~/.kaggle/kaggle.json configured
kaggle datasets download -d hennryprince/iot-enabled-pharmaceutical-supply-chain -p data/supply_chain/iot_pharma --unzip
kaggle datasets download -d mohammedashraf000/pharmaceutical-supply-chain-optimization -p data/supply_chain/ --unzip
kaggle datasets download -d ziya07/smart-logistics-supply-chain-dataset -p data/supply_chain/logistics --unzip
kaggle datasets download -d trumedicines/pharmaceutical-tablets-dataset -p data/pill_images/kaggle --unzip
kaggle datasets download -d richardradli/ogyeiv2 -p data/pill_images/kaggle --unzip
kaggle datasets download -d shudhanshusingh/az-medicine-dataset-of-india -p data/india/drug_reference --unzip

echo "=== STEP 5: Clone Pill Defects & SupplyGraph ==="
cd data/pill_images
git clone https://github.com/PerceptiLabs/Pill-Defects
cd ../supply_chain
git clone https://github.com/ciol-researchlab/SupplyGraph
cd ../..

echo "=== STEP 6: Download CDSCO Alert PDFs ==="
cd data/india/cdsco_alerts
# Download monthly alerts (adjust URLs as needed — check CDSCO site for latest)
for month in "January" "February" "March" "April" "May" "June" "July" "August" "September" "October" "November" "December"; do
    wget -c "https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2018/UploadAlertsFiles/alert%20${month}-2024.pdf" 2>/dev/null || true
    wget -c "https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2018/UploadAlertsFiles/NSQ%20Alert%20For%20the%20month%20of%20${month}-2024.pdf" 2>/dev/null || true
done
cd ../../..

echo "=== STEP 7: Download FAERS Recent Quarter ==="
cd data/adverse_events/faers_quarterly
# Download most recent quarter available
wget -c "https://fis.fda.gov/content/Exports/faers_ascii_2024Q2.zip"
unzip -o faers_ascii_2024Q2.zip
cd ../../..

echo "=== STEP 8: Run scrapers ==="
python -m data.scrapers.rximage_scraper          # Scrapes pill images via API
python -m data.scrapers.cdsco_pdf_parser          # Parses CDSCO alert PDFs
python -m data.scrapers.cdsco_geocoder            # Geocodes manufacturer addresses
python -m data.scrapers.openfda_cache_builder      # Pre-caches common drug lookups

echo "=== STEP 9: Run data preparation ==="
python -m data.preparation.prepare_pill_dataset    # Organize all pill images into train/val/test
python -m data.preparation.prepare_supply_chain    # Merge Kaggle datasets + inject labeled anomalies  
python -m data.preparation.prepare_faers           # Filter FAERS for counterfeit signals
python -m data.preparation.prepare_heatmap_seed    # Combine CDSCO geocoded data into heatmap JSON

echo "=== DATA ACQUISITION COMPLETE ==="
echo "Check data/ directory for all acquired datasets"
find data/ -name "*.csv" -o -name "*.json" | head -30
```

---

## DATA PREPARATION SCRIPTS

### prepare_pill_dataset.py

```python
"""
Organize all downloaded pill images into a unified PyTorch-ready structure.

Output structure:
  data/pill_images/unified/
    train/
      authentic/     ← C3PI + Pillbox + Kaggle authentic images (80%)
      suspicious/    ← Roboflow counterfeit + augmented images (80%)
    val/
      authentic/     ← (10%)
      suspicious/    ← (10%)
    test/
      authentic/     ← (10%)
      suspicious/    ← (10%)

Steps:
1. Copy C3PI reference images → authentic/
2. Copy Kaggle tablet images → authentic/ 
3. Copy Roboflow counterfeit-labeled images → suspicious/
4. Copy Pill-Defects "defective" class → suspicious/
5. If self-collected Indian data exists in data/pill_images/self_collected/:
   - Copy originals → authentic/
   - Apply augmentation pipeline → suspicious/
6. Verify class balance. If imbalanced:
   - Undersample majority class OR
   - Apply weighted sampling in DataLoader
7. Generate split indices and save as JSON
8. Resize all images to 224x224
9. Compute dataset-specific mean/std for normalization
"""
```

### prepare_supply_chain.py

```python
"""
Merge multiple real supply chain datasets and inject labeled anomalies.

Input sources:
  - data/supply_chain/iot_pharma/ (IoT sensor data)
  - data/supply_chain/logistics/ (shipment tracking)
  - data/supply_chain/supply_graph/ (graph-structured data)

Steps:
1. Load each dataset, standardize column names
2. Compute derived features:
   - transfer_velocity_kmh (from distance + time)
   - geographic_consistency (avg consecutive distances)
   - time_patterns (hour, day_of_week, is_business_hours)
3. Label all existing data as is_anomaly=0 (real normal patterns)
4. Create anomaly copies with injected patterns:
   - 5% velocity anomalies (shrink time between distant points)
   - 3% path deviations (remove intermediate steps)
   - 2% duplicate entries (same ID, different locations, same timestamp)
5. Combine normal + anomalous, shuffle
6. Split: 70% train, 15% val, 15% test
7. Save feature matrix and labels as CSV + numpy arrays
"""
```

### prepare_faers.py

```python
"""
Process FDA FAERS quarterly data to extract counterfeit drug signals.

Input: data/adverse_events/faers_quarterly/ (unzipped ASCII files)
  - DEMO*.txt (demographics)
  - DRUG*.txt (drug info)
  - REAC*.txt (reactions)
  - OUTC*.txt (outcomes)

Steps:
1. Load and join tables on caseid
2. Filter for counterfeit-signal reactions:
   - "DRUG INEFFECTIVE"
   - "PRODUCT QUALITY ISSUE"
   - "THERAPEUTIC RESPONSE UNEXPECTED"
   - "PRODUCT CONTAMINATION"
   - "SUSPECTED COUNTERFEIT PRODUCT"
3. Compute per-drug statistics:
   - total_reports, signal_reports, signal_rate
   - baseline_rate (overall avg), signal_ratio (vs baseline)
4. Compute temporal trends:
   - Monthly report counts per drug
   - Flag drugs where signal rate increased >2x in last quarter
5. Save:
   - drug_counterfeit_signals.csv (per-drug risk summary)
   - temporal_trends.csv (monthly time series)
   - high_risk_drugs.json (drugs with signal_ratio > 2.0)
"""
```

### prepare_heatmap_seed.py

```python
"""
Build heatmap seed data from REAL sources.

Input sources (in priority order):
1. data/india/cdsco_parsed/geocoded_alerts.csv (CDSCO NSQ + spurious alerts with lat/lng)
2. data/heatmap/news_scraped/incidents.csv (scraped news articles, if available)
3. OpenStreetMap pharmacy locations (for base activity layer)

Steps:
1. Load geocoded CDSCO alerts
2. Assign intensity weights:
   - Spurious drug: intensity = 1.0 (confirmed fake)
   - NSQ drug: intensity = 0.5 (substandard)
   - Repeated offender manufacturer: intensity += 0.2 per offense
3. Apply time decay (half-life = 90 days for regulatory data — slower than scan data)
4. Run DBSCAN (eps=0.15 ≈ ~15km) on high-severity points
5. Compute cluster stats: center, radius, event_count, top_drugs, top_manufacturers
6. Load pharmacy locations as background activity layer (low intensity)
7. Save:
   - heatmap_points.json: [[lat, lng, intensity], ...]
   - clusters.json: [{center, radius, severity, events, description}, ...]
   - pharmacy_baseline.json: [[lat, lng, 0.05], ...] (background layer)
"""
```

---

## WHAT GOES SYNTHETIC (ONLY THESE)

After acquiring all real data above, generate synthetic data ONLY for:

1. **Blockchain event simulation** — You need to populate your local Hardhat node with transactions for the demo. This isn't "fake data" — it's running your real smart contracts with test addresses. Use the real CDSCO geographic data and real drug names.

2. **Future scan event stream** — For the real-time dashboard demo, you need a stream of incoming events. Generate these based on patterns learned from the real Kaggle supply chain data, not from assumptions.

3. **Data augmentation** — Standard ML augmentation (rotation, flip, jitter) for pill images to balance classes. This is standard practice, not "fake data."

That's it. Everything else should be real.

---

## QUICK REFERENCE: WHAT'S REAL vs WHAT'S GENERATED

| Data Type | Real Source | Status |
|---|---|---|
| Pill images (authentic) | NLM C3PI + Pillbox + self-photos | ✅ 100% real |
| Pill images (suspicious) | Roboflow counterfeit dataset + augmented authentic | ✅ Real labels + augmentation |
| Supply chain patterns | Kaggle IoT + Logistics datasets | ✅ 100% real |
| Supply chain anomalies | Injected into real data | ⚠️ Semi-real (real normal + injected anomaly) |
| Adverse event reports | FDA FAERS bulk download | ✅ 100% real |
| Drug identity reference | OpenFDA NDC + CDSCO + Kaggle India medicines | ✅ 100% real |
| Heatmap geographic data | CDSCO alerts geocoded | ✅ 100% real Indian data |
| Drug shortage/recall data | OpenFDA API | ✅ 100% real |
| Blockchain demo events | Local Hardhat transactions | ⚠️ Simulated but real contracts |
| Real-time scan stream | Generated from real distribution patterns | ⚠️ Synthetic, based on real patterns |
