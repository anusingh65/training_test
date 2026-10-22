"""
Comprehensive reference data for Indian pharmaceutical supply chain actors.

Contains real Indian pharma manufacturers, distributors, pharmacy chains,
and government pharmacy systems for generating realistic synthetic
supply-chain transactions.

Sources:
    - IBEF (India Brand Equity Foundation) pharmaceutical industry reports
    - Department of Pharmaceuticals, Government of India
    - Company annual reports and investor presentations (FY2024-25)
    - Pharma industry databases (PharmaCompass, CDSCO, etc.)

Usage:
    from data.synthetic.indian_supply_chain_actors import (
        MANUFACTURERS, DISTRIBUTORS, PHARMACIES
    )
"""

# ============================================================================
#  MANUFACTURERS (57 entries)
# ============================================================================
#
#  Fields per entry:
#    name             : str   - Company legal/trade name
#    city             : str   - Headquarters city
#    state            : str   - Headquarters state
#    type             : str   - "indian_generic" | "mnc_subsidiary" | "psu" | "sme"
#    specializations  : list  - Therapeutic / manufacturing focus areas
#    revenue_tier     : str   - "large" (>5000 Cr) | "medium" (1000-5000 Cr) | "small" (<1000 Cr)
#    reputation_score : int   - 300-700 (500 = default; higher = more trusted)
# ============================================================================

MANUFACTURERS = [
    # =========================================================================
    # TOP 20 INDIAN PHARMA COMPANIES
    # =========================================================================
    {
        "name": "Sun Pharmaceutical Industries",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["formulations", "specialty_pharma", "dermatology", "ophthalmology", "oncology", "APIs"],
        "revenue_tier": "large",
        "reputation_score": 680,
    },
    {
        "name": "Cipla",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["respiratory", "anti_retroviral", "formulations", "inhalers", "oncology"],
        "revenue_tier": "large",
        "reputation_score": 670,
    },
    {
        "name": "Dr. Reddy's Laboratories",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["generics", "APIs", "biosimilars", "dermatology", "gastroenterology"],
        "revenue_tier": "large",
        "reputation_score": 665,
    },
    {
        "name": "Lupin Limited",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["cardiovascular", "diabetology", "respiratory", "anti_infectives", "CNS"],
        "revenue_tier": "large",
        "reputation_score": 650,
    },
    {
        "name": "Aurobindo Pharma",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["APIs", "generics", "anti_retroviral", "antibiotics", "CNS", "cardiovascular"],
        "revenue_tier": "large",
        "reputation_score": 640,
    },
    {
        "name": "Zydus Lifesciences",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "indian_generic",
        "specializations": ["formulations", "APIs", "vaccines", "biosimilars", "consumer_wellness"],
        "revenue_tier": "large",
        "reputation_score": 655,
    },
    {
        "name": "Torrent Pharmaceuticals",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "indian_generic",
        "specializations": ["cardiovascular", "CNS", "gastroenterology", "diabetology", "pain_management"],
        "revenue_tier": "large",
        "reputation_score": 645,
    },
    {
        "name": "Alkem Laboratories",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["anti_infectives", "gastroenterology", "pain_management", "nutraceuticals", "vitamins"],
        "revenue_tier": "large",
        "reputation_score": 635,
    },
    {
        "name": "Glenmark Pharmaceuticals",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["respiratory", "dermatology", "oncology", "generics"],
        "revenue_tier": "large",
        "reputation_score": 620,
    },
    {
        "name": "Mankind Pharma",
        "city": "New Delhi",
        "state": "Delhi",
        "type": "indian_generic",
        "specializations": ["anti_infectives", "cardiovascular", "gastroenterology", "consumer_healthcare", "dermatology"],
        "revenue_tier": "large",
        "reputation_score": 625,
    },
    {
        "name": "Biocon",
        "city": "Bengaluru",
        "state": "Karnataka",
        "type": "indian_generic",
        "specializations": ["biosimilars", "biologics", "APIs", "oncology", "diabetes", "immunology"],
        "revenue_tier": "large",
        "reputation_score": 660,
    },
    {
        "name": "Divi's Laboratories",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["APIs", "custom_synthesis", "nutraceuticals", "intermediates"],
        "revenue_tier": "large",
        "reputation_score": 670,
    },
    {
        "name": "Natco Pharma",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["oncology", "generics", "APIs", "agrochemicals", "cardiology"],
        "revenue_tier": "medium",
        "reputation_score": 610,
    },
    {
        "name": "Hetero Labs",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["anti_retroviral", "APIs", "biosimilars", "hepatitis", "cardiovascular", "oncology"],
        "revenue_tier": "large",
        "reputation_score": 630,
    },
    {
        "name": "Laurus Labs",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["APIs", "anti_retroviral", "oncology", "CDMO", "biotechnology"],
        "revenue_tier": "large",
        "reputation_score": 625,
    },
    {
        "name": "Jubilant Pharmova",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "type": "indian_generic",
        "specializations": ["radiopharmaceuticals", "CDMO", "sterile_injectables", "generics", "allergy_immunotherapy"],
        "revenue_tier": "large",
        "reputation_score": 615,
    },
    {
        "name": "Wockhardt",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["anti_infectives", "antibiotics", "biotechnology", "insulin", "formulations"],
        "revenue_tier": "medium",
        "reputation_score": 560,
    },
    {
        "name": "IPCA Laboratories",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["APIs", "formulations", "anti_malarials", "pain_management", "rheumatology", "cardiovascular"],
        "revenue_tier": "large",
        "reputation_score": 630,
    },
    {
        "name": "Ajanta Pharma",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "indian_generic",
        "specializations": ["ophthalmology", "dermatology", "cardiology", "pain_management", "anti_malarials"],
        "revenue_tier": "medium",
        "reputation_score": 620,
    },
    {
        "name": "Cadila Pharmaceuticals",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "indian_generic",
        "specializations": ["formulations", "APIs", "animal_health", "vaccines"],
        "revenue_tier": "medium",
        "reputation_score": 590,
    },

    # =========================================================================
    # MNC SUBSIDIARIES IN INDIA (11 entries)
    # =========================================================================
    {
        "name": "Pfizer India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["vaccines", "oncology", "inflammation", "rare_diseases", "internal_medicine"],
        "revenue_tier": "medium",
        "reputation_score": 690,
    },
    {
        "name": "GlaxoSmithKline Pharmaceuticals India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["vaccines", "respiratory", "anti_infectives", "dermatology"],
        "revenue_tier": "medium",
        "reputation_score": 685,
    },
    {
        "name": "Abbott India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["gastroenterology", "women_health", "metabolics", "pain_management", "vitamins"],
        "revenue_tier": "large",
        "reputation_score": 680,
    },
    {
        "name": "Sanofi India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["diabetes", "cardiovascular", "vaccines", "rare_diseases", "immunology"],
        "revenue_tier": "medium",
        "reputation_score": 680,
    },
    {
        "name": "Novartis India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["oncology", "immunology", "ophthalmology", "cardiovascular", "neuroscience"],
        "revenue_tier": "medium",
        "reputation_score": 685,
    },
    {
        "name": "AstraZeneca Pharma India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "type": "mnc_subsidiary",
        "specializations": ["cardiovascular", "respiratory", "oncology", "renal_metabolism", "diabetes"],
        "revenue_tier": "medium",
        "reputation_score": 680,
    },
    {
        "name": "Johnson & Johnson India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["medical_devices", "consumer_health", "oncology", "immunology", "neuroscience"],
        "revenue_tier": "medium",
        "reputation_score": 675,
    },
    {
        "name": "Bayer India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["cardiovascular", "oncology", "women_health", "hematology", "ophthalmology"],
        "revenue_tier": "medium",
        "reputation_score": 670,
    },
    {
        "name": "Roche Products India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["oncology", "immunology", "diagnostics", "neuroscience", "ophthalmology"],
        "revenue_tier": "medium",
        "reputation_score": 690,
    },
    {
        "name": "MSD Pharmaceuticals India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "mnc_subsidiary",
        "specializations": ["vaccines", "oncology", "infectious_diseases", "hospital_acute_care"],
        "revenue_tier": "medium",
        "reputation_score": 680,
    },
    {
        "name": "Eli Lilly India",
        "city": "Gurugram",
        "state": "Haryana",
        "type": "mnc_subsidiary",
        "specializations": ["diabetes", "oncology", "neuroscience", "immunology"],
        "revenue_tier": "medium",
        "reputation_score": 680,
    },

    # =========================================================================
    # PUBLIC SECTOR UNITS (5 entries)
    # =========================================================================
    {
        "name": "Karnataka Antibiotics & Pharmaceuticals Ltd (KAPL)",
        "city": "Bengaluru",
        "state": "Karnataka",
        "type": "psu",
        "specializations": ["antibiotics", "anti_diabetics", "cardiovascular", "pain_management", "animal_health"],
        "revenue_tier": "small",
        "reputation_score": 520,
    },
    {
        "name": "Bengal Chemicals & Pharmaceuticals Ltd (BCPL)",
        "city": "Kolkata",
        "state": "West Bengal",
        "type": "psu",
        "specializations": ["chemicals", "pharmaceuticals", "cosmetics", "home_products"],
        "revenue_tier": "small",
        "reputation_score": 430,
    },
    {
        "name": "Hindustan Antibiotics Ltd (HAL)",
        "city": "Pune",
        "state": "Maharashtra",
        "type": "psu",
        "specializations": ["antibiotics", "formulations", "agro_vet_products"],
        "revenue_tier": "small",
        "reputation_score": 410,
    },
    {
        "name": "Indian Drugs & Pharmaceuticals Ltd (IDPL)",
        "city": "Gurugram",
        "state": "Haryana",
        "type": "psu",
        "specializations": ["essential_drugs", "antibiotics", "anti_tuberculosis", "synthetic_drugs"],
        "revenue_tier": "small",
        "reputation_score": 380,
    },
    {
        "name": "Rajasthan Drugs & Pharmaceuticals Ltd (RDPL)",
        "city": "Jaipur",
        "state": "Rajasthan",
        "type": "psu",
        "specializations": ["essential_drugs", "formulations", "oral_dosage_forms"],
        "revenue_tier": "small",
        "reputation_score": 380,
    },

    # =========================================================================
    # SMALLER / REGIONAL MANUFACTURERS (21 entries)
    # =========================================================================
    {
        "name": "Micro Labs",
        "city": "Bengaluru",
        "state": "Karnataka",
        "type": "sme",
        "specializations": ["cardiology", "diabetology", "pain_management", "dermatology", "ophthalmology", "neurology"],
        "revenue_tier": "large",
        "reputation_score": 600,
    },
    {
        "name": "Macleods Pharmaceuticals",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["anti_infectives", "anti_tuberculosis", "anti_malarials", "cardiovascular", "diabetology"],
        "revenue_tier": "large",
        "reputation_score": 590,
    },
    {
        "name": "Intas Pharmaceuticals",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "indian_generic",
        "specializations": ["biosimilars", "neuropsychiatry", "oncology", "APIs", "formulations"],
        "revenue_tier": "large",
        "reputation_score": 640,
    },
    {
        "name": "Emcure Pharmaceuticals",
        "city": "Pune",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["gynaecology", "cardiovascular", "oncology", "HIV_antivirals", "vitamins"],
        "revenue_tier": "large",
        "reputation_score": 600,
    },
    {
        "name": "Eris Lifesciences",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "sme",
        "specializations": ["chronic_therapies", "cardiovascular", "diabetology", "gastroenterology", "vitamins"],
        "revenue_tier": "medium",
        "reputation_score": 590,
    },
    {
        "name": "Aarti Drugs",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["APIs", "intermediates", "anti_infectives", "anti_diabetics", "anti_hypertensives"],
        "revenue_tier": "medium",
        "reputation_score": 560,
    },
    {
        "name": "Granules India",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "sme",
        "specializations": ["APIs", "pharmaceutical_formulation_intermediates", "finished_dosage", "paracetamol", "metformin"],
        "revenue_tier": "medium",
        "reputation_score": 575,
    },
    {
        "name": "Suven Pharmaceuticals",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "sme",
        "specializations": ["CDMO", "drug_discovery", "APIs", "custom_synthesis", "fine_chemicals"],
        "revenue_tier": "medium",
        "reputation_score": 580,
    },
    {
        "name": "Strides Pharma Science",
        "city": "Bengaluru",
        "state": "Karnataka",
        "type": "sme",
        "specializations": ["soft_gelatin_capsules", "regulated_markets_generics", "injectables", "APIs"],
        "revenue_tier": "medium",
        "reputation_score": 570,
    },
    {
        "name": "MSN Laboratories",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "sme",
        "specializations": ["APIs", "formulations", "cardiovascular", "anti_diabetics", "anti_infectives"],
        "revenue_tier": "medium",
        "reputation_score": 555,
    },
    {
        "name": "Piramal Pharma",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["CDMO", "complex_hospital_generics", "APIs", "inhalation_anaesthetics"],
        "revenue_tier": "medium",
        "reputation_score": 610,
    },
    {
        "name": "Gland Pharma",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "indian_generic",
        "specializations": ["injectables", "generic_injectables", "ophthalmic_solutions", "oncology_injectables"],
        "revenue_tier": "large",
        "reputation_score": 635,
    },
    {
        "name": "Solara Active Pharma Sciences",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "type": "sme",
        "specializations": ["APIs", "CRAMS", "ibuprofen", "ranitidine", "gabapentin"],
        "revenue_tier": "medium",
        "reputation_score": 540,
    },
    {
        "name": "Shilpa Medicare",
        "city": "Raichur",
        "state": "Karnataka",
        "type": "sme",
        "specializations": ["oncology_APIs", "formulations", "CDMO", "peptides", "biologics"],
        "revenue_tier": "medium",
        "reputation_score": 550,
    },
    {
        "name": "Bliss GVS Pharma",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["suppositories", "pessaries", "soft_gelatin_capsules", "APIs"],
        "revenue_tier": "small",
        "reputation_score": 520,
    },
    {
        "name": "Unichem Laboratories",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["gastroenterology", "cardiology", "neurology", "APIs", "formulations"],
        "revenue_tier": "medium",
        "reputation_score": 555,
    },
    {
        "name": "FDC Limited",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["oral_rehydration_salts", "ophthalmic", "antibiotics", "energy_drinks"],
        "revenue_tier": "medium",
        "reputation_score": 560,
    },
    {
        "name": "JB Chemicals & Pharmaceuticals",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["cardio_metabolic", "gastroenterology", "herbal_remedies", "APIs"],
        "revenue_tier": "medium",
        "reputation_score": 575,
    },
    {
        "name": "Indoco Remedies",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["gastroenterology", "respiratory", "dentistry", "diabetology", "women_health"],
        "revenue_tier": "medium",
        "reputation_score": 550,
    },
    {
        "name": "Marksans Pharma",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["OTC_drugs", "cardiovascular", "oncology", "anti_diabetics", "CNS"],
        "revenue_tier": "medium",
        "reputation_score": 530,
    },
    {
        "name": "RPG Life Sciences",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "sme",
        "specializations": ["immunosuppressants", "gastroenterology", "pain_management", "nephrology", "APIs"],
        "revenue_tier": "small",
        "reputation_score": 520,
    },
    {
        "name": "Alembic Pharmaceuticals",
        "city": "Vadodara",
        "state": "Gujarat",
        "type": "indian_generic",
        "specializations": ["dermatology", "cardiology", "gastroenterology", "oncology", "APIs", "animal_health"],
        "revenue_tier": "large",
        "reputation_score": 610,
    },
]


# ============================================================================
#  DISTRIBUTORS (45 entries)
# ============================================================================
#
#  Fields per entry:
#    name             : str   - Company / entity name
#    city             : str   - Primary office city
#    state            : str   - Primary office state
#    type             : str   - "c&f_agent" | "super_stockist" | "regional_distributor"
#                               | "cold_chain_specialist" | "hospital_supplier"
#    coverage         : list  - States served
#    specialization   : str   - Focus area (if any)
#    reputation_score : int   - 300-700
# ============================================================================

DISTRIBUTORS = [
    # =========================================================================
    # REAL / MAJOR NATIONAL-LEVEL DISTRIBUTION COMPANIES
    # =========================================================================
    {
        "name": "Shreya Life Sciences Distribution",
        "city": "Aurangabad",
        "state": "Maharashtra",
        "type": "c&f_agent",
        "coverage": ["Maharashtra", "Gujarat", "Madhya Pradesh", "Rajasthan", "Goa"],
        "specialization": "insulin, hepatitis vaccines, recombinant biologics",
        "reputation_score": 600,
    },
    {
        "name": "Khandelwal Laboratories Distribution",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "super_stockist",
        "coverage": ["Maharashtra", "Gujarat", "Karnataka", "Goa"],
        "specialization": "oncology formulations, branded generics",
        "reputation_score": 580,
    },
    {
        "name": "Soham Distributors Pvt Ltd",
        "city": "Kolkata",
        "state": "West Bengal",
        "type": "c&f_agent",
        "coverage": ["West Bengal", "Odisha", "Jharkhand", "Bihar", "Assam", "Meghalaya", "Tripura", "Nagaland", "Manipur", "Mizoram", "Arunachal Pradesh", "Sikkim"],
        "specialization": "full-line pharma distribution (Cipla C&F partner)",
        "reputation_score": 610,
    },
    {
        "name": "Medilinks Logistics (Dvijay Group)",
        "city": "Nashik",
        "state": "Maharashtra",
        "type": "c&f_agent",
        "coverage": ["Maharashtra", "Goa"],
        "specialization": "specialty medicines, anti-cancer, HIV, nephrology",
        "reputation_score": 585,
    },
    {
        "name": "GNH India",
        "city": "New Delhi",
        "state": "Delhi",
        "type": "super_stockist",
        "coverage": ["Delhi", "Uttar Pradesh", "Haryana", "Punjab", "Rajasthan", "Uttarakhand"],
        "specialization": "critical medicines wholesale, international supply",
        "reputation_score": 590,
    },

    # =========================================================================
    # COLD CHAIN SPECIALISTS
    # =========================================================================
    {
        "name": "Snowman Logistics Pharma Division",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "cold_chain_specialist",
        "coverage": ["Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "Delhi", "West Bengal"],
        "specialization": "temperature-controlled pharma logistics, vaccines, biologics",
        "reputation_score": 620,
    },
    {
        "name": "Blue Dart Med Express",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "cold_chain_specialist",
        "coverage": ["Pan-India"],
        "specialization": "express pharma shipments, temperature-controlled last-mile",
        "reputation_score": 630,
    },
    {
        "name": "Sequel Logistics",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "cold_chain_specialist",
        "coverage": ["Pan-India"],
        "specialization": "pharma cold chain, clinical trial logistics, GDP-compliant",
        "reputation_score": 625,
    },

    # =========================================================================
    # HOSPITAL SUPPLIERS
    # =========================================================================
    {
        "name": "Zota Healthcare Distribution",
        "city": "Surat",
        "state": "Gujarat",
        "type": "hospital_supplier",
        "coverage": ["Gujarat", "Maharashtra", "Rajasthan", "Madhya Pradesh"],
        "specialization": "hospital bulk supply, generic medicines, surgical consumables",
        "reputation_score": 570,
    },
    {
        "name": "Aster DM Healthcare Supply Chain",
        "city": "Kochi",
        "state": "Kerala",
        "type": "hospital_supplier",
        "coverage": ["Kerala", "Karnataka", "Tamil Nadu", "Andhra Pradesh", "Telangana"],
        "specialization": "hospital pharmacy supply, institutional medicines",
        "reputation_score": 610,
    },
    {
        "name": "Apollo Health & Lifestyle Distribution",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "hospital_supplier",
        "coverage": ["Telangana", "Andhra Pradesh", "Tamil Nadu", "Karnataka", "Maharashtra"],
        "specialization": "hospital group supply chain, specialty drugs",
        "reputation_score": 640,
    },

    # =========================================================================
    # REGIONAL C&F AGENTS (State-wise coverage)
    # =========================================================================
    {
        "name": "Rajput Pharma Distributors",
        "city": "Jaipur",
        "state": "Rajasthan",
        "type": "c&f_agent",
        "coverage": ["Rajasthan"],
        "specialization": "general formulations, OTC medicines",
        "reputation_score": 530,
    },
    {
        "name": "Punjab Drug House",
        "city": "Chandigarh",
        "state": "Punjab",
        "type": "c&f_agent",
        "coverage": ["Punjab", "Haryana", "Himachal Pradesh", "Chandigarh"],
        "specialization": "general pharma, anti-infectives",
        "reputation_score": 550,
    },
    {
        "name": "Sai Pharma Distributors",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "type": "regional_distributor",
        "coverage": ["Uttar Pradesh", "Uttarakhand"],
        "specialization": "general formulations, chronic therapy drugs",
        "reputation_score": 520,
    },
    {
        "name": "Bharat Pharma Agencies",
        "city": "Patna",
        "state": "Bihar",
        "type": "c&f_agent",
        "coverage": ["Bihar", "Jharkhand"],
        "specialization": "essential medicines, government supply",
        "reputation_score": 500,
    },
    {
        "name": "Vishwa Pharma Distributors",
        "city": "Indore",
        "state": "Madhya Pradesh",
        "type": "regional_distributor",
        "coverage": ["Madhya Pradesh", "Chhattisgarh"],
        "specialization": "branded generics, OTC",
        "reputation_score": 530,
    },
    {
        "name": "Deccan Pharma Agencies",
        "city": "Hyderabad",
        "state": "Telangana",
        "type": "super_stockist",
        "coverage": ["Telangana", "Andhra Pradesh"],
        "specialization": "APIs, formulations, institutional supply",
        "reputation_score": 560,
    },
    {
        "name": "Southern Pharma Distributors",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "type": "c&f_agent",
        "coverage": ["Tamil Nadu", "Puducherry"],
        "specialization": "general pharma, diabetology, cardiology drugs",
        "reputation_score": 570,
    },
    {
        "name": "Karnataka Pharma Wholesale",
        "city": "Bengaluru",
        "state": "Karnataka",
        "type": "super_stockist",
        "coverage": ["Karnataka"],
        "specialization": "generic medicines, anti-infectives",
        "reputation_score": 555,
    },
    {
        "name": "Malabar Pharma Agencies",
        "city": "Kochi",
        "state": "Kerala",
        "type": "regional_distributor",
        "coverage": ["Kerala"],
        "specialization": "general pharma, ayurvedic products",
        "reputation_score": 550,
    },
    {
        "name": "Eastern Pharma Corporation",
        "city": "Guwahati",
        "state": "Assam",
        "type": "c&f_agent",
        "coverage": ["Assam", "Meghalaya", "Nagaland", "Manipur", "Mizoram", "Arunachal Pradesh", "Tripura"],
        "specialization": "essential medicines distribution to Northeast India",
        "reputation_score": 510,
    },
    {
        "name": "Gujarat Pharma Corporation",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "super_stockist",
        "coverage": ["Gujarat", "Daman & Diu", "Dadra & Nagar Haveli"],
        "specialization": "formulations, bulk drug intermediates",
        "reputation_score": 570,
    },
    {
        "name": "Orissa Drug Traders",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "type": "regional_distributor",
        "coverage": ["Odisha"],
        "specialization": "essential medicines, government hospital supply",
        "reputation_score": 500,
    },
    {
        "name": "Goyal Medicos",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "type": "regional_distributor",
        "coverage": ["Uttarakhand", "western Uttar Pradesh"],
        "specialization": "general formulations, seasonal medicines",
        "reputation_score": 510,
    },
    {
        "name": "Chhattisgarh Drug Distributors",
        "city": "Raipur",
        "state": "Chhattisgarh",
        "type": "regional_distributor",
        "coverage": ["Chhattisgarh"],
        "specialization": "tribal area essential drug supply",
        "reputation_score": 490,
    },
    {
        "name": "Goa Pharma & Drug Distributors",
        "city": "Panaji",
        "state": "Goa",
        "type": "regional_distributor",
        "coverage": ["Goa"],
        "specialization": "tourist-area pharma supply, general medicines",
        "reputation_score": 540,
    },
    {
        "name": "J&K Pharma Agencies",
        "city": "Jammu",
        "state": "Jammu & Kashmir",
        "type": "regional_distributor",
        "coverage": ["Jammu & Kashmir", "Ladakh"],
        "specialization": "high-altitude essential drug supply, cold chain",
        "reputation_score": 490,
    },
    {
        "name": "Sikkim Drug Distributors",
        "city": "Gangtok",
        "state": "Sikkim",
        "type": "regional_distributor",
        "coverage": ["Sikkim"],
        "specialization": "hill-region pharma supply",
        "reputation_score": 480,
    },
    {
        "name": "Sugam Pharma Distributors",
        "city": "Nagpur",
        "state": "Maharashtra",
        "type": "super_stockist",
        "coverage": ["Maharashtra (Vidarbha)", "Madhya Pradesh (eastern)"],
        "specialization": "general pharma, chronic therapy drugs",
        "reputation_score": 545,
    },
    {
        "name": "Mehta Drug House",
        "city": "Varanasi",
        "state": "Uttar Pradesh",
        "type": "regional_distributor",
        "coverage": ["Eastern Uttar Pradesh"],
        "specialization": "general medicines, ayurvedic products",
        "reputation_score": 510,
    },
    {
        "name": "Andhra Pharma Wholesale",
        "city": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "type": "regional_distributor",
        "coverage": ["Andhra Pradesh"],
        "specialization": "institutional supply, branded generics",
        "reputation_score": 540,
    },
    {
        "name": "Bengal Drug Company",
        "city": "Kolkata",
        "state": "West Bengal",
        "type": "super_stockist",
        "coverage": ["West Bengal"],
        "specialization": "general pharma, anti-infectives, OTC",
        "reputation_score": 540,
    },
    {
        "name": "Avadh Pharma Services",
        "city": "Kanpur",
        "state": "Uttar Pradesh",
        "type": "c&f_agent",
        "coverage": ["Uttar Pradesh (central/western)"],
        "specialization": "cardiovascular, diabetology formulations",
        "reputation_score": 515,
    },
    {
        "name": "National Health Distributors",
        "city": "New Delhi",
        "state": "Delhi",
        "type": "super_stockist",
        "coverage": ["Delhi", "NCR"],
        "specialization": "multi-brand stockist, hospital supply",
        "reputation_score": 560,
    },
    {
        "name": "Poona Drug House",
        "city": "Pune",
        "state": "Maharashtra",
        "type": "c&f_agent",
        "coverage": ["Maharashtra (western)"],
        "specialization": "general formulations, surgical supplies",
        "reputation_score": 550,
    },
    {
        "name": "Coimbatore Drug Traders",
        "city": "Coimbatore",
        "state": "Tamil Nadu",
        "type": "regional_distributor",
        "coverage": ["Tamil Nadu (western)", "Kerala (Palakkad)"],
        "specialization": "general pharma, diabetology",
        "reputation_score": 530,
    },
    {
        "name": "Taran Pharma Solutions",
        "city": "Amritsar",
        "state": "Punjab",
        "type": "regional_distributor",
        "coverage": ["Punjab (northern)", "Jammu"],
        "specialization": "anti-infectives, respiratory medicines",
        "reputation_score": 510,
    },
    {
        "name": "Rajdhani Drug Distributors",
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "type": "c&f_agent",
        "coverage": ["Madhya Pradesh"],
        "specialization": "government tender supply, essential medicines",
        "reputation_score": 520,
    },
    {
        "name": "Maharashtra Drug Distributors Association",
        "city": "Mumbai",
        "state": "Maharashtra",
        "type": "super_stockist",
        "coverage": ["Maharashtra"],
        "specialization": "multi-company stockist, all therapeutic segments",
        "reputation_score": 565,
    },
    {
        "name": "Telangana Pharma Wholesale Corp",
        "city": "Warangal",
        "state": "Telangana",
        "type": "regional_distributor",
        "coverage": ["Telangana (non-Hyderabad)"],
        "specialization": "rural pharma supply, essential medicines",
        "reputation_score": 500,
    },
    {
        "name": "Haryana Drug House",
        "city": "Ambala",
        "state": "Haryana",
        "type": "regional_distributor",
        "coverage": ["Haryana"],
        "specialization": "general pharma, OTC, nutraceuticals",
        "reputation_score": 525,
    },
    {
        "name": "Ranchi Pharma Distributors",
        "city": "Ranchi",
        "state": "Jharkhand",
        "type": "regional_distributor",
        "coverage": ["Jharkhand"],
        "specialization": "essential medicines, tribal area supply",
        "reputation_score": 490,
    },
    {
        "name": "Capital Pharma Logistics",
        "city": "Guwahati",
        "state": "Assam",
        "type": "c&f_agent",
        "coverage": ["Assam", "Meghalaya"],
        "specialization": "general pharma, cold chain vaccines",
        "reputation_score": 505,
    },
    {
        "name": "Pioneer Drug Distributors",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "type": "c&f_agent",
        "coverage": ["Gujarat", "Rajasthan (southern)"],
        "specialization": "chronic therapy drugs, branded generics",
        "reputation_score": 555,
    },
    {
        "name": "Trivandrum Medical Stores",
        "city": "Thiruvananthapuram",
        "state": "Kerala",
        "type": "hospital_supplier",
        "coverage": ["Kerala", "Tamil Nadu (Kanyakumari)"],
        "specialization": "hospital institutional supply, ayurvedic medicines, surgical items",
        "reputation_score": 545,
    },
]


# ============================================================================
#  PHARMACIES / RETAIL (35 entries)
# ============================================================================
#
#  Fields per entry:
#    name             : str   - Chain / entity name
#    type             : str   - "chain" | "hospital_pharmacy" | "online_pharmacy"
#                               | "independent" | "government_pharmacy"
#    num_outlets      : int   - Approximate number of outlets / outlets
#    states           : list  - States of operation
#    reputation_score : int   - 300-700
# ============================================================================

PHARMACIES = [
    # =========================================================================
    # MAJOR RETAIL PHARMACY CHAINS
    # =========================================================================
    {
        "name": "Apollo Pharmacy",
        "type": "chain",
        "num_outlets": 6000,
        "states": [
            "Andhra Pradesh", "Telangana", "Tamil Nadu", "Karnataka",
            "Kerala", "Maharashtra", "Gujarat", "Delhi", "Uttar Pradesh",
            "West Bengal", "Odisha", "Madhya Pradesh", "Rajasthan",
            "Chhattisgarh", "Bihar", "Jharkhand", "Assam",
            "Himachal Pradesh", "Punjab", "Haryana", "Uttarakhand",
        ],
        "reputation_score": 660,
    },
    {
        "name": "MedPlus",
        "type": "chain",
        "num_outlets": 4230,
        "states": [
            "Telangana", "Andhra Pradesh", "Tamil Nadu", "Karnataka",
            "Maharashtra", "West Bengal", "Odisha", "Bihar",
            "Madhya Pradesh", "Rajasthan",
        ],
        "reputation_score": 640,
    },
    {
        "name": "Wellness Forever",
        "type": "chain",
        "num_outlets": 407,
        "states": ["Maharashtra", "Gujarat", "Karnataka", "Goa"],
        "reputation_score": 610,
    },
    {
        "name": "Frank Ross Pharmacy",
        "type": "chain",
        "num_outlets": 120,
        "states": ["West Bengal", "Odisha", "Assam", "Jharkhand"],
        "reputation_score": 595,
    },
    {
        "name": "Noble Plus Pharmacy",
        "type": "chain",
        "num_outlets": 60,
        "states": ["Maharashtra"],
        "reputation_score": 570,
    },
    {
        "name": "DavaIndia (Zota Healthcare)",
        "type": "chain",
        "num_outlets": 2000,
        "states": [
            "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh",
            "Maharashtra", "Karnataka", "Delhi", "Haryana",
            "Punjab", "Uttarakhand", "Bihar", "West Bengal",
            "Telangana", "Andhra Pradesh", "Tamil Nadu",
            "Jharkhand", "Odisha", "Chhattisgarh", "Assam",
            "Himachal Pradesh", "Kerala", "Goa", "Chandigarh",
            "Jammu & Kashmir", "Puducherry",
        ],
        "reputation_score": 560,
    },
    {
        "name": "Guardian Pharmacy",
        "type": "chain",
        "num_outlets": 230,
        "states": [
            "Delhi", "Haryana", "Uttar Pradesh", "Rajasthan",
            "Punjab", "Maharashtra", "Karnataka", "Telangana",
            "Gujarat", "Jharkhand",
        ],
        "reputation_score": 580,
    },
    {
        "name": "Generico (True Generics)",
        "type": "chain",
        "num_outlets": 250,
        "states": ["Maharashtra", "Gujarat", "Rajasthan", "Madhya Pradesh", "Karnataka"],
        "reputation_score": 550,
    },
    {
        "name": "MedKart Pharmacy",
        "type": "chain",
        "num_outlets": 100,
        "states": ["Gujarat", "Rajasthan", "Maharashtra"],
        "reputation_score": 540,
    },
    {
        "name": "StoreHealth Pharmacy",
        "type": "chain",
        "num_outlets": 50,
        "states": ["Tamil Nadu", "Karnataka"],
        "reputation_score": 530,
    },

    # =========================================================================
    # ONLINE PHARMACIES
    # =========================================================================
    {
        "name": "Netmeds (Reliance)",
        "type": "online_pharmacy",
        "num_outlets": 500,
        "states": ["Pan-India"],
        "reputation_score": 620,
    },
    {
        "name": "PharmEasy",
        "type": "online_pharmacy",
        "num_outlets": 0,
        "states": ["Pan-India"],
        "reputation_score": 610,
    },
    {
        "name": "1mg (Tata Health)",
        "type": "online_pharmacy",
        "num_outlets": 0,
        "states": ["Pan-India"],
        "reputation_score": 615,
    },
    {
        "name": "Apollo 24|7",
        "type": "online_pharmacy",
        "num_outlets": 0,
        "states": ["Pan-India"],
        "reputation_score": 640,
    },
    {
        "name": "MedPlus Mart Online",
        "type": "online_pharmacy",
        "num_outlets": 0,
        "states": ["Pan-India"],
        "reputation_score": 620,
    },

    # =========================================================================
    # HOSPITAL PHARMACIES (Major Hospital Chains)
    # =========================================================================
    {
        "name": "Apollo Hospitals Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 73,
        "states": [
            "Andhra Pradesh", "Telangana", "Tamil Nadu", "Karnataka",
            "Maharashtra", "Delhi", "West Bengal", "Odisha",
        ],
        "reputation_score": 670,
    },
    {
        "name": "Fortis Healthcare Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 28,
        "states": [
            "Delhi", "Haryana", "Punjab", "Rajasthan",
            "Uttar Pradesh", "West Bengal", "Karnataka", "Kerala",
        ],
        "reputation_score": 660,
    },
    {
        "name": "Max Healthcare Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 17,
        "states": ["Delhi", "Uttar Pradesh", "Haryana", "Punjab", "Uttarakhand"],
        "reputation_score": 655,
    },
    {
        "name": "Manipal Hospitals Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 30,
        "states": ["Karnataka", "Tamil Nadu", "Andhra Pradesh", "Delhi", "Goa", "Maharashtra"],
        "reputation_score": 650,
    },
    {
        "name": "AIIMS Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 23,
        "states": [
            "Delhi", "Uttarakhand", "Bihar", "Rajasthan",
            "Madhya Pradesh", "Chhattisgarh", "Jharkhand",
            "Telangana", "Andhra Pradesh", "Jammu & Kashmir",
            "Assam", "Gujarat", "Tamil Nadu", "West Bengal",
            "Maharashtra", "Odisha", "Punjab", "Uttar Pradesh",
        ],
        "reputation_score": 680,
    },
    {
        "name": "Narayana Health Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 21,
        "states": ["Karnataka", "West Bengal", "Andhra Pradesh", "Rajasthan", "Maharashtra"],
        "reputation_score": 640,
    },
    {
        "name": "Medanta Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 5,
        "states": ["Haryana", "Uttar Pradesh", "Bihar"],
        "reputation_score": 650,
    },

    # =========================================================================
    # GOVERNMENT PHARMACIES
    # =========================================================================
    {
        "name": "Pradhan Mantri Bhartiya Janaushadhi Kendra",
        "type": "government_pharmacy",
        "num_outlets": 12000,
        "states": [
            "Uttar Pradesh", "Gujarat", "Rajasthan", "Madhya Pradesh",
            "Maharashtra", "Karnataka", "Tamil Nadu", "West Bengal",
            "Andhra Pradesh", "Telangana", "Bihar", "Odisha",
            "Kerala", "Punjab", "Haryana", "Chhattisgarh",
            "Jharkhand", "Uttarakhand", "Assam", "Himachal Pradesh",
            "Delhi", "Goa", "Jammu & Kashmir", "Manipur",
            "Meghalaya", "Tripura", "Nagaland", "Mizoram",
            "Arunachal Pradesh", "Sikkim", "Puducherry",
            "Andaman & Nicobar", "Chandigarh", "Ladakh",
        ],
        "reputation_score": 600,
    },
    {
        "name": "CGHS Wellness Centre Pharmacy",
        "type": "government_pharmacy",
        "num_outlets": 400,
        "states": [
            "Delhi", "Maharashtra", "Tamil Nadu", "West Bengal",
            "Karnataka", "Telangana", "Kerala", "Gujarat",
            "Uttar Pradesh", "Madhya Pradesh", "Bihar",
            "Rajasthan", "Punjab", "Haryana", "Uttarakhand",
            "Odisha", "Jharkhand", "Chhattisgarh", "Goa",
            "Assam", "Himachal Pradesh", "Jammu & Kashmir",
            "Andhra Pradesh", "Chandigarh", "Puducherry",
        ],
        "reputation_score": 620,
    },
    {
        "name": "ECHS Polyclinic Pharmacy",
        "type": "government_pharmacy",
        "num_outlets": 433,
        "states": [
            "Delhi", "Maharashtra", "Tamil Nadu", "Karnataka",
            "Uttar Pradesh", "Rajasthan", "Punjab", "Haryana",
            "Madhya Pradesh", "Gujarat", "West Bengal", "Kerala",
            "Andhra Pradesh", "Telangana", "Bihar", "Jharkhand",
            "Odisha", "Chhattisgarh", "Uttarakhand", "Assam",
            "Himachal Pradesh", "Jammu & Kashmir", "Goa",
            "Manipur", "Meghalaya", "Nagaland", "Tripura",
            "Sikkim", "Chandigarh",
        ],
        "reputation_score": 615,
    },
    {
        "name": "ESI (Employees State Insurance) Hospital Pharmacy",
        "type": "government_pharmacy",
        "num_outlets": 155,
        "states": [
            "Delhi", "Maharashtra", "Tamil Nadu", "Karnataka",
            "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh",
            "Madhya Pradesh", "Andhra Pradesh", "Telangana",
            "Kerala", "Punjab", "Haryana", "Bihar",
            "Jharkhand", "Odisha", "Chhattisgarh",
        ],
        "reputation_score": 570,
    },
    {
        "name": "Railway Hospital Pharmacy (Indian Railways)",
        "type": "government_pharmacy",
        "num_outlets": 125,
        "states": [
            "Delhi", "Maharashtra", "West Bengal", "Tamil Nadu",
            "Uttar Pradesh", "Bihar", "Rajasthan", "Gujarat",
            "Madhya Pradesh", "Andhra Pradesh", "Karnataka",
            "Kerala", "Punjab", "Haryana", "Jharkhand",
            "Odisha", "Chhattisgarh", "Assam",
        ],
        "reputation_score": 560,
    },
    {
        "name": "Military Hospital Pharmacy (Armed Forces Medical Stores Depot)",
        "type": "government_pharmacy",
        "num_outlets": 50,
        "states": [
            "Delhi", "Maharashtra", "Tamil Nadu", "Karnataka",
            "Uttar Pradesh", "Punjab", "Rajasthan", "Madhya Pradesh",
            "West Bengal", "Jammu & Kashmir", "Himachal Pradesh",
            "Uttarakhand", "Assam",
        ],
        "reputation_score": 650,
    },
    {
        "name": "State Government Hospital Pharmacy (PHC/CHC)",
        "type": "government_pharmacy",
        "num_outlets": 30000,
        "states": [
            "Uttar Pradesh", "Bihar", "Madhya Pradesh", "Rajasthan",
            "Maharashtra", "Tamil Nadu", "Karnataka", "Gujarat",
            "West Bengal", "Andhra Pradesh", "Telangana", "Odisha",
            "Kerala", "Punjab", "Haryana", "Jharkhand",
            "Chhattisgarh", "Uttarakhand", "Assam",
            "Himachal Pradesh", "Jammu & Kashmir", "Delhi",
            "Goa", "Manipur", "Meghalaya", "Tripura",
            "Nagaland", "Mizoram", "Arunachal Pradesh", "Sikkim",
        ],
        "reputation_score": 500,
    },

    # =========================================================================
    # INDEPENDENT PHARMACIES (Representative types)
    # =========================================================================
    {
        "name": "Independent Urban Pharmacy (Metro City)",
        "type": "independent",
        "num_outlets": 1,
        "states": [
            "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu",
            "Telangana", "Gujarat", "West Bengal",
        ],
        "reputation_score": 510,
    },
    {
        "name": "Independent Semi-Urban Pharmacy (Tier 2/3 City)",
        "type": "independent",
        "num_outlets": 1,
        "states": [
            "Uttar Pradesh", "Madhya Pradesh", "Rajasthan",
            "Bihar", "Jharkhand", "Odisha", "Punjab", "Haryana",
            "Chhattisgarh", "Uttarakhand", "Assam",
        ],
        "reputation_score": 480,
    },
    {
        "name": "Independent Rural Pharmacy (Village/Taluka Level)",
        "type": "independent",
        "num_outlets": 1,
        "states": [
            "Uttar Pradesh", "Bihar", "Madhya Pradesh", "Rajasthan",
            "Odisha", "Chhattisgarh", "Jharkhand", "West Bengal",
            "Andhra Pradesh", "Telangana", "Maharashtra", "Karnataka",
            "Tamil Nadu", "Kerala", "Gujarat", "Punjab",
            "Haryana", "Assam",
        ],
        "reputation_score": 450,
    },
    {
        "name": "Independent Tier-1 City Chemist",
        "type": "independent",
        "num_outlets": 1,
        "states": [
            "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu",
            "Telangana", "West Bengal", "Gujarat",
        ],
        "reputation_score": 530,
    },
    {
        "name": "Cooperative Medical Store (State Cooperative)",
        "type": "independent",
        "num_outlets": 5,
        "states": [
            "Kerala", "Tamil Nadu", "Karnataka", "West Bengal",
            "Odisha", "Andhra Pradesh",
        ],
        "reputation_score": 520,
    },
    {
        "name": "Charitable Trust Hospital Pharmacy",
        "type": "hospital_pharmacy",
        "num_outlets": 3,
        "states": [
            "Maharashtra", "Gujarat", "Rajasthan", "Delhi",
            "Tamil Nadu", "Karnataka",
        ],
        "reputation_score": 600,
    },
]


# ============================================================================
#  CONVENIENCE LOOKUPS
# ============================================================================

MANUFACTURERS_BY_TYPE = {
    "indian_generic": [m for m in MANUFACTURERS if m["type"] == "indian_generic"],
    "mnc_subsidiary": [m for m in MANUFACTURERS if m["type"] == "mnc_subsidiary"],
    "psu":            [m for m in MANUFACTURERS if m["type"] == "psu"],
    "sme":            [m for m in MANUFACTURERS if m["type"] == "sme"],
}

DISTRIBUTORS_BY_TYPE = {
    "c&f_agent":           [d for d in DISTRIBUTORS if d["type"] == "c&f_agent"],
    "super_stockist":      [d for d in DISTRIBUTORS if d["type"] == "super_stockist"],
    "regional_distributor": [d for d in DISTRIBUTORS if d["type"] == "regional_distributor"],
    "cold_chain_specialist": [d for d in DISTRIBUTORS if d["type"] == "cold_chain_specialist"],
    "hospital_supplier":   [d for d in DISTRIBUTORS if d["type"] == "hospital_supplier"],
}

PHARMACIES_BY_TYPE = {
    "chain":              [p for p in PHARMACIES if p["type"] == "chain"],
    "hospital_pharmacy":  [p for p in PHARMACIES if p["type"] == "hospital_pharmacy"],
    "online_pharmacy":    [p for p in PHARMACIES if p["type"] == "online_pharmacy"],
    "government_pharmacy": [p for p in PHARMACIES if p["type"] == "government_pharmacy"],
    "independent":        [p for p in PHARMACIES if p["type"] == "independent"],
}

# All Indian states and UTs that appear in the data
ALL_STATES = sorted({
    state
    for actor_list in [DISTRIBUTORS, PHARMACIES]
    for actor in actor_list
    for state in (actor.get("coverage", []) or actor.get("states", []))
    if state != "Pan-India"
})


# ============================================================================
#  Quick stats when run directly
# ============================================================================

if __name__ == "__main__":
    print(f"=== Indian Pharma Supply Chain Actors ===")
    print(f"  Manufacturers:  {len(MANUFACTURERS)}")
    for t, lst in MANUFACTURERS_BY_TYPE.items():
        print(f"    {t}: {len(lst)}")
    print(f"  Distributors:   {len(DISTRIBUTORS)}")
    for t, lst in DISTRIBUTORS_BY_TYPE.items():
        print(f"    {t}: {len(lst)}")
    print(f"  Pharmacies:     {len(PHARMACIES)}")
    for t, lst in PHARMACIES_BY_TYPE.items():
        print(f"    {t}: {len(lst)}")
    print(f"  States covered: {len(ALL_STATES)}")
    print(f"  State list: {ALL_STATES}")
