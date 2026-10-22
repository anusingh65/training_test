"""
India-specific seasonal, temporal, and demand patterns for pharmaceutical supply chains.

Provides comprehensive reference data for generating realistic synthetic data
in MediChain's counterfeit drug detection system.  Every multiplier, date range,
and risk factor is grounded in published epidemiological, commercial, and
logistics data for the Indian pharmaceutical sector.

Data structures
---------------
- ``SEASONAL_DEMAND_PATTERNS``   -- month-by-month demand multipliers and drivers
- ``FESTIVAL_EVENT_CALENDAR``    -- all major Indian events affecting pharma supply
- ``DISEASE_OUTBREAK_PATTERNS``  -- India-specific disease seasonality
- ``SUPPLY_CHAIN_DISRUPTIONS``   -- weather, logistics, and geopolitical disruptions
- ``OPERATING_HOUR_PATTERNS``    -- realistic activity-hour distributions
- ``DRUG_CATEGORY_SEASONALITY``  -- per-category monthly demand curves

Sources
-------
- CDSCO public alerts and NSQ database
- NCVBDC (National Center for Vector Borne Diseases Control) India
- IDSP (Integrated Disease Surveillance Programme) weekly reports
- IMD (India Meteorological Department) seasonal forecasts
- IPA (Indian Pharmaceutical Alliance) supply-chain reports
- Business Standard pharma sales data (Pharmarack / IQVIA)
- WHO Substandard/Falsified medical products alerts
- Published literature on TB, dengue, malaria seasonality in India

Usage
-----
    from data.synthetic.india_seasonal_patterns import (
        SEASONAL_DEMAND_PATTERNS,
        FESTIVAL_EVENT_CALENDAR,
        DISEASE_OUTBREAK_PATTERNS,
        SUPPLY_CHAIN_DISRUPTIONS,
        OPERATING_HOUR_PATTERNS,
        DRUG_CATEGORY_SEASONALITY,
    )
"""

from __future__ import annotations

# ============================================================================
#  1. SEASONAL DEMAND PATTERNS  (month-by-month)
# ============================================================================

SEASONAL_DEMAND_PATTERNS: dict = {
    1: {
        "month_name": "January",
        "overall_demand_multiplier": 0.95,
        "key_drivers": [
            "Post-holiday normalization",
            "Winter peak: respiratory infections (cold, flu, asthma)",
            "Poor air quality in North India (Delhi NCR, Punjab, UP)",
            "Republic Day holiday (26 Jan) causes minor distribution pause",
        ],
        "spike_categories": [
            "antiasthmatic", "bronchodilator", "cough_syrup",
            "antibiotic", "antihistamine", "corticosteroid",
        ],
        "dip_categories": [
            "antimalarial", "rehydration",
        ],
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Respiratory drug sales remain elevated from Nov-Dec peak. "
                 "Fog-related transport delays in North India (Punjab, Haryana, UP) "
                 "can create localized supply gaps.",
    },
    2: {
        "month_name": "February",
        "overall_demand_multiplier": 0.92,
        "key_drivers": [
            "Tail end of winter respiratory season",
            "Financial year planning (companies adjust inventory)",
            "Low disease burden -- inter-seasonal trough",
            "Wedding season begins (North India)",
        ],
        "spike_categories": [
            "antiasthmatic", "bronchodilator", "cough_syrup",
        ],
        "dip_categories": [
            "antimalarial", "rehydration", "antifungal",
        ],
        "counterfeit_risk_multiplier": 0.9,
        "notes": "Lowest overall disease burden month. Respiratory sales tapering. "
                 "Pharmaceutical companies begin Q4 (Jan-Mar) inventory push.",
    },
    3: {
        "month_name": "March",
        "overall_demand_multiplier": 1.10,
        "key_drivers": [
            "Financial year-end (31 Mar) -- bulk purchasing, channel loading",
            "Holi festival -- distribution slowdown for 2-3 days",
            "Ramadan begins (variable) -- demand pattern shifts",
            "Temperature rise -- early summer illnesses begin",
            "TB diagnosis peak (April-June cases developing now)",
        ],
        "spike_categories": [
            "analgesic", "rehydration", "antidiabetic",
            "antihypertensive", "statin",
        ],
        "dip_categories": [
            "antimalarial",
        ],
        "counterfeit_risk_multiplier": 1.15,
        "notes": "Financial year-end drives bulk procurement at all levels. "
                 "Channel loading means distributors stock heavily -- reduced "
                 "scrutiny on incoming goods creates counterfeiting opportunity. "
                 "Holi disrupts North India distribution for 2-3 days.",
    },
    4: {
        "month_name": "April",
        "overall_demand_multiplier": 1.05,
        "key_drivers": [
            "New financial year begins -- fresh budgets, tender procurement",
            "Summer heat intensifies -- heat stroke, dehydration",
            "TB notifications peak (April-June) in North India",
            "Government hospital restocking (annual tenders)",
            "School holidays begin -- family travel increases exposure",
        ],
        "spike_categories": [
            "rehydration", "analgesic", "anti_tb",
            "supplement", "antidiabetic",
        ],
        "dip_categories": [
            "cough_syrup", "antiasthmatic",
        ],
        "counterfeit_risk_multiplier": 1.05,
        "notes": "Government procurement cycle creates surge in institutional "
                 "demand. Tender-based procurement at scale can miss quality "
                 "checks. ORS and electrolyte demand rising with temperatures.",
    },
    5: {
        "month_name": "May",
        "overall_demand_multiplier": 1.08,
        "key_drivers": [
            "Peak summer -- heatwaves across Rajasthan, Gujarat, central India",
            "Gastroenteritis and food poisoning spike from contaminated food/water",
            "Anti-infective drug sales surge (fever season onset)",
            "Pre-monsoon disease buildup: early P. vivax malaria cases",
            "School holidays -- reduced institutional demand for pediatrics",
        ],
        "spike_categories": [
            "rehydration", "antibiotic", "analgesic",
            "antifungal", "antidiabetic",
        ],
        "dip_categories": [
            "cough_syrup", "bronchodilator",
        ],
        "counterfeit_risk_multiplier": 1.1,
        "notes": "Anti-infective segment starts strong growth. "
                 "Antibacterial sales historically jump 9-10% in May. "
                 "Heat-related emergencies drive ORS demand in rural areas.",
    },
    6: {
        "month_name": "June",
        "overall_demand_multiplier": 1.20,
        "key_drivers": [
            "Monsoon onset (Kerala: Jun 1, reaching North India by late June)",
            "Water-borne diseases begin: typhoid, cholera, hepatitis A",
            "Vector-borne diseases rising: malaria mosquitoes breeding",
            "Skin infections (fungal) from humidity",
            "Leptospirosis risk in flood-prone areas",
        ],
        "spike_categories": [
            "antibiotic", "antimalarial", "antifungal",
            "rehydration", "analgesic", "antihistamine",
        ],
        "dip_categories": [
            "cough_syrup",
        ],
        "counterfeit_risk_multiplier": 1.2,
        "notes": "Monsoon onset is the sharpest demand inflection point. "
                 "Anti-infective sales grow 15-17% YoY. Acute therapy demand "
                 "surges. Early monsoon flooding can disrupt last-mile delivery.",
    },
    7: {
        "month_name": "July",
        "overall_demand_multiplier": 1.30,
        "key_drivers": [
            "Full monsoon -- peak rainfall across most of India",
            "Malaria season in full swing (P. vivax peaking)",
            "Dengue vectors breeding -- early cases appearing",
            "Water-borne disease burden: typhoid, cholera at peak",
            "Flooding disrupts transport in Assam, Bihar, Mumbai, Kerala",
            "Leptospirosis cases spike in Mumbai and Kerala",
        ],
        "spike_categories": [
            "antimalarial", "antibiotic", "rehydration",
            "analgesic", "antifungal", "antihistamine",
        ],
        "dip_categories": [],
        "counterfeit_risk_multiplier": 1.35,
        "notes": "Peak monsoon month. Transport delays up to 40% in flood zones. "
                 "Supply shortages from logistics disruption create prime "
                 "conditions for counterfeit injection. Antimalarial demand "
                 "can exceed supply in endemic northeastern states.",
    },
    8: {
        "month_name": "August",
        "overall_demand_multiplier": 1.35,
        "key_drivers": [
            "Peak malaria transmission (SAF = 3.14 for August)",
            "Dengue cases accelerating rapidly",
            "Japanese Encephalitis peak in eastern UP, Bihar, Assam",
            "Chikungunya cases rising",
            "Independence Day (15 Aug) -- minor distribution pause",
            "Ganesh Chaturthi (late Aug) -- Maharashtra demand surge",
            "Onam festival (Kerala) -- regional demand spike",
            "Flooding continues -- Assam, Bihar, West Bengal",
        ],
        "spike_categories": [
            "antimalarial", "antibiotic", "analgesic",
            "rehydration", "antifungal", "antiplatelet",
        ],
        "dip_categories": [],
        "counterfeit_risk_multiplier": 1.4,
        "notes": "Highest overall disease burden month. Malaria + dengue + JE "
                 "triple threat in eastern India. Paracetamol demand surges "
                 "for dengue symptomatic treatment. Counterfeit paracetamol "
                 "and antimalarials historically spike during this period.",
    },
    9: {
        "month_name": "September",
        "overall_demand_multiplier": 1.30,
        "key_drivers": [
            "Dengue peaks (September-October highest caseload)",
            "Malaria still high (P. falciparum now dominating)",
            "Chikungunya peak transmission",
            "Navratri / Durga Puja festival preparations",
            "Post-monsoon waterlogging sustains disease burden",
            "Scrub typhus season begins (post-rainy)",
        ],
        "spike_categories": [
            "analgesic", "antimalarial", "antibiotic",
            "antiplatelet", "rehydration",
        ],
        "dip_categories": [],
        "counterfeit_risk_multiplier": 1.35,
        "notes": "Dengue panic buying drives paracetamol demand 1.5x above baseline. "
                 "Festival pre-stocking begins for Oct-Nov season. P. falciparum "
                 "malaria peaks now through November, requiring artemisinin "
                 "combination therapy.",
    },
    10: {
        "month_name": "October",
        "overall_demand_multiplier": 1.25,
        "key_drivers": [
            "Peak dengue month (October has highest case counts nationally)",
            "Navratri and Dussehra -- distribution disruptions",
            "Pre-Diwali inventory buildup (massive channel loading)",
            "Transition from monsoon to winter disease patterns",
            "Respiratory season beginning (pollution + weather shift)",
            "P. falciparum malaria remains elevated",
        ],
        "spike_categories": [
            "analgesic", "antiplatelet", "antibiotic",
            "antiasthmatic", "cough_syrup", "bronchodilator",
        ],
        "dip_categories": [
            "rehydration",
        ],
        "counterfeit_risk_multiplier": 1.3,
        "notes": "Dual-burden month: monsoon diseases declining while winter "
                 "respiratory diseases start rising. Pre-Diwali bulk purchasing "
                 "across all categories. Distributors under pressure to stock up "
                 "means reduced quality oversight.",
    },
    11: {
        "month_name": "November",
        "overall_demand_multiplier": 1.15,
        "key_drivers": [
            "Diwali festival (Oct-Nov) -- peak retail sales period",
            "Respiratory drug sales surge 66% from monsoon trough",
            "Dengue tail (declining but still significant)",
            "Pollution season peak (Delhi NCR, Indo-Gangetic plain)",
            "Winter onset in North India -- cold/flu cases rising",
            "Post-Diwali distribution normalization",
        ],
        "spike_categories": [
            "antiasthmatic", "bronchodilator", "cough_syrup",
            "antihistamine", "corticosteroid", "analgesic",
        ],
        "dip_categories": [
            "antimalarial", "rehydration", "antifungal",
        ],
        "counterfeit_risk_multiplier": 1.2,
        "notes": "Respiratory segment contributes ~8% of total IPM revenue and "
                 "shows 14% YoY growth in Oct-Dec quarter. Anti-asthma/COPD sales "
                 "reach ~Rs 3,500 crore in Q3. Cough and cold segment grows 11.3%.",
    },
    12: {
        "month_name": "December",
        "overall_demand_multiplier": 1.00,
        "key_drivers": [
            "Peak winter respiratory season continues",
            "Christmas / New Year -- distribution slow period (last 2 weeks)",
            "Influenza / H1N1 cases peak in some years",
            "North India fog severely impacts road and rail transport",
            "Year-end inventory adjustments",
        ],
        "spike_categories": [
            "antiasthmatic", "bronchodilator", "cough_syrup",
            "antibiotic", "antihistamine", "corticosteroid",
        ],
        "dip_categories": [
            "antimalarial", "rehydration", "antifungal",
        ],
        "counterfeit_risk_multiplier": 1.05,
        "notes": "Respiratory drug sales peaked at Rs 1,638 crore in November "
                 "and remain elevated through December. Dense fog in North India "
                 "(visibility < 100m) causes 2-5 day transport delays. "
                 "Year-end holiday period creates distribution slowdown.",
    },
}


# ============================================================================
#  2. FESTIVAL / EVENT CALENDAR
# ============================================================================

FESTIVAL_EVENT_CALENDAR: list[dict] = [
    # --- JANUARY ---
    {
        "name": "Lohri",
        "typical_month": 1,
        "typical_day_range": [13, 13],
        "duration_days": 1,
        "demand_multiplier": 1.02,
        "affected_categories": [],
        "affected_regions": ["Punjab", "Haryana", "Delhi", "Himachal Pradesh"],
        "supply_chain_impact": "Minor; limited to Punjab/Haryana region",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Regional North India celebration; minimal pharma supply chain impact",
    },
    {
        "name": "Makar Sankranti / Pongal",
        "typical_month": 1,
        "typical_day_range": [14, 16],
        "duration_days": 3,
        "demand_multiplier": 1.05,
        "affected_categories": [],
        "affected_regions": ["Tamil Nadu", "Karnataka", "Andhra Pradesh", "Telangana",
                             "Gujarat", "Maharashtra", "Rajasthan"],
        "supply_chain_impact": "Regional holiday; South India distribution pause for 1-2 days",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Pongal is 4-day holiday in Tamil Nadu. Makar Sankranti celebrated "
                 "across western and southern India.",
    },
    {
        "name": "Republic Day",
        "typical_month": 1,
        "typical_day_range": [26, 26],
        "duration_days": 1,
        "demand_multiplier": 1.0,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "National holiday; government offices, banks closed. "
                               "Security restrictions in Delhi affect local logistics.",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Single-day national holiday; minimal pharma impact.",
    },

    # --- FEBRUARY ---
    {
        "name": "Maha Shivaratri",
        "typical_month": 2,
        "typical_day_range": [20, 28],
        "duration_days": 1,
        "demand_multiplier": 1.0,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "Minor; single day holiday",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "National holiday but limited supply chain impact.",
    },

    # --- MARCH ---
    {
        "name": "Holi",
        "typical_month": 3,
        "typical_day_range": [10, 25],
        "duration_days": 2,
        "demand_multiplier": 1.08,
        "affected_categories": ["analgesic", "antihistamine", "antifungal"],
        "affected_regions": ["all"],
        "supply_chain_impact": "North India distribution shutdown for 2-3 days. "
                               "Pre-stocking 1 week before. Skin allergies from "
                               "chemical colors drive dermatology drug demand.",
        "counterfeit_risk_multiplier": 1.1,
        "notes": "Chemical colors cause allergic reactions, driving demand for "
                 "antihistamines and topical steroids. North India logistics "
                 "paralyzed for 2-3 days.",
    },
    {
        "name": "Financial Year End",
        "typical_month": 3,
        "typical_day_range": [20, 31],
        "duration_days": 12,
        "demand_multiplier": 1.20,
        "affected_categories": ["all"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Massive channel loading. Distributors push stock to "
                               "meet annual targets. Bulk purchasing with reduced "
                               "per-unit scrutiny. Banks close 31 Mar.",
        "counterfeit_risk_multiplier": 1.25,
        "notes": "Single biggest commercial event for Indian pharma supply chain. "
                 "Companies push 15-20% of annual volume in March. Target-chasing "
                 "at distributor level means quality checks are rushed. "
                 "Historically highest window for counterfeit infiltration.",
    },
    {
        "name": "Ramadan (Start)",
        "typical_month": 3,
        "typical_day_range": [1, 5],
        "duration_days": 30,
        "demand_multiplier": 1.05,
        "affected_categories": ["antacid", "antidiabetic", "analgesic"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Muslim-majority areas see demand shift for antacids, "
                               "anti-diabetics (fasting management). Distribution "
                               "timing shifts in some areas. Reduced working hours "
                               "for Muslim-owned distribution firms.",
        "counterfeit_risk_multiplier": 1.05,
        "notes": "Dates shift ~11 days earlier each year (lunar calendar). "
                 "Fasting-related GI complaints drive antacid demand. "
                 "Diabetics adjusting insulin/OHA timing increases pharmacy visits. "
                 "2025: Ramadan started ~March 1.",
    },

    # --- APRIL ---
    {
        "name": "Eid al-Fitr",
        "typical_month": 3,
        "typical_day_range": [29, 31],
        "duration_days": 3,
        "demand_multiplier": 1.08,
        "affected_categories": ["antacid", "analgesic", "antidiabetic"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Distribution pause in Muslim-majority areas for 2-3 days. "
                               "Pre-Eid stocking. Feast-related GI complaints post-Eid.",
        "counterfeit_risk_multiplier": 1.05,
        "notes": "2025: Eid expected March 31. End of Ramadan fasting. "
                 "Post-Eid GI complaints from rich food common.",
    },
    {
        "name": "Ram Navami / Chaitra Navratri",
        "typical_month": 4,
        "typical_day_range": [1, 8],
        "duration_days": 9,
        "demand_multiplier": 1.03,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "Minor; intermittent fasting may affect diabetic drug demand",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Nine-day festival; mostly celebrated domestically with minimal "
                 "commercial supply chain disruption.",
    },
    {
        "name": "Baisakhi / Tamil New Year / Vishu",
        "typical_month": 4,
        "typical_day_range": [13, 15],
        "duration_days": 1,
        "demand_multiplier": 1.03,
        "affected_categories": [],
        "affected_regions": ["Punjab", "Tamil Nadu", "Kerala", "Assam"],
        "supply_chain_impact": "Regional harvest festival; minor distribution pause "
                               "in Punjab and South India",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Multiple regional New Year celebrations across India. "
                 "Assam: Rongali Bihu (3 days). Tamil Nadu: Puthandu.",
    },

    # --- MAY ---
    {
        "name": "Buddha Purnima",
        "typical_month": 5,
        "typical_day_range": [10, 15],
        "duration_days": 1,
        "demand_multiplier": 1.0,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "National holiday; single day off",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Minimal pharma supply chain impact.",
    },
    {
        "name": "Summer Holidays (Schools)",
        "typical_month": 5,
        "typical_day_range": [1, 31],
        "duration_days": 45,
        "demand_multiplier": 1.05,
        "affected_categories": ["rehydration", "analgesic", "supplement"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Travel increases disease exposure. Rural-to-urban "
                               "patient migration for elective procedures. "
                               "Reduced pediatric institutional demand.",
        "counterfeit_risk_multiplier": 1.05,
        "notes": "Peak travel season increases exposure to water/food-borne disease. "
                 "Pilgrimage season (Char Dham, Amarnath) begins.",
    },

    # --- JUNE ---
    {
        "name": "Eid al-Adha (Bakrid)",
        "typical_month": 6,
        "typical_day_range": [6, 8],
        "duration_days": 3,
        "demand_multiplier": 1.05,
        "affected_categories": ["analgesic", "antibiotic"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Muslim-majority area distribution pause for 1-2 days",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "2025: Expected around June 7. Dates shift annually (lunar calendar). "
                 "Meat consumption spike can increase food-borne illness.",
    },
    {
        "name": "Monsoon Onset (Kerala)",
        "typical_month": 6,
        "typical_day_range": [1, 5],
        "duration_days": 7,
        "demand_multiplier": 1.15,
        "affected_categories": ["antimalarial", "antibiotic", "antifungal",
                                "rehydration", "analgesic"],
        "affected_regions": ["Kerala", "Karnataka", "Goa", "Maharashtra"],
        "supply_chain_impact": "Southwest monsoon hits Kerala coast ~June 1. "
                               "Heavy rainfall disrupts coastal and Western Ghats "
                               "transport. 15-25% increase in transit times.",
        "counterfeit_risk_multiplier": 1.15,
        "notes": "The monsoon onset is the single biggest seasonal demand trigger "
                 "for the Indian pharma market. Anti-infective category grows "
                 "15-17% in the monsoon quarter.",
    },

    # --- JULY ---
    {
        "name": "Muharram",
        "typical_month": 7,
        "typical_day_range": [5, 7],
        "duration_days": 1,
        "demand_multiplier": 1.0,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "National holiday; single day off",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "2025: Expected around July 6. Dates shift annually (lunar). "
                 "Minor supply chain impact.",
    },

    # --- AUGUST ---
    {
        "name": "Independence Day",
        "typical_month": 8,
        "typical_day_range": [15, 15],
        "duration_days": 1,
        "demand_multiplier": 1.0,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "National holiday; government and bank closure. "
                               "Security restrictions in major cities.",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Single-day national holiday; minimal supply chain disruption.",
    },
    {
        "name": "Janmashtami",
        "typical_month": 8,
        "typical_day_range": [15, 18],
        "duration_days": 1,
        "demand_multiplier": 1.02,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "Minor; fasting associated. North India celebrations.",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "2025: August 17. Hindu festival celebrated nationally.",
    },
    {
        "name": "Onam",
        "typical_month": 8,
        "typical_day_range": [26, 31],
        "duration_days": 10,
        "demand_multiplier": 1.10,
        "affected_categories": ["analgesic", "antacid"],
        "affected_regions": ["Kerala"],
        "supply_chain_impact": "Major Kerala festival. Distribution shutdown for "
                               "3-5 days in the state. Pre-stocking 2 weeks before. "
                               "Kerala pharma market ~4% of IPM.",
        "counterfeit_risk_multiplier": 1.05,
        "notes": "2025: Thiruvonam on September 5. 10-day festival starting "
                 "late August. Kerala's biggest commercial event.",
    },
    {
        "name": "Ganesh Chaturthi",
        "typical_month": 8,
        "typical_day_range": [25, 30],
        "duration_days": 10,
        "demand_multiplier": 1.12,
        "affected_categories": ["analgesic", "antibiotic"],
        "affected_regions": ["Maharashtra", "Goa", "Karnataka", "Andhra Pradesh",
                             "Telangana"],
        "supply_chain_impact": "10-day celebration. Maharashtra distribution slows "
                               "significantly. Mumbai logistics disrupted by "
                               "processions and immersion routes. Pre-stocking "
                               "2 weeks before.",
        "counterfeit_risk_multiplier": 1.1,
        "notes": "2025: August 27 to September 6. Maharashtra pharma market is "
                 "~10% of IPM. Mumbai's logistics paralyzed during Visarjan "
                 "(immersion) processions.",
    },

    # --- SEPTEMBER ---
    {
        "name": "Navratri (Sharad)",
        "typical_month": 9,
        "typical_day_range": [22, 30],
        "duration_days": 9,
        "demand_multiplier": 1.10,
        "affected_categories": ["analgesic", "antacid", "supplement"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Nine nights of fasting and celebrations. "
                               "Distribution slows in Gujarat (Garba season) and "
                               "across North India. Pre-Dussehra/Diwali stocking "
                               "begins.",
        "counterfeit_risk_multiplier": 1.1,
        "notes": "2025: September 22 to October 1. Fasting can affect diabetic "
                 "medication compliance. Gujarat celebrates with 9 nights of "
                 "Garba -- commercial activity drops significantly.",
    },

    # --- OCTOBER ---
    {
        "name": "Durga Puja",
        "typical_month": 9,
        "typical_day_range": [28, 30],
        "duration_days": 5,
        "demand_multiplier": 1.15,
        "affected_categories": ["analgesic", "antibiotic", "antiacid"],
        "affected_regions": ["West Bengal", "Odisha", "Assam", "Jharkhand", "Bihar"],
        "supply_chain_impact": "Complete shutdown of commercial activity in West Bengal "
                               "and eastern India for 5 days. Pre-stocking essential "
                               "2 weeks before. Post-festival restocking surge.",
        "counterfeit_risk_multiplier": 1.15,
        "notes": "2025: September 28 to October 2. Kolkata and eastern India "
                 "pharma market (~8% IPM) shuts down completely. "
                 "Post-immersion water contamination drives GI illness.",
    },
    {
        "name": "Dussehra / Vijayadashami",
        "typical_month": 10,
        "typical_day_range": [1, 5],
        "duration_days": 1,
        "demand_multiplier": 1.08,
        "affected_categories": [],
        "affected_regions": ["all"],
        "supply_chain_impact": "National holiday. Marks end of Navratri. "
                               "Distribution pause for 1-2 days.",
        "counterfeit_risk_multiplier": 1.05,
        "notes": "2025: October 2. Coincides with Gandhi Jayanti (national holiday). "
                 "Double holiday amplifies distribution disruption.",
    },
    {
        "name": "Diwali / Deepavali",
        "typical_month": 10,
        "typical_day_range": [18, 25],
        "duration_days": 5,
        "demand_multiplier": 1.30,
        "affected_categories": ["all"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Pre-stocking 2-3 weeks before. Complete distribution "
                               "shutdown for 3-5 days during festival. Firecrackers "
                               "cause respiratory distress and burns -- spike in ER "
                               "visits. Post-Diwali pollution crisis in North India.",
        "counterfeit_risk_multiplier": 1.25,
        "notes": "2025: October 20. Biggest commercial event in India. "
                 "Massive inventory buildup creates opportunity for counterfeit "
                 "infiltration. Reduced oversight during festive rush. "
                 "Post-Diwali air pollution in Delhi drives respiratory drug demand. "
                 "Firecracker injuries drive analgesic and burn treatment demand.",
    },

    # --- NOVEMBER ---
    {
        "name": "Chhath Puja",
        "typical_month": 11,
        "typical_day_range": [1, 5],
        "duration_days": 4,
        "demand_multiplier": 1.05,
        "affected_categories": [],
        "affected_regions": ["Bihar", "Jharkhand", "Uttar Pradesh", "Delhi"],
        "supply_chain_impact": "Regional Bihar/UP festival. Migration to home states "
                               "affects urban labor availability in logistics.",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Bihar and eastern UP logistics workforce migrates home for "
                 "Chhath, causing temporary labor shortage.",
    },
    {
        "name": "Guru Nanak Jayanti",
        "typical_month": 11,
        "typical_day_range": [3, 7],
        "duration_days": 1,
        "demand_multiplier": 1.0,
        "affected_categories": [],
        "affected_regions": ["Punjab", "Haryana", "Delhi"],
        "supply_chain_impact": "Punjab distribution pause for 1 day",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "2025: November 5. Sikh festival; Punjab region impact only.",
    },

    # --- DECEMBER ---
    {
        "name": "Christmas",
        "typical_month": 12,
        "typical_day_range": [25, 25],
        "duration_days": 1,
        "demand_multiplier": 1.03,
        "affected_categories": [],
        "affected_regions": ["Goa", "Kerala", "Meghalaya", "Mizoram",
                             "Nagaland", "all"],
        "supply_chain_impact": "National holiday. Stronger impact in Christian-majority "
                               "states (Goa, Kerala, NE India). Distribution pause 1-2 days.",
        "counterfeit_risk_multiplier": 1.0,
        "notes": "Minimal national pharma impact. Goa and Kerala see extended "
                 "holiday period when combined with New Year.",
    },
    {
        "name": "New Year / Year-End Period",
        "typical_month": 12,
        "typical_day_range": [25, 31],
        "duration_days": 7,
        "demand_multiplier": 1.05,
        "affected_categories": ["all"],
        "affected_regions": ["all"],
        "supply_chain_impact": "Reduced distribution activity. Year-end inventory "
                               "adjustments. Banks and government offices on "
                               "reduced schedules. Cold-chain logistics challenged "
                               "by winter fog in North India.",
        "counterfeit_risk_multiplier": 1.05,
        "notes": "Combined Christmas-New Year week is a slow distribution period. "
                 "Some companies push end-of-calendar-year sales targets.",
    },

    # --- ELECTION PERIODS (variable) ---
    {
        "name": "State / General Elections",
        "typical_month": 0,
        "typical_day_range": [1, 30],
        "duration_days": 30,
        "demand_multiplier": 0.95,
        "affected_categories": [],
        "affected_regions": ["varies"],
        "supply_chain_impact": "Dry days (no alcohol), transport restrictions, "
                               "bandhs (shutdowns) before/after results. Security "
                               "forces commandeer vehicles. Government procurement "
                               "freezes during model code of conduct.",
        "counterfeit_risk_multiplier": 1.1,
        "notes": "Election periods (typically 4-6 weeks) cause government procurement "
                 "freeze and transport disruption. Five-phase elections can affect "
                 "different states over 2+ months. Reduced regulatory inspections.",
    },
]


# ============================================================================
#  3. DISEASE OUTBREAK PATTERNS  (India-specific)
# ============================================================================

DISEASE_OUTBREAK_PATTERNS: list[dict] = [
    {
        "disease": "Dengue",
        "peak_months": [9, 10, 11],
        "rising_months": [7, 8],
        "declining_months": [12],
        "low_months": [1, 2, 3, 4, 5, 6],
        "affected_regions": [
            "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu", "West Bengal",
            "Kerala", "Rajasthan", "Uttar Pradesh", "Telangana", "Punjab",
        ],
        "drug_demand_spike": {
            "analgesic": 1.5,
            "rehydration": 1.4,
            "antiplatelet": 1.3,
        },
        "overall_demand_multiplier": 1.5,
        "counterfeit_risk": "high",
        "annual_cases_approx": 150000,
        "notes": "Dengue panic buying creates massive paracetamol demand. "
                 "NSAIDs (aspirin, ibuprofen) are contraindicated -- patients "
                 "must use paracetamol only. Counterfeit paracetamol spikes "
                 "during dengue season. PharmEasy data shows Aug-Oct testing surge.",
    },
    {
        "disease": "Malaria",
        "peak_months": [8, 9],
        "rising_months": [6, 7],
        "declining_months": [10, 11],
        "low_months": [12, 1, 2, 3, 4, 5],
        "affected_regions": [
            "Odisha", "Chhattisgarh", "Jharkhand", "Madhya Pradesh",
            "Maharashtra", "Rajasthan", "Gujarat", "West Bengal",
            "Assam", "Meghalaya", "Mizoram", "Tripura",
        ],
        "drug_demand_spike": {
            "antimalarial": 2.0,
            "analgesic": 1.3,
            "antibiotic": 1.2,
        },
        "overall_demand_multiplier": 1.8,
        "counterfeit_risk": "critical",
        "annual_cases_approx": 5000000,
        "notes": "P. vivax peaks June-August; P. falciparum peaks September-December. "
                 "WHO estimates 19.1% of antimalarials in endemic regions are "
                 "substandard/falsified. Northeastern states and tribal areas have "
                 "highest burden. SAF for August is 3.14 (seasonal adjustment).",
    },
    {
        "disease": "Chikungunya",
        "peak_months": [8, 9, 10],
        "rising_months": [7],
        "declining_months": [11],
        "low_months": [12, 1, 2, 3, 4, 5, 6],
        "affected_regions": [
            "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu",
            "Kerala", "Andhra Pradesh", "Telangana", "Rajasthan",
        ],
        "drug_demand_spike": {
            "analgesic": 1.4,
            "corticosteroid": 1.2,
            "antihistamine": 1.1,
        },
        "overall_demand_multiplier": 1.3,
        "counterfeit_risk": "medium",
        "annual_cases_approx": 50000,
        "notes": "Shares Aedes aegypti vector with dengue -- outbreaks often "
                 "co-occur. Dengue-chikungunya syndemic documented. "
                 "Chronic joint pain drives prolonged analgesic demand.",
    },
    {
        "disease": "Typhoid",
        "peak_months": [7, 8, 9],
        "rising_months": [6],
        "declining_months": [10],
        "low_months": [11, 12, 1, 2, 3, 4, 5],
        "affected_regions": [
            "Delhi", "Uttar Pradesh", "Bihar", "West Bengal",
            "Maharashtra", "Madhya Pradesh", "Rajasthan",
        ],
        "drug_demand_spike": {
            "antibiotic": 1.6,
            "analgesic": 1.3,
            "rehydration": 1.4,
        },
        "overall_demand_multiplier": 1.4,
        "counterfeit_risk": "medium",
        "annual_cases_approx": 500000,
        "notes": "Waterborne; monsoon contamination of drinking water is primary "
                 "driver. Azithromycin and cefixime are first-line treatments. "
                 "Multi-drug resistant typhoid increasing, driving demand for "
                 "newer antibiotics.",
    },
    {
        "disease": "Cholera",
        "peak_months": [7, 8, 9],
        "rising_months": [6],
        "declining_months": [10],
        "low_months": [11, 12, 1, 2, 3, 4, 5],
        "affected_regions": [
            "West Bengal", "Odisha", "Bihar", "Uttar Pradesh",
            "Assam", "Jharkhand", "Maharashtra",
        ],
        "drug_demand_spike": {
            "rehydration": 2.0,
            "antibiotic": 1.5,
        },
        "overall_demand_multiplier": 1.5,
        "counterfeit_risk": "low",
        "annual_cases_approx": 5000,
        "notes": "Cholera cases rose 421% from 2021 to 2025 per health ministry data. "
                 "Primarily affects areas with poor water infrastructure. "
                 "ORS is critical treatment -- low counterfeit risk due to low value.",
    },
    {
        "disease": "Japanese Encephalitis",
        "peak_months": [8, 9],
        "rising_months": [7],
        "declining_months": [10, 11],
        "low_months": [12, 1, 2, 3, 4, 5, 6],
        "affected_regions": [
            "Uttar Pradesh", "Bihar", "Assam", "West Bengal",
            "Tamil Nadu", "Karnataka", "Andhra Pradesh",
        ],
        "drug_demand_spike": {
            "corticosteroid": 1.3,
            "anticonvulsant": 1.2,
        },
        "overall_demand_multiplier": 1.2,
        "counterfeit_risk": "low",
        "annual_cases_approx": 3000,
        "notes": "Peaks during monsoon; eastern UP and Bihar are epicenters. "
                 "Time-series shows highest peak in August-September. "
                 "Karnataka/AP see a secondary April-July peak. "
                 "Primarily affects children in rice-cultivating rural areas.",
    },
    {
        "disease": "Leptospirosis",
        "peak_months": [7, 8, 9],
        "rising_months": [6],
        "declining_months": [10],
        "low_months": [11, 12, 1, 2, 3, 4, 5],
        "affected_regions": [
            "Mumbai", "Kerala", "Karnataka", "Andaman & Nicobar",
            "Gujarat", "Tamil Nadu",
        ],
        "drug_demand_spike": {
            "antibiotic": 1.4,
            "analgesic": 1.2,
        },
        "overall_demand_multiplier": 1.3,
        "counterfeit_risk": "low",
        "annual_cases_approx": 10000,
        "notes": "Spread through contact with floodwater contaminated by rat urine. "
                 "Mumbai and Kerala are hotspots during heavy monsoon flooding. "
                 "Doxycycline is primary prophylaxis and treatment.",
    },
    {
        "disease": "Hepatitis A / Hepatitis E",
        "peak_months": [7, 8, 9],
        "rising_months": [6],
        "declining_months": [10, 11],
        "low_months": [12, 1, 2, 3, 4, 5],
        "affected_regions": [
            "Delhi", "Uttar Pradesh", "Bihar", "West Bengal",
            "Rajasthan", "Madhya Pradesh",
        ],
        "drug_demand_spike": {
            "analgesic": 1.2,
            "supplement": 1.3,
        },
        "overall_demand_multiplier": 1.2,
        "counterfeit_risk": "low",
        "annual_cases_approx": 40000,
        "notes": "Hepatitis A cases surged 890% from 2021 to 2025. Waterborne; "
                 "monsoon contamination is primary driver. No specific antiviral "
                 "treatment -- supportive care with paracetamol and liver supplements. "
                 "Hepatitis E particularly dangerous in pregnant women.",
    },
    {
        "disease": "Influenza / H1N1",
        "peak_months": [1, 2, 8],
        "rising_months": [7, 12],
        "declining_months": [3, 9],
        "low_months": [4, 5, 6, 10, 11],
        "affected_regions": [
            "Delhi", "Maharashtra", "Rajasthan", "Gujarat",
            "Karnataka", "Telangana", "Tamil Nadu",
        ],
        "drug_demand_spike": {
            "antiviral": 1.5,
            "cough_syrup": 1.3,
            "antibiotic": 1.2,
            "analgesic": 1.3,
        },
        "overall_demand_multiplier": 1.4,
        "counterfeit_risk": "medium",
        "annual_cases_approx": 50000,
        "notes": "Bimodal peak: winter (Jan-Feb) and monsoon (Jul-Aug). "
                 "H1N1 peaks in January-February in most years. "
                 "Respiratory infection samples highest during monsoon (43.8%). "
                 "Influenza A H1 2009 peaked in monsoon with smaller Feb peak.",
    },
    {
        "disease": "Tuberculosis",
        "peak_months": [4, 5, 6],
        "rising_months": [3],
        "declining_months": [7],
        "low_months": [10, 11, 12, 1, 2, 8, 9],
        "affected_regions": [
            "Uttar Pradesh", "Maharashtra", "Madhya Pradesh", "Rajasthan",
            "Bihar", "Gujarat", "Tamil Nadu", "Delhi",
        ],
        "drug_demand_spike": {
            "anti_tb": 1.4,
            "antibiotic": 1.1,
            "supplement": 1.1,
        },
        "overall_demand_multiplier": 1.3,
        "counterfeit_risk": "high",
        "annual_cases_approx": 2800000,
        "notes": "TB notifications peak April-June in North India (infections "
                 "acquired in winter manifest months later). South India shows "
                 "no significant seasonality. WHO monitors anti-TB drug quality -- "
                 "substandard rifampicin threatens MDR-TB control. India has "
                 "highest TB burden globally (~28 lakh cases/year).",
    },
    {
        "disease": "Scrub Typhus",
        "peak_months": [9, 10, 11],
        "rising_months": [8],
        "declining_months": [12],
        "low_months": [1, 2, 3, 4, 5, 6, 7],
        "affected_regions": [
            "Himachal Pradesh", "Uttarakhand", "Jammu & Kashmir",
            "Assam", "Meghalaya", "Nagaland", "Tamil Nadu",
        ],
        "drug_demand_spike": {
            "antibiotic": 1.3,
            "analgesic": 1.2,
        },
        "overall_demand_multiplier": 1.2,
        "counterfeit_risk": "low",
        "annual_cases_approx": 25000,
        "notes": "Post-rainy season disease. Northeast India and hilly northern "
                 "states are primary endemic zones. Doxycycline and azithromycin "
                 "are first-line treatments. Often misdiagnosed as dengue due "
                 "to overlapping season and similar symptoms.",
    },
    {
        "disease": "COVID-19 Waves",
        "peak_months": [],
        "rising_months": [],
        "declining_months": [],
        "low_months": [],
        "affected_regions": ["all"],
        "drug_demand_spike": {
            "antiviral": 2.5,
            "corticosteroid": 2.0,
            "antibiotic": 1.8,
            "analgesic": 1.5,
            "supplement": 1.5,
        },
        "overall_demand_multiplier": 2.0,
        "counterfeit_risk": "critical",
        "annual_cases_approx": 0,
        "notes": "No fixed seasonality -- pandemic waves unpredictable. "
                 "Delta wave (Apr-Jun 2021) was worst. Massive counterfeit "
                 "remdesivir wave in India: empty vials filled with paracetamol "
                 "or saline. COVID disrupted API supply from China, creating "
                 "shortages that enabled counterfeit penetration across all "
                 "drug categories. Model should treat as stochastic event.",
    },
]


# ============================================================================
#  4. SUPPLY CHAIN DISRUPTION PATTERNS
# ============================================================================

SUPPLY_CHAIN_DISRUPTIONS: list[dict] = [
    {
        "disruption_type": "monsoon_flooding",
        "months": [7, 8, 9],
        "affected_states": [
            "Assam", "Bihar", "West Bengal", "Kerala",
            "Mumbai (Maharashtra)", "Uttar Pradesh", "Odisha",
        ],
        "transit_delay_multiplier": 2.5,
        "supply_shortage_risk": "high",
        "counterfeit_opportunity": "high",
        "probability_per_year": 0.95,
        "notes": "Annual occurrence. Flooding disrupts road transport; transit "
                 "time increases up to 40%. Shortages in flood-affected areas "
                 "create prime conditions for counterfeit injection. "
                 "2023 North India floods severely affected pharma supply chains. "
                 "Costs increase 15% due to rerouting and damaged infrastructure.",
    },
    {
        "disruption_type": "winter_fog",
        "months": [12, 1, 2],
        "affected_states": [
            "Punjab", "Haryana", "Delhi", "Uttar Pradesh",
            "Bihar", "Rajasthan", "Madhya Pradesh",
        ],
        "transit_delay_multiplier": 1.5,
        "supply_shortage_risk": "medium",
        "counterfeit_opportunity": "low",
        "probability_per_year": 0.90,
        "notes": "Dense fog with visibility under 100m is common in the "
                 "Indo-Gangetic plain from December to February. Road and rail "
                 "delays of 2-5 days frequent. Highway pile-ups common. "
                 "Cold-chain pharmaceuticals especially affected (insulin, "
                 "vaccines). Temperature extremes can degrade products.",
    },
    {
        "disruption_type": "cyclone_coastal",
        "months": [10, 11, 12, 4, 5],
        "affected_states": [
            "Odisha", "Andhra Pradesh", "Tamil Nadu", "West Bengal",
            "Kerala", "Gujarat", "Karnataka",
        ],
        "transit_delay_multiplier": 3.0,
        "supply_shortage_risk": "high",
        "counterfeit_opportunity": "medium",
        "probability_per_year": 0.70,
        "notes": "Bay of Bengal cyclones (Oct-Dec) and Arabian Sea cyclones "
                 "(Apr-Jun). Can destroy local infrastructure for weeks. "
                 "Port operations at major pharma ports (JNPT, Chennai, "
                 "Visakhapatnam) disrupted. Emergency medicine demand surges. "
                 "IMD data shows 30% increase in extreme weather events since 2010.",
    },
    {
        "disruption_type": "strikes_bandhs",
        "months": [0],
        "affected_states": ["varies"],
        "transit_delay_multiplier": 2.0,
        "supply_shortage_risk": "medium",
        "counterfeit_opportunity": "medium",
        "probability_per_year": 0.60,
        "notes": "Bharat Bandh (national shutdowns), transport strikes, and "
                 "state-level bandhs occur periodically. Truck driver strikes "
                 "can paralyze the entire supply chain. India's ~12 million "
                 "truckers handle 65% of freight. A 3-day truckers' strike "
                 "can wipe out buffer stocks in pharmacies.",
    },
    {
        "disruption_type": "election_period",
        "months": [0],
        "affected_states": ["varies"],
        "transit_delay_multiplier": 1.3,
        "supply_shortage_risk": "low",
        "counterfeit_opportunity": "medium",
        "probability_per_year": 0.50,
        "notes": "General elections (every 5 years) and state elections (rolling) "
                 "cause Model Code of Conduct, restricting government procurement "
                 "and tenders. Security forces commandeer transport. Bandhs and "
                 "protests around results. Regulatory inspections reduced as "
                 "officials are deployed for election duty.",
    },
    {
        "disruption_type": "highway_construction",
        "months": [10, 11, 12, 1, 2, 3, 4, 5],
        "affected_states": [
            "Rajasthan", "Madhya Pradesh", "Maharashtra", "Karnataka",
            "Gujarat", "Tamil Nadu", "Uttar Pradesh",
        ],
        "transit_delay_multiplier": 1.4,
        "supply_shortage_risk": "low",
        "counterfeit_opportunity": "low",
        "probability_per_year": 0.80,
        "notes": "India's massive highway expansion program (Bharatmala, "
                 "Sagarmala) means perpetual construction on arterial routes. "
                 "Detours add 2-6 hours to transit times. Worse in non-monsoon "
                 "months when construction is active. Toll plaza congestion adds delays.",
    },
    {
        "disruption_type": "api_shortage_china",
        "months": [1, 2, 3],
        "affected_states": ["all"],
        "transit_delay_multiplier": 1.0,
        "supply_shortage_risk": "high",
        "counterfeit_opportunity": "critical",
        "probability_per_year": 0.30,
        "notes": "India imports ~71% of API intermediates from China. Chinese "
                 "New Year (Jan-Feb) causes annual production slowdown. "
                 "Any geopolitical disruption, pandemic, or regulatory action "
                 "in China can cause severe API shortages in India. "
                 "COVID-19 demonstrated catastrophic dependence when border "
                 "shutdowns caused medicine shortages across categories. "
                 "PLI scheme aims to reduce dependence but progress is slow.",
    },
    {
        "disruption_type": "port_congestion",
        "months": [10, 11, 3],
        "affected_states": [
            "Maharashtra", "Gujarat", "Tamil Nadu", "Andhra Pradesh",
        ],
        "transit_delay_multiplier": 1.6,
        "supply_shortage_risk": "medium",
        "counterfeit_opportunity": "low",
        "probability_per_year": 0.50,
        "notes": "JNPT (Nhava Sheva), Mundra, and Chennai ports handle most "
                 "pharma imports/exports. Pre-festival inventory surges (Oct-Nov) "
                 "and financial year-end (March) cause congestion. "
                 "Container shortages post-pandemic remain intermittent. "
                 "API imports from China transiting through these ports.",
    },
    {
        "disruption_type": "heatwave",
        "months": [4, 5, 6],
        "affected_states": [
            "Rajasthan", "Gujarat", "Madhya Pradesh", "Telangana",
            "Andhra Pradesh", "Maharashtra", "Delhi", "Bihar",
        ],
        "transit_delay_multiplier": 1.2,
        "supply_shortage_risk": "medium",
        "counterfeit_opportunity": "low",
        "probability_per_year": 0.85,
        "notes": "Temperatures exceeding 45-50 degrees C in western/central India. "
                 "Cold-chain failures common: insulin, vaccines, biologics "
                 "degrade during transport. Truck drivers avoid midday travel. "
                 "Heat-related illness drives emergency drug demand. "
                 "Product stability compromised in non-AC warehouses.",
    },
    {
        "disruption_type": "natural_disaster_earthquake",
        "months": [0],
        "affected_states": [
            "Jammu & Kashmir", "Himachal Pradesh", "Uttarakhand",
            "Gujarat", "Maharashtra", "Assam",
        ],
        "transit_delay_multiplier": 5.0,
        "supply_shortage_risk": "critical",
        "counterfeit_opportunity": "high",
        "probability_per_year": 0.10,
        "notes": "India lies on seismically active zones. Earthquakes destroy "
                 "infrastructure and create acute medicine shortages. "
                 "Relief supply chains are chaotic -- prime counterfeit entry point. "
                 "2001 Gujarat earthquake and 2005 Kashmir earthquake are examples.",
    },
    {
        "disruption_type": "regulatory_crackdown",
        "months": [0],
        "affected_states": ["all"],
        "transit_delay_multiplier": 1.0,
        "supply_shortage_risk": "medium",
        "counterfeit_opportunity": "low",
        "probability_per_year": 0.40,
        "notes": "Periodic CDSCO drives, state FDA raids, and court orders "
                 "can shut down manufacturing units or distribution chains. "
                 "Post-WHO alert crackdowns (e.g., after Gambia cough syrup "
                 "deaths) cause supply disruption for affected categories. "
                 "GST enforcement drives also affect small distributors.",
    },
]


# ============================================================================
#  5. OPERATING HOUR PATTERNS
# ============================================================================

OPERATING_HOUR_PATTERNS: dict = {
    "manufacturing": {
        "description": "Pharmaceutical manufacturing plants in India",
        "shift_pattern": "3-shift rotation (24/7 for large plants; 2-shift for smaller)",
        "shifts": {
            "morning":  {"start": 6, "end": 14, "label": "Morning / A Shift"},
            "afternoon": {"start": 14, "end": 22, "label": "Afternoon / B Shift"},
            "night":    {"start": 22, "end": 6,  "label": "Night / C Shift"},
            "general":  {"start": 9, "end": 17,  "label": "General Shift (admin/QA)"},
        },
        "hourly_activity_distribution": {
            # Probability weight of manufacturing activity by hour (0-23)
            # 24/7 operation but with slight preference for day shifts
            0: 0.70, 1: 0.65, 2: 0.60, 3: 0.55, 4: 0.55, 5: 0.60,
            6: 0.85, 7: 0.90, 8: 0.95, 9: 1.00, 10: 1.00, 11: 0.98,
            12: 0.90, 13: 0.95, 14: 0.95, 15: 0.95, 16: 0.95, 17: 0.90,
            18: 0.85, 19: 0.80, 20: 0.80, 21: 0.75, 22: 0.75, 23: 0.70,
        },
        "weekly_pattern": {
            "monday": 1.0, "tuesday": 1.0, "wednesday": 1.0,
            "thursday": 1.0, "friday": 1.0, "saturday": 0.80,
            "sunday": 0.30,
        },
        "notes": "Large plants (Sun Pharma, Cipla, Dr Reddy's) run 24/7 with "
                 "3 rotating shifts. Smaller units run 2 shifts (6am-2pm, 2pm-10pm). "
                 "QA/QC and admin staff work general shift (9am-5:30pm). "
                 "Factories Act limits: 8 hours/day, 48 hours/week, max 50 OT hours/quarter.",
    },

    "distribution_warehouse": {
        "description": "Clearing and Forwarding Agents (CFAs) and stockist warehouses",
        "shift_pattern": "Primary day operations with evening dispatch",
        "shifts": {
            "primary":   {"start": 8, "end": 18, "label": "Primary Operations"},
            "dispatch":  {"start": 18, "end": 22, "label": "Evening Dispatch"},
            "receiving": {"start": 6, "end": 8,  "label": "Early Morning Receiving"},
        },
        "hourly_activity_distribution": {
            0: 0.02, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.02, 5: 0.05,
            6: 0.20, 7: 0.40, 8: 0.70, 9: 0.90, 10: 1.00, 11: 1.00,
            12: 0.80, 13: 0.90, 14: 0.95, 15: 0.95, 16: 0.90, 17: 0.80,
            18: 0.60, 19: 0.40, 20: 0.25, 21: 0.15, 22: 0.08, 23: 0.04,
        },
        "weekly_pattern": {
            "monday": 1.0, "tuesday": 1.0, "wednesday": 1.0,
            "thursday": 1.0, "friday": 1.0, "saturday": 0.70,
            "sunday": 0.10,
        },
        "notes": "1-3 CFAs per state per company. Operate primarily during "
                 "business hours with evening dispatch window. Large CFAs "
                 "(e.g., in Maharashtra, Gujarat) may run extended hours. "
                 "Stockists handle 5-15 companies simultaneously. "
                 "Credit cycle: 30-45 days. Distribution cost: up to 33% of revenue.",
    },

    "pharmacy_retail": {
        "description": "Retail pharmacies (medical shops) across India",
        "shift_pattern": "Extended hours, split shifts common",
        "shifts": {
            "morning":  {"start": 8, "end": 14, "label": "Morning Shift"},
            "evening":  {"start": 14, "end": 22, "label": "Evening Shift"},
            "full_day": {"start": 9, "end": 21, "label": "Full Day (single pharmacist)"},
        },
        "hourly_activity_distribution": {
            0: 0.02, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02,
            6: 0.05, 7: 0.10, 8: 0.30, 9: 0.60, 10: 0.85, 11: 0.95,
            12: 0.80, 13: 0.75, 14: 0.70, 15: 0.75, 16: 0.80, 17: 0.90,
            18: 1.00, 19: 0.95, 20: 0.80, 21: 0.50, 22: 0.20, 23: 0.08,
        },
        "weekly_pattern": {
            "monday": 1.0, "tuesday": 1.0, "wednesday": 1.0,
            "thursday": 1.0, "friday": 1.0, "saturday": 0.95,
            "sunday": 0.60,
        },
        "notes": "Most Indian pharmacies operate 8am-10pm (14-16 hours). "
                 "Evening hours (5pm-8pm) are peak due to post-work visits. "
                 "Hospital pharmacy: 24/7 in tertiary care. "
                 "Sunday: open but reduced hours (many close by 2pm). "
                 "Night pharmacy (after 10pm) in cities only.",
    },

    "consumer_scanning": {
        "description": "Consumer medicine verification scans (MediChain mobile app)",
        "shift_pattern": "Follows consumer behavior patterns",
        "shifts": {
            "morning_meds":  {"start": 7, "end": 10, "label": "Morning Medication Time"},
            "midday":        {"start": 12, "end": 14, "label": "Lunch Break Scanning"},
            "evening_meds":  {"start": 18, "end": 22, "label": "Evening Medication / Post-Purchase"},
        },
        "hourly_activity_distribution": {
            0: 0.02, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.03,
            6: 0.08, 7: 0.20, 8: 0.45, 9: 0.65, 10: 0.75, 11: 0.70,
            12: 0.60, 13: 0.55, 14: 0.50, 15: 0.50, 16: 0.55, 17: 0.65,
            18: 0.85, 19: 1.00, 20: 0.90, 21: 0.60, 22: 0.30, 23: 0.10,
        },
        "weekly_pattern": {
            "monday": 0.90, "tuesday": 0.90, "wednesday": 0.90,
            "thursday": 0.90, "friday": 0.95, "saturday": 1.00,
            "sunday": 0.80,
        },
        "notes": "Consumers most likely to scan medicines after pharmacy purchase "
                 "(evening peak). Morning peak from medication time awareness. "
                 "Saturday peak: more pharmacy visits on weekends. "
                 "Scans cluster around medication administration times.",
    },

    "suspicious_activity": {
        "description": "Patterns indicating potentially illicit supply chain activity",
        "shift_pattern": "Inverse of normal operations",
        "peak_hours": [0, 1, 2, 3, 4, 5, 22, 23],
        "hourly_anomaly_score_modifier": {
            # Multiplier for anomaly scoring based on hour of activity
            # Higher values = more suspicious
            0: 2.0, 1: 2.5, 2: 3.0, 3: 3.0, 4: 2.5, 5: 2.0,
            6: 1.2, 7: 1.0, 8: 0.8, 9: 0.7, 10: 0.7, 11: 0.7,
            12: 0.8, 13: 0.7, 14: 0.7, 15: 0.7, 16: 0.7, 17: 0.8,
            18: 0.9, 19: 1.0, 20: 1.2, 21: 1.5, 22: 1.8, 23: 2.0,
        },
        "weekly_anomaly_score_modifier": {
            "monday": 1.0, "tuesday": 1.0, "wednesday": 1.0,
            "thursday": 1.0, "friday": 1.0, "saturday": 1.3,
            "sunday": 1.8,
        },
        "notes": "Transfers between 2am and 5am on weekdays are most suspicious. "
                 "Sunday warehouse activity is rare for legitimate operations. "
                 "Weekend night transfers are a strong anomaly signal. "
                 "Holiday transfers should also be flagged. "
                 "Cross-reference with known operating hours of specific facilities.",
    },

    "regulatory_inspection": {
        "description": "CDSCO / State FDA inspection activity hours",
        "shift_pattern": "Government working hours only",
        "shifts": {
            "inspection": {"start": 10, "end": 17, "label": "Inspection Window"},
        },
        "hourly_activity_distribution": {
            0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0,
            6: 0.0, 7: 0.0, 8: 0.0, 9: 0.05, 10: 0.40, 11: 0.80,
            12: 0.60, 13: 0.70, 14: 0.90, 15: 1.00, 16: 0.80, 17: 0.30,
            18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0, 22: 0.0, 23: 0.0,
        },
        "weekly_pattern": {
            "monday": 1.0, "tuesday": 1.0, "wednesday": 1.0,
            "thursday": 1.0, "friday": 0.80, "saturday": 0.10,
            "sunday": 0.0,
        },
        "notes": "CDSCO has only ~323 inspectors for all of India (2014 data). "
                 "Inspections happen during government hours (10am-5pm). "
                 "No inspections on weekends or gazetted holidays. "
                 "This gap is exploited by counterfeiters who operate outside "
                 "inspection windows.",
    },
}


# ============================================================================
#  6. DRUG CATEGORY SEASONALITY  (per-category monthly demand curves)
# ============================================================================

DRUG_CATEGORY_SEASONALITY: dict = {
    "antimalarial": {
        "monthly_multiplier": {
            1: 0.3, 2: 0.3, 3: 0.4, 4: 0.5, 5: 0.6,
            6: 1.2, 7: 1.6, 8: 2.0, 9: 1.8, 10: 1.4,
            11: 0.8, 12: 0.4,
        },
        "peak_description": "Monsoon malaria season (Jun-Oct)",
        "counterfeit_risk_seasonal": {
            1: 0.8, 2: 0.8, 3: 0.9, 4: 0.9, 5: 1.0,
            6: 1.2, 7: 1.5, 8: 1.8, 9: 1.6, 10: 1.3,
            11: 0.9, 12: 0.8,
        },
    },
    "antibiotic": {
        "monthly_multiplier": {
            1: 0.9, 2: 0.85, 3: 0.90, 4: 0.95, 5: 1.10,
            6: 1.25, 7: 1.40, 8: 1.45, 9: 1.35, 10: 1.15,
            11: 1.00, 12: 0.95,
        },
        "peak_description": "Monsoon infections + winter respiratory secondary peak",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.1,
            6: 1.2, 7: 1.4, 8: 1.5, 9: 1.3, 10: 1.1,
            11: 1.0, 12: 1.0,
        },
    },
    "analgesic": {
        "monthly_multiplier": {
            1: 1.0, 2: 0.95, 3: 0.95, 4: 1.00, 5: 1.05,
            6: 1.10, 7: 1.15, 8: 1.20, 9: 1.30, 10: 1.35,
            11: 1.10, 12: 1.05,
        },
        "peak_description": "Dengue season drives paracetamol peak (Sep-Oct); year-round baseline",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0,
            6: 1.1, 7: 1.2, 8: 1.3, 9: 1.5, 10: 1.5,
            11: 1.2, 12: 1.0,
        },
    },
    "antiasthmatic": {
        "monthly_multiplier": {
            1: 1.30, 2: 1.20, 3: 1.00, 4: 0.80, 5: 0.75,
            6: 0.85, 7: 0.90, 8: 0.90, 9: 0.95, 10: 1.10,
            11: 1.40, 12: 1.35,
        },
        "peak_description": "Winter pollution season (Nov-Feb) drives respiratory drug demand",
        "counterfeit_risk_seasonal": {
            1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.9,
            6: 0.9, 7: 0.9, 8: 0.9, 9: 1.0, 10: 1.1,
            11: 1.3, 12: 1.2,
        },
    },
    "bronchodilator": {
        "monthly_multiplier": {
            1: 1.25, 2: 1.15, 3: 0.95, 4: 0.80, 5: 0.75,
            6: 0.80, 7: 0.85, 8: 0.85, 9: 0.90, 10: 1.05,
            11: 1.35, 12: 1.30,
        },
        "peak_description": "Mirrors antiasthmatic pattern -- winter respiratory surge",
        "counterfeit_risk_seasonal": {
            1: 1.1, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.9,
            6: 0.9, 7: 0.9, 8: 0.9, 9: 1.0, 10: 1.0,
            11: 1.2, 12: 1.2,
        },
    },
    "cough_syrup": {
        "monthly_multiplier": {
            1: 1.30, 2: 1.15, 3: 0.90, 4: 0.70, 5: 0.65,
            6: 0.70, 7: 0.75, 8: 0.80, 9: 0.85, 10: 1.00,
            11: 1.35, 12: 1.40,
        },
        "peak_description": "Winter cough/cold season (Nov-Feb); minimal in summer",
        "counterfeit_risk_seasonal": {
            1: 1.3, 2: 1.2, 3: 1.0, 4: 0.9, 5: 0.8,
            6: 0.8, 7: 0.9, 8: 0.9, 9: 1.0, 10: 1.1,
            11: 1.4, 12: 1.4,
        },
    },
    "rehydration": {
        "monthly_multiplier": {
            1: 0.50, 2: 0.50, 3: 0.60, 4: 0.80, 5: 1.20,
            6: 1.50, 7: 1.80, 8: 1.90, 9: 1.70, 10: 1.20,
            11: 0.70, 12: 0.50,
        },
        "peak_description": "Summer heat + monsoon diarrheal disease (May-Sep)",
        "counterfeit_risk_seasonal": {
            1: 0.8, 2: 0.8, 3: 0.8, 4: 0.9, 5: 1.0,
            6: 1.1, 7: 1.2, 8: 1.2, 9: 1.1, 10: 1.0,
            11: 0.8, 12: 0.8,
        },
    },
    "antifungal": {
        "monthly_multiplier": {
            1: 0.70, 2: 0.65, 3: 0.70, 4: 0.80, 5: 0.90,
            6: 1.30, 7: 1.50, 8: 1.55, 9: 1.40, 10: 1.10,
            11: 0.80, 12: 0.70,
        },
        "peak_description": "Monsoon humidity drives fungal infections (Jun-Sep)",
        "counterfeit_risk_seasonal": {
            1: 0.9, 2: 0.9, 3: 0.9, 4: 0.9, 5: 1.0,
            6: 1.2, 7: 1.3, 8: 1.3, 9: 1.2, 10: 1.0,
            11: 0.9, 12: 0.9,
        },
    },
    "antihistamine": {
        "monthly_multiplier": {
            1: 1.10, 2: 1.05, 3: 1.15, 4: 0.90, 5: 0.85,
            6: 1.00, 7: 1.05, 8: 1.10, 9: 1.10, 10: 1.05,
            11: 1.15, 12: 1.10,
        },
        "peak_description": "Bimodal: Holi season (Mar) + winter allergies (Nov-Jan) + monsoon",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 1.1, 12: 1.0,
        },
    },
    "antidiabetic": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.00, 3: 1.05, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.05,
            11: 1.05, 12: 1.00,
        },
        "peak_description": "Chronic therapy -- relatively flat with minor Q1/Q3 bumps from festivals/fasting",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.1,
            11: 1.0, 12: 1.0,
        },
    },
    "antihypertensive": {
        "monthly_multiplier": {
            1: 1.05, 2: 1.00, 3: 1.05, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.05,
            11: 1.05, 12: 1.05,
        },
        "peak_description": "Chronic therapy -- flat with minor winter BP elevation",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.1,
            11: 1.0, 12: 1.0,
        },
    },
    "statin": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.00, 3: 1.05, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.05,
            11: 1.00, 12: 1.00,
        },
        "peak_description": "Chronic therapy -- flat with financial year-end bulk procurement",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 1.0, 12: 1.0,
        },
    },
    "corticosteroid": {
        "monthly_multiplier": {
            1: 1.20, 2: 1.10, 3: 0.95, 4: 0.90, 5: 0.85,
            6: 0.90, 7: 0.95, 8: 1.00, 9: 1.05, 10: 1.05,
            11: 1.15, 12: 1.20,
        },
        "peak_description": "Winter respiratory + chikungunya/JE supportive treatment",
        "counterfeit_risk_seasonal": {
            1: 1.1, 2: 1.0, 3: 1.0, 4: 0.9, 5: 0.9,
            6: 0.9, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 1.1, 12: 1.1,
        },
    },
    "anti_tb": {
        "monthly_multiplier": {
            1: 0.90, 2: 0.95, 3: 1.05, 4: 1.20, 5: 1.25,
            6: 1.20, 7: 1.10, 8: 1.00, 9: 0.95, 10: 0.90,
            11: 0.90, 12: 0.85,
        },
        "peak_description": "TB notifications peak Apr-Jun in North India (winter infections manifesting)",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.2, 5: 1.3,
            6: 1.2, 7: 1.1, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 1.0, 12: 1.0,
        },
    },
    "antiviral": {
        "monthly_multiplier": {
            1: 1.20, 2: 1.15, 3: 0.90, 4: 0.85, 5: 0.85,
            6: 0.90, 7: 1.00, 8: 1.10, 9: 1.00, 10: 0.90,
            11: 0.95, 12: 1.10,
        },
        "peak_description": "Winter influenza (Jan-Feb) + monsoon secondary peak (Jul-Aug)",
        "counterfeit_risk_seasonal": {
            1: 1.2, 2: 1.2, 3: 1.0, 4: 0.9, 5: 0.9,
            6: 1.0, 7: 1.1, 8: 1.2, 9: 1.0, 10: 0.9,
            11: 1.0, 12: 1.1,
        },
    },
    "antiplatelet": {
        "monthly_multiplier": {
            1: 0.90, 2: 0.90, 3: 0.90, 4: 0.90, 5: 0.90,
            6: 0.95, 7: 1.00, 8: 1.10, 9: 1.30, 10: 1.40,
            11: 1.10, 12: 0.90,
        },
        "peak_description": "Dengue season drives platelet-support demand (Sep-Oct)",
        "counterfeit_risk_seasonal": {
            1: 0.9, 2: 0.9, 3: 0.9, 4: 0.9, 5: 0.9,
            6: 1.0, 7: 1.0, 8: 1.1, 9: 1.3, 10: 1.3,
            11: 1.0, 12: 0.9,
        },
    },
    "supplement": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.00, 3: 1.05, 4: 1.05, 5: 1.05,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.05,
            11: 1.00, 12: 1.00,
        },
        "peak_description": "Fairly flat; minor bumps from health awareness seasons and festivals",
        "counterfeit_risk_seasonal": {
            1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.0,
            6: 0.9, 7: 0.9, 8: 0.9, 9: 0.9, 10: 1.0,
            11: 0.9, 12: 0.9,
        },
    },
    "oncology": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.00, 3: 1.05, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 0.95, 8: 0.95, 9: 1.00, 10: 1.00,
            11: 1.00, 12: 0.95,
        },
        "peak_description": "Non-seasonal chronic therapy; minor dip during monsoon from access issues",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 1.0, 12: 1.0,
        },
    },
    "antacid": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.00, 3: 1.10, 4: 1.05, 5: 1.00,
            6: 1.05, 7: 1.10, 8: 1.10, 9: 1.05, 10: 1.10,
            11: 1.15, 12: 1.05,
        },
        "peak_description": "Festival feasting (Diwali, Eid, Holi) + monsoon GI issues",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.1, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.1,
            11: 1.1, 12: 1.0,
        },
    },
    "controlled": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.00,
            11: 1.00, 12: 1.00,
        },
        "peak_description": "Non-seasonal; regulated supply. Diversion risk is constant.",
        "counterfeit_risk_seasonal": {
            1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 1.0, 12: 1.0,
        },
    },
    "glp1_agonist": {
        "monthly_multiplier": {
            1: 1.05, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.00,
            11: 1.00, 12: 1.05,
        },
        "peak_description": "Non-seasonal but constant shortage. Year-round high counterfeit risk.",
        "counterfeit_risk_seasonal": {
            1: 1.5, 2: 1.5, 3: 1.5, 4: 1.5, 5: 1.5,
            6: 1.5, 7: 1.5, 8: 1.5, 9: 1.5, 10: 1.5,
            11: 1.5, 12: 1.5,
        },
    },
    "pde5_inhibitor": {
        "monthly_multiplier": {
            1: 1.00, 2: 1.15, 3: 1.00, 4: 1.00, 5: 1.00,
            6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.00,
            11: 1.10, 12: 1.05,
        },
        "peak_description": "Minor bumps during wedding season (Nov-Feb). Year-round high counterfeit risk.",
        "counterfeit_risk_seasonal": {
            1: 1.3, 2: 1.4, 3: 1.3, 4: 1.3, 5: 1.3,
            6: 1.3, 7: 1.3, 8: 1.3, 9: 1.3, 10: 1.3,
            11: 1.4, 12: 1.3,
        },
    },
}


# ============================================================================
#  CONVENIENCE FUNCTIONS
# ============================================================================

def get_demand_multiplier(month: int, category: str | None = None) -> float:
    """Return the demand multiplier for a given month (1-12) and optional drug category.

    If a category is provided and has specific seasonality data, the category-specific
    multiplier is returned. Otherwise, the overall monthly demand multiplier is used.
    """
    if category and category in DRUG_CATEGORY_SEASONALITY:
        return DRUG_CATEGORY_SEASONALITY[category]["monthly_multiplier"].get(month, 1.0)
    return SEASONAL_DEMAND_PATTERNS.get(month, {}).get("overall_demand_multiplier", 1.0)


def get_counterfeit_risk(month: int, category: str | None = None) -> float:
    """Return the counterfeit risk multiplier for a given month and optional drug category."""
    if category and category in DRUG_CATEGORY_SEASONALITY:
        return DRUG_CATEGORY_SEASONALITY[category]["counterfeit_risk_seasonal"].get(month, 1.0)
    return SEASONAL_DEMAND_PATTERNS.get(month, {}).get("counterfeit_risk_multiplier", 1.0)


def get_active_festivals(month: int, day: int | None = None) -> list[dict]:
    """Return festivals active during a given month (and optionally day)."""
    active = []
    for fest in FESTIVAL_EVENT_CALENDAR:
        if fest["typical_month"] == month or fest["typical_month"] == 0:
            if day is not None and fest["typical_month"] != 0:
                start_day, end_day = fest["typical_day_range"]
                if start_day <= day <= end_day + fest["duration_days"]:
                    active.append(fest)
            else:
                active.append(fest)
    return active


def get_active_diseases(month: int) -> list[dict]:
    """Return diseases that are active (peak or rising) during a given month."""
    active = []
    for disease in DISEASE_OUTBREAK_PATTERNS:
        all_active = disease["peak_months"] + disease.get("rising_months", [])
        if month in all_active:
            active.append(disease)
    return active


def get_disruption_risk(month: int) -> list[dict]:
    """Return supply chain disruptions that may be active during a given month."""
    active = []
    for d in SUPPLY_CHAIN_DISRUPTIONS:
        if month in d["months"] or d["months"] == [0]:
            active.append(d)
    return active


def get_hour_activity_weight(hour: int, facility_type: str = "pharmacy_retail") -> float:
    """Return the normalized activity weight for a given hour and facility type."""
    pattern = OPERATING_HOUR_PATTERNS.get(facility_type, {})
    dist = pattern.get("hourly_activity_distribution", {})
    return dist.get(hour, 0.5)


def get_anomaly_hour_modifier(hour: int) -> float:
    """Return the anomaly score modifier for a given hour (higher = more suspicious)."""
    return OPERATING_HOUR_PATTERNS["suspicious_activity"]["hourly_anomaly_score_modifier"].get(hour, 1.0)
