"""
Adverse-event monitor for MediChain counterfeit-drug detection.

Queries the OpenFDA Drug Adverse Events, Drug NDC Directory, and Drug
Enforcement (recall) APIs to surface signals that may indicate counterfeit
or substandard pharmaceuticals circulating in the supply chain.

Key capabilities
----------------
* **analyze_drug** -- Pulls recent adverse-event reports for a given drug,
  counts quality- and efficacy-related reactions that are known counterfeit
  indicators, and computes a composite ``counterfeit_risk_score`` in [0, 1].
* **check_recalls** -- Returns active and recent FDA enforcement actions
  (recalls) for a drug.
* **get_drug_identity** -- Retrieves the authoritative NDC directory entry
  so downstream consumers can compare scanned product metadata against the
  ground-truth label.

All network I/O is asynchronous (``httpx.AsyncClient``) with a per-request
timeout of 10 seconds and graceful handling of 429 (rate-limit) and 404
(no results) responses.
"""

from __future__ import annotations

import asyncio
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

# --------------------------------------------------------------------------- #
#  Constants                                                                   #
# --------------------------------------------------------------------------- #

_DEFAULT_TIMEOUT = 10.0  # seconds per HTTP request
_RATE_LIMIT_BACKOFF = 2.0  # seconds to wait on 429 before retry
_MAX_RETRIES = 3  # retries on transient failures


class AdverseEventMonitor:
    """OpenFDA-backed adverse-event and recall monitor.

    Attributes
    ----------
    BASE_URL : str
        Endpoint for the FDA Adverse Event Reporting System (FAERS).
    NDC_URL : str
        Endpoint for the National Drug Code Directory.
    ENFORCEMENT_URL : str
        Endpoint for FDA enforcement / recall data.
    COUNTERFEIT_SIGNAL_REACTIONS : list[str]
        MedDRA preferred terms whose elevated frequency may indicate a
        counterfeit product has entered the supply chain.
    """

    BASE_URL: str = "https://api.fda.gov/drug/event.json"
    NDC_URL: str = "https://api.fda.gov/drug/ndc.json"
    ENFORCEMENT_URL: str = "https://api.fda.gov/drug/enforcement.json"

    COUNTERFEIT_SIGNAL_REACTIONS: List[str] = [
        "PRODUCT QUALITY ISSUE",
        "DRUG INEFFECTIVE",
        "THERAPEUTIC RESPONSE UNEXPECTED",
        "PRODUCT CONTAMINATION",
        "PRODUCT ADULTERATION",
        "SUSPECTED COUNTERFEIT PRODUCT",
        "PRODUCT PACKAGING QUANTITY ERROR",
    ]

    # Weights used when computing the composite counterfeit risk score.
    # Each weight is applied to a normalised sub-score in [0, 1].
    _WEIGHT_QUALITY: float = 0.30
    _WEIGHT_THERAPEUTIC_FAILURE: float = 0.25
    _WEIGHT_SPIKE: float = 0.25
    _WEIGHT_COUNTERFEIT_EXPLICIT: float = 0.20

    # ----------------------------------------------------------------------- #
    #  Public API                                                              #
    # ----------------------------------------------------------------------- #

    async def analyze_drug(
        self,
        drug_name: str,
        days_back: int = 90,
    ) -> Dict[str, Any]:
        """Analyse adverse-event signals for a drug over a recent window.

        Parameters
        ----------
        drug_name:
            The medicinal product name as it appears in FAERS (case-insensitive).
        days_back:
            Number of days to consider for the "recent" window.  Defaults to
            90.

        Returns
        -------
        dict
            Keys: ``drug_name``, ``total_reports``, ``recent_reports_30d``,
            ``quality_complaints``, ``therapeutic_failures``,
            ``counterfeit_risk_score`` (float in [0, 1]),
            ``top_reactions`` (list of ``{term, count}``),
            ``signal_alerts`` (list of human-readable alert strings).
        """

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        start_30d = end_date - timedelta(days=30)

        date_fmt = "%Y%m%d"
        start_str = start_date.strftime(date_fmt)
        end_str = end_date.strftime(date_fmt)
        start_30d_str = start_30d.strftime(date_fmt)

        drug_search = f'patient.drug.medicinalproduct:"{drug_name}"'

        # 1. Total reports (all time) -----------------------------------------
        total_reports = await self._count_events(drug_search)

        # 2. Recent reports (last ``days_back`` days) --------------------------
        recent_search = (
            f"{drug_search}+AND+receivedate:[{start_str}+TO+{end_str}]"
        )
        recent_reports = await self._count_events(recent_search)

        # 3. Reports in the last 30 days (for spike detection) -----------------
        recent_30d_search = (
            f"{drug_search}+AND+receivedate:[{start_30d_str}+TO+{end_str}]"
        )
        recent_reports_30d = await self._count_events(recent_30d_search)

        # 4. Fetch top reactions for the recent window -------------------------
        top_reactions = await self._top_reactions(recent_search, limit=20)

        # 5. Count counterfeit-signal reactions --------------------------------
        quality_complaints = 0
        therapeutic_failures = 0
        explicit_counterfeit = 0
        for rxn in top_reactions:
            term_upper = rxn["term"].upper()
            if term_upper in (
                "PRODUCT QUALITY ISSUE",
                "PRODUCT CONTAMINATION",
                "PRODUCT ADULTERATION",
                "PRODUCT PACKAGING QUANTITY ERROR",
            ):
                quality_complaints += rxn["count"]
            if term_upper in (
                "DRUG INEFFECTIVE",
                "THERAPEUTIC RESPONSE UNEXPECTED",
            ):
                therapeutic_failures += rxn["count"]
            if term_upper == "SUSPECTED COUNTERFEIT PRODUCT":
                explicit_counterfeit += rxn["count"]

        # 6. Compute the composite risk score ----------------------------------
        counterfeit_risk_score = self._compute_risk_score(
            total_reports=total_reports,
            recent_reports=recent_reports,
            recent_reports_30d=recent_reports_30d,
            quality_complaints=quality_complaints,
            therapeutic_failures=therapeutic_failures,
            explicit_counterfeit=explicit_counterfeit,
            days_back=days_back,
        )

        # 7. Build human-readable signal alerts --------------------------------
        signal_alerts: List[str] = []

        if explicit_counterfeit > 0:
            signal_alerts.append(
                f"CRITICAL: {explicit_counterfeit} explicit counterfeit report(s) "
                f"in the last {days_back} days."
            )

        if recent_reports > 0 and total_reports > 0:
            # Expected proportion for the window vs all time (rough proxy --
            # assumes uniform rate historically).
            expected_fraction = days_back / 365.0
            actual_fraction = recent_reports / max(total_reports, 1)
            if actual_fraction > expected_fraction * 2:
                signal_alerts.append(
                    f"SPIKE: Recent {days_back}-day report rate is "
                    f"{actual_fraction / max(expected_fraction, 1e-9):.1f}x "
                    f"the historical average."
                )

        if quality_complaints > 0:
            signal_alerts.append(
                f"WARNING: {quality_complaints} product-quality complaint(s) "
                f"in the last {days_back} days."
            )

        if therapeutic_failures > 0:
            signal_alerts.append(
                f"WARNING: {therapeutic_failures} therapeutic-failure report(s) "
                f"in the last {days_back} days."
            )

        return {
            "drug_name": drug_name,
            "total_reports": total_reports,
            "recent_reports_30d": recent_reports_30d,
            "quality_complaints": quality_complaints,
            "therapeutic_failures": therapeutic_failures,
            "counterfeit_risk_score": round(counterfeit_risk_score, 4),
            "top_reactions": top_reactions[:10],
            "signal_alerts": signal_alerts,
        }

    async def check_recalls(self, drug_name: str) -> List[Dict[str, Any]]:
        """Retrieve FDA enforcement actions (recalls) for a drug.

        Parameters
        ----------
        drug_name:
            The product name to search for in recall records.

        Returns
        -------
        list[dict]
            Each dict contains: ``recall_number``, ``reason``, ``status``,
            ``date``, ``classification``.  Empty list when no recalls exist
            or the API returns a non-200 status.
        """

        search = f'openfda.brand_name:"{drug_name}"'
        params = {
            "search": search,
            "limit": 10,
        }

        data = await self._query_openfda(self.ENFORCEMENT_URL, params)
        if data is None or "results" not in data:
            return []

        recalls: List[Dict[str, Any]] = []
        for result in data["results"]:
            recalls.append(
                {
                    "recall_number": result.get("recall_number", "N/A"),
                    "reason": result.get("reason_for_recall", "N/A"),
                    "status": result.get("status", "N/A"),
                    "date": result.get("report_date", "N/A"),
                    "classification": result.get("classification", "N/A"),
                }
            )
        return recalls

    async def get_drug_identity(self, drug_name: str) -> Dict[str, Any]:
        """Look up the authoritative NDC directory entry for a drug.

        Parameters
        ----------
        drug_name:
            Brand or generic name to search.

        Returns
        -------
        dict
            Keys: ``brand_name``, ``generic_name``, ``manufacturer``,
            ``active_ingredients``, ``dosage_form``, ``route``,
            ``packaging``.  Values default to ``"N/A"`` or empty lists
            when not available.
        """

        search = f'brand_name:"{drug_name}"'
        params = {
            "search": search,
            "limit": 1,
        }

        data = await self._query_openfda(self.NDC_URL, params)

        empty_result: Dict[str, Any] = {
            "brand_name": "N/A",
            "generic_name": "N/A",
            "manufacturer": "N/A",
            "active_ingredients": [],
            "dosage_form": "N/A",
            "route": "N/A",
            "packaging": [],
        }

        if data is None or "results" not in data or len(data["results"]) == 0:
            return empty_result

        result = data["results"][0]

        # Active ingredients -- list of {name, strength} dicts.
        raw_ingredients = result.get("active_ingredients", [])
        active_ingredients = [
            {
                "name": ing.get("name", "N/A"),
                "strength": ing.get("strength", "N/A"),
            }
            for ing in raw_ingredients
        ]

        # Packaging descriptions.
        raw_packaging = result.get("packaging", [])
        packaging = [
            {
                "description": pkg.get("description", "N/A"),
                "ndc": pkg.get("package_ndc", "N/A"),
            }
            for pkg in raw_packaging
        ]

        # Route may be a list.
        route_raw = result.get("route", [])
        route = ", ".join(route_raw) if isinstance(route_raw, list) else str(route_raw)

        # Dosage form may also be a list.
        dosage_raw = result.get("dosage_form", "N/A")
        dosage_form = (
            ", ".join(dosage_raw) if isinstance(dosage_raw, list) else str(dosage_raw)
        )

        # Labeler (manufacturer).
        manufacturer = result.get("labeler_name", "N/A")

        return {
            "brand_name": result.get("brand_name", "N/A"),
            "generic_name": result.get("generic_name", "N/A"),
            "manufacturer": manufacturer,
            "active_ingredients": active_ingredients,
            "dosage_form": dosage_form,
            "route": route,
            "packaging": packaging,
        }

    # ----------------------------------------------------------------------- #
    #  Private helpers                                                         #
    # ----------------------------------------------------------------------- #

    async def _query_openfda(
        self,
        url: str,
        params: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Execute a GET request against an OpenFDA endpoint.

        Handles:
        * **429 Too Many Requests** -- backs off for ``_RATE_LIMIT_BACKOFF``
          seconds and retries up to ``_MAX_RETRIES`` times.
        * **404 Not Found** -- returns ``None`` (no matching records).
        * **Other HTTP errors** -- returns ``None`` after logging.
        * **Network / timeout errors** -- returns ``None``.

        Parameters
        ----------
        url:
            The full API endpoint URL (without query string).
        params:
            Query-string parameters forwarded to ``httpx``.

        Returns
        -------
        dict or None
            Parsed JSON body on success, ``None`` on failure.
        """

        retries = 0
        while retries <= _MAX_RETRIES:
            try:
                async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                    response = await client.get(url, params=params)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 404:
                    # No results -- perfectly normal for narrow searches.
                    return None

                if response.status_code == 429:
                    retries += 1
                    if retries <= _MAX_RETRIES:
                        await asyncio.sleep(
                            _RATE_LIMIT_BACKOFF * retries
                        )
                        continue
                    # Exhausted retries.
                    return None

                # Any other unexpected status.
                return None

            except httpx.TimeoutException:
                retries += 1
                if retries <= _MAX_RETRIES:
                    await asyncio.sleep(_RATE_LIMIT_BACKOFF)
                    continue
                return None

            except httpx.HTTPError:
                # Covers connection errors, redirect loops, etc.
                return None

        return None

    async def _count_events(self, search: str) -> int:
        """Return the total number of adverse-event records matching *search*.

        The trick is to request ``limit=1`` and read the ``meta.results.total``
        field, avoiding transfer of full result bodies.
        """

        params = {"search": search, "limit": 1}
        data = await self._query_openfda(self.BASE_URL, params)
        if data is None:
            return 0
        try:
            return int(data["meta"]["results"]["total"])
        except (KeyError, TypeError, ValueError):
            return 0

    async def _top_reactions(
        self,
        search: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return the most frequently reported reactions for a search query.

        Uses the OpenFDA ``count`` parameter on the
        ``patient.reaction.reactionmeddrapt.exact`` field.
        """

        params = {
            "search": search,
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": limit,
        }
        data = await self._query_openfda(self.BASE_URL, params)
        if data is None or "results" not in data:
            return []

        return [
            {"term": entry.get("term", "UNKNOWN"), "count": entry.get("count", 0)}
            for entry in data["results"]
        ]

    # ----------------------------------------------------------------------- #
    #  Risk-score computation                                                  #
    # ----------------------------------------------------------------------- #

    def _compute_risk_score(
        self,
        total_reports: int,
        recent_reports: int,
        recent_reports_30d: int,
        quality_complaints: int,
        therapeutic_failures: int,
        explicit_counterfeit: int,
        days_back: int,
    ) -> float:
        """Compute a composite counterfeit-risk score in [0, 1].

        The score is a weighted sum of four normalised sub-scores:

        1. **Quality complaints ratio** -- fraction of recent reports that are
           quality-related.
        2. **Therapeutic-failure ratio** -- fraction of recent reports that
           indicate the drug did not work as expected.
        3. **Reporting spike** -- how much the recent reporting rate exceeds
           the historical average.
        4. **Explicit counterfeit flag** -- hard signal (any explicit
           counterfeit report drives this sub-score to 1.0).

        All sub-scores are clamped to [0, 1] before weighting.
        """

        # Guard: if there are no reports at all, risk is unknown (return 0).
        if recent_reports == 0 and total_reports == 0:
            return 0.0

        # Sub-score 1: quality-complaint ratio.
        if recent_reports > 0:
            quality_ratio = min(quality_complaints / recent_reports, 1.0)
        else:
            quality_ratio = 0.0

        # Sub-score 2: therapeutic-failure ratio.
        if recent_reports > 0:
            failure_ratio = min(therapeutic_failures / recent_reports, 1.0)
        else:
            failure_ratio = 0.0

        # Sub-score 3: reporting-rate spike.
        #   expected_fraction = days_back / 365 of total reports
        #   spike_ratio       = actual / expected  (capped at 5x -> 1.0)
        if total_reports > 0:
            expected_recent = total_reports * (days_back / 365.0)
            if expected_recent > 0:
                spike_ratio = min(recent_reports / expected_recent, 5.0) / 5.0
            else:
                spike_ratio = 0.0
        else:
            spike_ratio = 0.0

        # Sub-score 4: explicit counterfeit flag (binary-ish, but use sigmoid
        # saturation so even 1 report gives a high score).
        if explicit_counterfeit > 0:
            # Sigmoid-like: 1 - exp(-k * n), k chosen so that 1 report -> ~0.63
            counterfeit_flag = 1.0 - math.exp(-1.0 * explicit_counterfeit)
        else:
            counterfeit_flag = 0.0

        score = (
            self._WEIGHT_QUALITY * quality_ratio
            + self._WEIGHT_THERAPEUTIC_FAILURE * failure_ratio
            + self._WEIGHT_SPIKE * spike_ratio
            + self._WEIGHT_COUNTERFEIT_EXPLICIT * counterfeit_flag
        )

        return max(0.0, min(score, 1.0))
