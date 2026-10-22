"""
Adverse Event Monitoring Routes for MediChain AI Engine.

Endpoints:
  GET /api/adverse-events/{drug_name}  -- Analyse adverse-event signals from
                                          OpenFDA FAERS for a given drug.
  GET /api/drug-identity/{drug_name}   -- Retrieve authoritative NDC directory
                                          entry for drug identity verification.
  GET /api/drug-recalls/{drug_name}    -- Check active FDA enforcement actions
                                          (recalls) for a drug.

All endpoints are backed by the AdverseEventMonitor class which queries the
OpenFDA Drug Adverse Event, NDC Directory, and Enforcement APIs with built-in
rate-limit handling, retries, and graceful degradation on API failures.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Response models                                                            #
# --------------------------------------------------------------------------- #

class ReactionEntry(BaseModel):
    """A single adverse reaction term with its report count."""
    term: str
    count: int


class AdverseEventAnalysis(BaseModel):
    """Result of analysing adverse-event signals for a drug."""
    drug_name: str
    total_reports: int = Field(..., description="All-time adverse event reports")
    recent_reports_30d: int = Field(..., description="Reports in the last 30 days")
    quality_complaints: int = Field(..., description="Quality-related complaints in window")
    therapeutic_failures: int = Field(..., description="Therapeutic failure reports in window")
    counterfeit_risk_score: float = Field(..., ge=0.0, le=1.0, description="Composite counterfeit risk 0-1")
    top_reactions: List[ReactionEntry] = Field(default_factory=list, description="Top 10 reactions by frequency")
    signal_alerts: List[str] = Field(default_factory=list, description="Human-readable signal alerts")
    processing_time_ms: float = 0.0


class ActiveIngredient(BaseModel):
    """Active ingredient entry from the NDC directory."""
    name: str
    strength: str


class PackagingEntry(BaseModel):
    """Packaging entry from the NDC directory."""
    description: str
    ndc: str


class DrugIdentity(BaseModel):
    """Authoritative drug identity from the FDA NDC directory."""
    brand_name: str
    generic_name: str
    manufacturer: str
    active_ingredients: List[ActiveIngredient] = Field(default_factory=list)
    dosage_form: str
    route: str
    packaging: List[PackagingEntry] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class RecallEntry(BaseModel):
    """A single FDA enforcement action (recall) for a drug."""
    recall_number: str
    reason: str
    status: str
    date: str
    classification: str


class DrugRecallsResponse(BaseModel):
    """Collection of recall entries for a drug."""
    drug_name: str
    recalls: List[RecallEntry]
    total_recalls: int
    processing_time_ms: float = 0.0


# --------------------------------------------------------------------------- #
#  Routes                                                                     #
# --------------------------------------------------------------------------- #

@router.get("/adverse-events/{drug_name}", response_model=AdverseEventAnalysis)
async def get_adverse_events(
    request: Request,
    drug_name: str = Path(..., description="Drug name as it appears in FAERS (case-insensitive)"),
    days_back: int = Query(90, ge=1, le=3650, description="Number of days to look back for recent events"),
):
    """Analyse adverse-event signals for a drug from the OpenFDA FAERS API.

    Pulls adverse-event reports for the specified drug within the given time
    window, counts quality- and efficacy-related reactions that are known
    counterfeit indicators, and computes a composite ``counterfeit_risk_score``
    in [0, 1].

    A higher score indicates stronger signals that the drug may be subject to
    counterfeiting or quality issues:
      - **0.0 - 0.2**: Minimal risk
      - **0.2 - 0.5**: Moderate -- monitor closely
      - **0.5 - 0.8**: High -- recommend additional verification
      - **0.8 - 1.0**: Critical -- potential active counterfeit threat

    Signal alerts are generated for:
      - Explicit counterfeit reports
      - Reporting rate spikes vs. historical average
      - Elevated quality complaint counts
      - Elevated therapeutic failure counts
    """
    start_time = time.perf_counter()

    adverse_monitor = request.app.state.adverse_monitor
    if adverse_monitor is None:
        raise HTTPException(
            status_code=503,
            detail="AdverseEventMonitor is not initialised.",
        )

    try:
        result = await adverse_monitor.analyze_drug(drug_name, days_back=days_back)
    except Exception as exc:
        logger.error(
            "AdverseEventMonitor.analyze_drug('%s', days_back=%d) failed: %s",
            drug_name,
            days_back,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=502,
            detail=f"OpenFDA API query failed for '{drug_name}': {exc}",
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Map the raw dict to the Pydantic model.
    top_reactions = [
        ReactionEntry(term=r.get("term", "UNKNOWN"), count=r.get("count", 0))
        for r in result.get("top_reactions", [])
    ]

    return AdverseEventAnalysis(
        drug_name=result.get("drug_name", drug_name),
        total_reports=result.get("total_reports", 0),
        recent_reports_30d=result.get("recent_reports_30d", 0),
        quality_complaints=result.get("quality_complaints", 0),
        therapeutic_failures=result.get("therapeutic_failures", 0),
        counterfeit_risk_score=result.get("counterfeit_risk_score", 0.0),
        top_reactions=top_reactions,
        signal_alerts=result.get("signal_alerts", []),
        processing_time_ms=round(elapsed_ms, 2),
    )


@router.get("/drug-identity/{drug_name}", response_model=DrugIdentity)
async def get_drug_identity(
    request: Request,
    drug_name: str = Path(..., description="Brand or generic drug name to look up"),
):
    """Retrieve the authoritative NDC directory entry for a drug.

    Returns brand name, generic name, manufacturer, active ingredients,
    dosage form, route of administration, and packaging information from
    the FDA National Drug Code (NDC) directory.

    This information can be used to verify scanned product metadata against
    the ground-truth label, detecting relabelling or substitution fraud.
    """
    start_time = time.perf_counter()

    adverse_monitor = request.app.state.adverse_monitor
    if adverse_monitor is None:
        raise HTTPException(
            status_code=503,
            detail="AdverseEventMonitor is not initialised.",
        )

    try:
        result = await adverse_monitor.get_drug_identity(drug_name)
    except Exception as exc:
        logger.error(
            "AdverseEventMonitor.get_drug_identity('%s') failed: %s",
            drug_name,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=502,
            detail=f"OpenFDA NDC API query failed for '{drug_name}': {exc}",
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    active_ingredients = [
        ActiveIngredient(name=ing.get("name", "N/A"), strength=ing.get("strength", "N/A"))
        for ing in result.get("active_ingredients", [])
    ]

    packaging = [
        PackagingEntry(description=pkg.get("description", "N/A"), ndc=pkg.get("ndc", "N/A"))
        for pkg in result.get("packaging", [])
    ]

    return DrugIdentity(
        brand_name=result.get("brand_name", "N/A"),
        generic_name=result.get("generic_name", "N/A"),
        manufacturer=result.get("manufacturer", "N/A"),
        active_ingredients=active_ingredients,
        dosage_form=result.get("dosage_form", "N/A"),
        route=result.get("route", "N/A"),
        packaging=packaging,
        processing_time_ms=round(elapsed_ms, 2),
    )


@router.get("/drug-recalls/{drug_name}", response_model=DrugRecallsResponse)
async def get_drug_recalls(
    request: Request,
    drug_name: str = Path(..., description="Brand name of the drug to check for recalls"),
):
    """Check active FDA enforcement actions (recalls) for a drug.

    Returns a list of recall entries with recall number, reason, current
    status, date, and FDA classification:
      - **Class I**: Dangerous or defective products that could cause
        serious health problems or death.
      - **Class II**: Products that might cause temporary health problems
        or slight threat of serious nature.
      - **Class III**: Products unlikely to cause health problems but that
        violate FDA manufacturing or labelling laws.

    An empty recall list indicates no active enforcement actions were found.
    """
    start_time = time.perf_counter()

    adverse_monitor = request.app.state.adverse_monitor
    if adverse_monitor is None:
        raise HTTPException(
            status_code=503,
            detail="AdverseEventMonitor is not initialised.",
        )

    try:
        recalls = await adverse_monitor.check_recalls(drug_name)
    except Exception as exc:
        logger.error(
            "AdverseEventMonitor.check_recalls('%s') failed: %s",
            drug_name,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=502,
            detail=f"OpenFDA Enforcement API query failed for '{drug_name}': {exc}",
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    recall_entries = [
        RecallEntry(
            recall_number=r.get("recall_number", "N/A"),
            reason=r.get("reason", "N/A"),
            status=r.get("status", "N/A"),
            date=r.get("date", "N/A"),
            classification=r.get("classification", "N/A"),
        )
        for r in recalls
    ]

    return DrugRecallsResponse(
        drug_name=drug_name,
        recalls=recall_entries,
        total_recalls=len(recall_entries),
        processing_time_ms=round(elapsed_ms, 2),
    )
