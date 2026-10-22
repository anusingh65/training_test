#!/usr/bin/env python3
"""One-time script to enrich drug_catalog with counterfeit risk data and add new high-risk drugs."""

import json
from pathlib import Path

HUBS_PATH = Path(__file__).parent / "indian_pharma_hubs.json"

# Counterfeit risk mapping: generic name -> (risk_level, risk_factors, notes)
RISK_DATA = {
    # --- CRITICAL ---
    "Acetaminophen": ("critical", ["cdsco_nsq_flagged", "high_volume", "contamination_risk"],
        "Pan-D combo is #1 spurious drug in India per CDSCO; paracetamol syrups linked to child deaths in Gambia/Uzbekistan"),
    "Azithromycin": ("critical", ["cdsco_nsq_flagged", "high_volume", "substandard_common"],
        "Among top 5 CDSCO NSQ-flagged antibiotics; widespread substandard generics detected across India"),
    "Cefixime": ("critical", ["cdsco_nsq_flagged", "high_volume", "substandard_common"],
        "Third-gen cephalosporin frequently appears in CDSCO Not-of-Standard-Quality alerts"),
    "Artemether+Lumefantrine": ("critical", ["who_sf_category", "high_volume", "shortage_driven"],
        "WHO estimates 19.1% of antimalarials in endemic regions are substandard/falsified; critical public health impact"),
    "Sildenafil Citrate": ("critical", ["high_price_low_complexity", "export_counterfeit", "brand_targeted"],
        "ED drugs account for 80% of US border seizure value; India is primary source country for counterfeit Viagra"),
    "Tramadol HCl": ("critical", ["diversion_risk", "export_counterfeit", "high_volume"],
        "Massive illicit tramadol production in India; WHO SF alerts; INCB monitoring for diversion"),

    # --- HIGH ---
    "Amoxicillin": ("high", ["cdsco_nsq_flagged", "high_volume", "substandard_common"],
        "Common in CDSCO NSQ alerts; penicillin antibiotics frequently substandard in India"),
    "Metformin HCl": ("high", ["cdsco_nsq_flagged", "high_volume", "contamination_risk"],
        "NDMA contamination recalls globally; high-volume generic with frequent quality failures"),
    "Ciprofloxacin": ("high", ["cdsco_nsq_flagged", "high_volume", "substandard_common"],
        "Fluoroquinolone frequently flagged in CDSCO quality testing; wide generic market"),
    "Pantoprazole": ("high", ["cdsco_nsq_flagged", "spurious_declared", "high_volume"],
        "Pan-D (pantoprazole+domperidone) declared spurious by CDSCO; very high volume drug in India"),
    "Telmisartan": ("high", ["cdsco_nsq_flagged", "contamination_risk"],
        "ARB class had sartan impurity crisis (NDMA/NDEA); telmisartan frequently in quality alerts"),
    "Rosuvastatin": ("high", ["cdsco_nsq_flagged", "high_volume"],
        "High-volume statin with frequent appearance in quality failure reports"),
    "Rifampicin": ("high", ["who_sf_category", "shortage_driven", "high_volume"],
        "WHO-monitored anti-TB drug; substandard versions threaten MDR-TB control programs"),
    "Hydroxychloroquine": ("high", ["shortage_driven", "high_volume"],
        "COVID-19 panic buying created massive counterfeit market; antimalarial with pre-existing risk"),
    "Tenofovir Disoproxil": ("high", ["who_sf_category", "high_volume"],
        "Antiretroviral frequently in WHO SF alerts; critical HIV treatment with counterfeit risk in Africa"),
    "Domperidone": ("high", ["cdsco_nsq_flagged", "spurious_declared"],
        "Part of Pan-D combination; domperidone-containing products frequently flagged"),
    "Norfloxacin": ("high", ["cdsco_nsq_flagged", "substandard_common"],
        "Older fluoroquinolone with high generic penetration; quality failures documented"),

    # --- MEDIUM ---
    "Atorvastatin": ("medium", ["high_volume"], "High-volume statin; moderate quality failure rate"),
    "Omeprazole": ("medium", ["high_volume"], "Common PPI with moderate counterfeit risk"),
    "Ibuprofen": ("medium", ["high_volume"], "High-volume OTC analgesic; moderate quality variation"),
    "Losartan Potassium": ("medium", ["contamination_risk"], "ARB class affected by sartan impurity recalls"),
    "Amlodipine": ("medium", ["high_volume"], "Very high prescription volume in India; moderate risk"),
    "Cetirizine HCl": ("medium", ["high_volume"], "OTC antihistamine; counterfeiting driven by volume"),
    "Clopidogrel": ("medium", ["brand_targeted"], "Brand-name premium creates counterfeiting incentive"),
    "Glimepiride": ("medium", ["high_volume"], "Common sulfonylurea; moderate quality risk"),
    "Montelukast": ("medium", ["high_volume"], "High prescription volume; some quality alerts"),
    "Doxycycline": ("medium", ["high_volume", "substandard_common"], "Tetracycline antibiotic with moderate risk"),
    "Levofloxacin": ("medium", ["cdsco_nsq_flagged"], "Fluoroquinolone occasionally in quality alerts"),
    "Metoprolol": ("medium", ["high_volume"], "Common beta-blocker; moderate quality risk"),
    "Diclofenac Sodium": ("medium", ["high_volume"], "Very common NSAID in India; quality varies"),
    "Gabapentin": ("medium", ["diversion_risk"], "Increasing recreational misuse; some diversion risk"),
    "Pregabalin": ("medium", ["diversion_risk"], "Growing misuse concern; moderate counterfeit risk"),
    "Isoniazid": ("medium", ["who_sf_category"], "Anti-TB drug monitored by WHO; less counterfeited than rifampicin"),
    "Ethambutol": ("medium", ["who_sf_category"], "Anti-TB drug in WHO monitoring; moderate risk"),
    "Warfarin Sodium": ("medium", ["contamination_risk"], "Narrow therapeutic index; quality critical"),
    "Phenytoin Sodium": ("medium", ["contamination_risk"], "Narrow therapeutic index anticonvulsant"),
    "Acyclovir": ("medium", ["high_volume"], "Common antiviral; moderate counterfeit risk"),
    "Ofloxacin": ("medium", ["cdsco_nsq_flagged"], "Fluoroquinolone in quality alerts occasionally"),
    "Metronidazole": ("medium", ["high_volume", "substandard_common"], "Very common antibiotic; quality varies"),
    "Clindamycin": ("medium", ["high_volume"], "Moderate risk; some quality variation"),
    "Pioglitazone": ("medium", ["contamination_risk"], "Thiazolidinedione with contamination history"),
    "Sitagliptin": ("medium", ["high_price_low_complexity", "brand_targeted"], "Expensive DPP-4 inhibitor; brand premium incentivizes counterfeiting"),
    "Empagliflozin": ("medium", ["high_price_low_complexity", "brand_targeted"], "Expensive SGLT2 inhibitor; newer drug with premium pricing"),
    "Tamsulosin HCl": ("medium", ["high_volume"], "Common urology drug; moderate risk"),
    "Ondansetron": ("medium", ["high_volume"], "Common antiemetic; moderate risk"),

    # --- LOW ---
    "Ranitidine HCl": ("low", ["contamination_risk"], "Largely withdrawn due to NDMA; remaining stocks at risk"),
    "Aspirin": ("low", [], "Low-value OTC; limited counterfeiting incentive"),
    "Oral Rehydration Salts": ("low", [], "Very low value; minimal counterfeiting incentive"),
    "Zinc Sulphate": ("low", [], "Low-value supplement; minimal risk"),
    "Ferrous Sulphate+Folic Acid": ("low", [], "Low-cost government-distributed supplement"),
    "Cholecalciferol": ("low", [], "Vitamin D supplement; minimal counterfeiting"),
    "Enalapril Maleate": ("low", ["high_volume"], "Older ACE inhibitor; lower market share now"),
    "Albendazole": ("low", [], "Very cheap anthelmintic; minimal incentive"),
    "Salbutamol": ("low", [], "Inhaler; device complexity reduces counterfeiting"),
    "Budesonide": ("low", [], "Inhaler; device complexity reduces counterfeiting"),
    "Prednisolone": ("low", [], "Low-cost corticosteroid; minimal counterfeiting"),
    "Dexamethasone": ("low", [], "Low-cost corticosteroid; minimal counterfeiting"),
    "Fluconazole": ("low", [], "Common cheap antifungal; low incentive"),
    "Levothyroxine": ("low", ["contamination_risk"], "Low value but narrow therapeutic index"),
    "Insulin Glargine": ("low", ["cold_chain_vulnerable"], "Cold-chain biologic; complex to counterfeit but storage issues"),
    "Insulin Human": ("low", ["cold_chain_vulnerable"], "Cold-chain; hard to counterfeit but storage-sensitive"),
}

# New drugs to add
NEW_DRUGS = [
    # Cough syrups - critical (300+ child deaths)
    {"name": "Promethazine Syrup 5mg/5ml",   "generic": "Promethazine",         "category": "cough_syrup",     "form": "syrup",     "shelf_life_months": 24, "mrp": 55.00,  "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["contamination_risk", "child_deaths", "export_counterfeit", "cdsco_nsq_flagged"],
     "counterfeit_notes": "Contaminated cough syrups caused 300+ child deaths in Gambia, Uzbekistan, Cameroon; DEG/EG contamination from Indian manufacturers"},
    {"name": "Dextromethorphan Syrup 10mg/5ml","generic": "Dextromethorphan",    "category": "cough_syrup",     "form": "syrup",     "shelf_life_months": 24, "mrp": 65.00,  "schedule": "OTC",
     "counterfeit_risk": "critical", "risk_factors": ["contamination_risk", "child_deaths", "export_counterfeit"],
     "counterfeit_notes": "Multiple Indian-origin cough syrups recalled worldwide for diethylene glycol contamination"},
    {"name": "Codeine Phosphate Syrup 10mg/5ml","generic": "Codeine Phosphate", "category": "cough_syrup",     "form": "syrup",     "shelf_life_months": 24, "mrp": 80.00,  "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["diversion_risk", "contamination_risk", "child_deaths"],
     "counterfeit_notes": "Codeine-containing cough syrups major diversion target; implicated in contamination deaths"},

    # Oncology drugs - critical
    {"name": "Imatinib 400mg",               "generic": "Imatinib Mesylate",    "category": "oncology",        "form": "tablet",    "shelf_life_months": 36, "mrp": 850.00, "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["high_price_low_complexity", "brand_targeted", "shortage_driven"],
     "counterfeit_notes": "CML treatment; Gleevec counterfeits widespread in developing countries; massive price differential drives counterfeiting"},
    {"name": "Capecitabine 500mg",           "generic": "Capecitabine",         "category": "oncology",        "form": "tablet",    "shelf_life_months": 24, "mrp": 780.00, "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["high_price_low_complexity", "shortage_driven"],
     "counterfeit_notes": "Oral chemotherapy; fake capecitabine seized in India containing no active ingredient"},
    {"name": "Bevacizumab 100mg/4ml",        "generic": "Bevacizumab",          "category": "oncology",        "form": "injection", "shelf_life_months": 24, "mrp": 22000.00,"schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["high_price_low_complexity", "cold_chain_vulnerable", "brand_targeted"],
     "counterfeit_notes": "Avastin counterfeits (starch+salt water) detected worldwide; very high value target"},
    {"name": "Trastuzumab 440mg",            "generic": "Trastuzumab",          "category": "oncology",        "form": "injection", "shelf_life_months": 24, "mrp": 75000.00,"schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["high_price_low_complexity", "cold_chain_vulnerable", "brand_targeted"],
     "counterfeit_notes": "Herceptin: among most counterfeited cancer drugs globally due to extreme price"},
    {"name": "Paclitaxel 260mg",             "generic": "Paclitaxel",           "category": "oncology",        "form": "injection", "shelf_life_months": 18, "mrp": 8500.00, "schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["high_price_low_complexity", "shortage_driven"],
     "counterfeit_notes": "Taxane chemotherapy; price creates counterfeiting incentive in cancer treatment"},
    {"name": "Pembrolizumab 100mg/4ml",      "generic": "Pembrolizumab",        "category": "oncology",        "form": "injection", "shelf_life_months": 24, "mrp": 315000.00,"schedule":"H",
     "counterfeit_risk": "high", "risk_factors": ["high_price_low_complexity", "cold_chain_vulnerable", "brand_targeted"],
     "counterfeit_notes": "Keytruda: extremely expensive immunotherapy; counterfeiting emerging as biosimilars not yet available everywhere"},

    # COVID antivirals
    {"name": "Remdesivir 100mg",             "generic": "Remdesivir",           "category": "antiviral",       "form": "injection", "shelf_life_months": 24, "mrp": 2500.00, "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["shortage_driven", "high_price_low_complexity"],
     "counterfeit_notes": "Massive counterfeit wave during COVID-19 Delta wave in India; fake remdesivir with no active ingredient sold at 10x markup"},
    {"name": "Favipiravir 200mg",            "generic": "Favipiravir",          "category": "antiviral",       "form": "tablet",    "shelf_life_months": 24, "mrp": 75.00,  "schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["shortage_driven"],
     "counterfeit_notes": "COVID antiviral; shortage-driven counterfeiting during pandemic waves in India"},
    {"name": "Molnupiravir 200mg",           "generic": "Molnupiravir",         "category": "antiviral",       "form": "capsule",   "shelf_life_months": 24, "mrp": 65.00,  "schedule": "H",
     "counterfeit_risk": "medium", "risk_factors": ["shortage_driven"],
     "counterfeit_notes": "COVID antiviral with moderate counterfeiting risk; Indian generics reduced price differential"},

    # GLP-1 agonists - critical (currently most counterfeited drug class globally)
    {"name": "Semaglutide 1mg Pen",          "generic": "Semaglutide",          "category": "glp1_agonist",    "form": "injection", "shelf_life_months": 24, "mrp": 8500.00, "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["high_price_low_complexity", "shortage_driven", "brand_targeted", "cold_chain_vulnerable"],
     "counterfeit_notes": "Ozempic/Wegovy: #1 most counterfeited drug globally in 2024-25; WHO alerts; fake pens with insulin/water found worldwide"},
    {"name": "Liraglutide 6mg/ml Pen",       "generic": "Liraglutide",          "category": "glp1_agonist",    "form": "injection", "shelf_life_months": 24, "mrp": 7200.00, "schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["high_price_low_complexity", "shortage_driven", "brand_targeted", "cold_chain_vulnerable"],
     "counterfeit_notes": "Victoza/Saxenda: GLP-1 agonist with high counterfeiting due to weight-loss demand and supply shortages"},

    # ED drugs - additional
    {"name": "Tadalafil 20mg",               "generic": "Tadalafil",            "category": "pde5_inhibitor",  "form": "tablet",    "shelf_life_months": 36, "mrp": 120.00, "schedule": "H",
     "counterfeit_risk": "critical", "risk_factors": ["high_price_low_complexity", "export_counterfeit", "brand_targeted"],
     "counterfeit_notes": "Cialis counterfeits found with heavy metals, printer ink; high-value target alongside sildenafil"},

    # Maternal health
    {"name": "Oxytocin 5IU/ml",              "generic": "Oxytocin",             "category": "maternal_health", "form": "injection", "shelf_life_months": 24, "mrp": 18.00,  "schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["cold_chain_vulnerable", "who_sf_category"],
     "counterfeit_notes": "WHO priority; degraded/substandard oxytocin causes maternal deaths; cold chain failures in India common"},
    {"name": "Misoprostol 200mcg",           "generic": "Misoprostol",          "category": "maternal_health", "form": "tablet",    "shelf_life_months": 24, "mrp": 25.00,  "schedule": "H",
     "counterfeit_risk": "medium", "risk_factors": ["who_sf_category", "diversion_risk"],
     "counterfeit_notes": "WHO essential medicine; quality issues documented in LMICs; diversion for unapproved uses"},

    # Biologics
    {"name": "Erythropoietin 4000IU",        "generic": "Epoetin Alfa",         "category": "biologic",        "form": "injection", "shelf_life_months": 24, "mrp": 650.00, "schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["cold_chain_vulnerable", "high_price_low_complexity"],
     "counterfeit_notes": "Biologic with complex manufacturing; substandard EPO with wrong potency detected in developing markets"},
    {"name": "Rituximab 500mg/50ml",         "generic": "Rituximab",            "category": "biologic",        "form": "injection", "shelf_life_months": 24, "mrp": 25000.00,"schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["high_price_low_complexity", "cold_chain_vulnerable", "brand_targeted"],
     "counterfeit_notes": "MabThera/Rituxan counterfeits seized; extremely high value biologic"},
    {"name": "Adalimumab 40mg",              "generic": "Adalimumab",           "category": "biologic",        "form": "injection", "shelf_life_months": 24, "mrp": 15000.00,"schedule": "H",
     "counterfeit_risk": "high", "risk_factors": ["high_price_low_complexity", "cold_chain_vulnerable", "brand_targeted"],
     "counterfeit_notes": "Humira: one of highest-revenue drugs globally; biosimilar market complexity creates counterfeiting opportunities"},

    # Controlled substances
    {"name": "Alprazolam 0.5mg",             "generic": "Alprazolam",           "category": "controlled",      "form": "tablet",    "shelf_life_months": 36, "mrp": 30.00,  "schedule": "X",
     "counterfeit_risk": "high", "risk_factors": ["diversion_risk", "high_volume"],
     "counterfeit_notes": "Benzodiazepine with major diversion and counterfeit market; pressed pills with fentanyl found globally"},
    {"name": "Clonazepam 0.5mg",             "generic": "Clonazepam",           "category": "controlled",      "form": "tablet",    "shelf_life_months": 36, "mrp": 25.00,  "schedule": "X",
     "counterfeit_risk": "high", "risk_factors": ["diversion_risk"],
     "counterfeit_notes": "Benzodiazepine with significant diversion risk; counterfeits circulate in grey market"},
    {"name": "Buprenorphine 8mg",            "generic": "Buprenorphine",        "category": "controlled",      "form": "tablet",    "shelf_life_months": 36, "mrp": 180.00, "schedule": "X",
     "counterfeit_risk": "medium", "risk_factors": ["diversion_risk"],
     "counterfeit_notes": "Opioid substitution therapy; some diversion risk but lower counterfeiting than full agonists"},

    # Paracetamol syrup specifically (different from tablet)
    {"name": "Paracetamol Syrup 120mg/5ml",  "generic": "Acetaminophen",        "category": "analgesic",       "form": "syrup",     "shelf_life_months": 24, "mrp": 35.00,  "schedule": "OTC",
     "counterfeit_risk": "critical", "risk_factors": ["contamination_risk", "child_deaths", "export_counterfeit", "cdsco_nsq_flagged"],
     "counterfeit_notes": "Paracetamol syrups from India caused 70+ child deaths in Gambia (2022); DEG/EG contamination; WHO alert issued"},
]


def enrich():
    data = json.loads(HUBS_PATH.read_text())
    catalog = data["drug_catalog"]

    # Enrich existing drugs
    enriched = 0
    for drug in catalog:
        generic = drug["generic"]
        if generic in RISK_DATA:
            risk, factors, notes = RISK_DATA[generic]
            drug["counterfeit_risk"] = risk
            drug["risk_factors"] = factors
            drug["counterfeit_notes"] = notes
            enriched += 1
        else:
            # Default: low risk with no specific factors
            drug["counterfeit_risk"] = "low"
            drug["risk_factors"] = []
            drug["counterfeit_notes"] = ""

    # Add new drugs
    existing_names = {d["name"] for d in catalog}
    added = 0
    for new_drug in NEW_DRUGS:
        if new_drug["name"] not in existing_names:
            catalog.append(new_drug)
            added += 1

    data["drug_catalog"] = catalog
    HUBS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Enriched {enriched} existing drugs, added {added} new drugs. Total catalog: {len(catalog)}")

    # Summary stats
    risk_counts = {}
    for d in catalog:
        r = d.get("counterfeit_risk", "unknown")
        risk_counts[r] = risk_counts.get(r, 0) + 1
    print(f"Risk distribution: {risk_counts}")

    categories = set(d["category"] for d in catalog)
    print(f"Categories ({len(categories)}): {sorted(categories)}")


if __name__ == "__main__":
    enrich()
