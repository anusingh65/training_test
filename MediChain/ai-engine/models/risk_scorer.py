"""
Composite Risk Scoring Engine for MediChain.

Combines AI signals into a single 0-100 Trust Score per medicine.

Signal weights (3-signal architecture):
  1. Supply chain anomaly score (50%) - from AnomalyDetector.detect()
  2. External risk factors (30%) - drug shortage, recalls, actor reputation, adverse events
  3. Geographic risk / hotspot proximity (20%) - from HeatmapEngine.get_zone_risk_level()

Trust score thresholds:
  80-100 -> "low" risk (FlagSeverity.Low, no action)
  50-79  -> "medium" risk (FlagSeverity.Medium, warning)
  20-49  -> "high" risk (FlagSeverity.High, auto-flag on blockchain)
  0-19   -> "critical" risk (FlagSeverity.Critical, auto-flag + alert)

Output format:
{
  "medicine_id": 12345,
  "trust_score": 73,
  "risk_level": "medium",
  "flag_severity": 1,
  "signals": {
    "supply_chain": {"score": 0.15, "status": "warning", "reasons": [...]},
    "geographic_risk": {"score": 0.7, "status": "high", "nearest_hotspot": "..."},
    "external_factors": {"score": 0.2, "status": "normal"}
  },
  "recommendation": "Flag for manual inspection -- ...",
  "auto_flag": true,
  "timestamp": "2024-01-15T10:30:00Z"
}

Smart contract integration:
  trust_score < 50 -> auto-call core.flagDrug(medicineId, FlagSeverity.High)
  trust_score < 20 -> auto-call core.flagDrug(medicineId, FlagSeverity.Critical)
  trust_score 50-70 -> warning only
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FlagSeverity(IntEnum):
    """Maps to the on-chain uint8 severity parameter for core.flagDrug()."""
    Low = 0
    Medium = 1
    High = 2
    Critical = 3


class RiskScorer:
    """
    Composite risk scoring engine that fuses signals from every MediChain AI
    module into a single 0-100 Trust Score per medicine.

    Any dependency can be ``None``; the engine gracefully degrades by using a
    neutral 0.5 risk score for any missing signal, ensuring partial scoring is
    always possible.
    """

    WEIGHTS: Dict[str, float] = {
        "supply_chain": 0.50,
        "external_factors": 0.30,
        "geographic_risk": 0.20,
    }

    TRUST_THRESHOLDS: Dict[str, tuple] = {
        "low": (80, 100),
        "medium": (50, 79),
        "high": (20, 49),
        "critical": (0, 19),
    }

    # Mapping from HeatmapEngine risk-level strings to numeric scores
    _GEO_RISK_LEVEL_MAP: Dict[str, float] = {
        "low": 0.10,
        "moderate": 0.30,
        "elevated": 0.50,
        "high": 0.70,
        "critical": 0.90,
    }

    # Default neutral risk when a signal source is unavailable
    _NEUTRAL_RISK: float = 0.5

    def __init__(
        self,
        anomaly_detector=None,
        heatmap_engine=None,
        adverse_monitor=None,
    ):
        """
        Parameters
        ----------
        anomaly_detector : AnomalyDetector or None
            Supply-chain anomaly detection model.  Expected interface:
            ``detect(transaction_data) -> {"anomaly_score": float, "is_anomaly": bool,
            "reasons": list, ...}``
        heatmap_engine : HeatmapEngine or None
            Geographic risk heatmap.  Expected interface:
            ``get_zone_risk_level(lat, lng) -> {"risk_level": str,
            "nearest_hotspot": str or None, "distance_km": float, ...}``
        adverse_monitor : AdverseEventMonitor or None
            FDA adverse event monitor (folded into external factors).
            Expected interface:
            ``analyze_drug(drug_name) -> {"counterfeit_risk_score": float,
            "risk_level": str, "alerts": list, ...}``
        """
        self.anomaly_detector = anomaly_detector
        self.heatmap_engine = heatmap_engine
        self.adverse_monitor = adverse_monitor

    # ------------------------------------------------------------------ #
    #  Main entry point                                                    #
    # ------------------------------------------------------------------ #

    async def score_medicine(
        self,
        medicine_id: int,
        transaction_data: Optional[Dict[str, Any]] = None,
        drug_name: Optional[str] = None,
        location: Optional[Dict[str, float]] = None,
        actor_reputation: Optional[float] = None,
        shortage_flag: bool = False,
        recall_flag: bool = False,
    ) -> Dict[str, Any]:
        """
        Compute a composite trust score for a medicine by gathering and
        fusing signals from the three AI modules.

        Parameters
        ----------
        medicine_id : int
            On-chain medicine identifier.
        transaction_data : dict or None
            Supply-chain transaction records for anomaly detection.
        drug_name : str or None
            Drug name for adverse-event lookup (folded into external factors).
        location : dict or None
            ``{"lat": float, "lng": float}`` for geographic risk assessment.
        actor_reputation : float or None
            Reputation score of the current supply-chain actor (0.0 = worst,
            1.0 = perfect).  ``None`` means unknown.
        shortage_flag : bool
            Whether the drug is currently on a shortage list.
        recall_flag : bool
            Whether the drug is currently under a recall notice.

        Returns
        -------
        dict
            Full risk assessment result (see module docstring for schema).
        """
        # Gather all three signal groups concurrently
        supply_signal, geo_signal, external_signal = (
            await asyncio.gather(
                self._gather_supply_chain_signal(transaction_data),
                self._gather_geographic_signal(location),
                self._gather_external_signal(
                    actor_reputation=actor_reputation,
                    shortage_flag=shortage_flag,
                    recall_flag=recall_flag,
                    drug_name=drug_name,
                ),
            )
        )

        # Build signal scores dict (each value is 0-1 where 1 = highest risk)
        signal_scores: Dict[str, float] = {
            "supply_chain": supply_signal["score"],
            "geographic_risk": geo_signal["score"],
            "external_factors": external_signal["score"],
        }

        # Compute composite trust score
        trust_score = self._compute_trust_score(signal_scores)
        risk_level = self._map_to_risk_level(trust_score)
        flag_severity = self._map_to_severity(trust_score)

        # Enrich signal dicts with status labels
        supply_signal["status"] = self._determine_signal_status(supply_signal["score"])
        geo_signal["status"] = self._determine_signal_status(geo_signal["score"])
        external_signal["status"] = self._determine_signal_status(external_signal["score"])

        # Build the signals sub-dict
        signals: Dict[str, Dict[str, Any]] = {
            "supply_chain": supply_signal,
            "geographic_risk": geo_signal,
            "external_factors": external_signal,
        }

        recommendation = self._generate_recommendation(signals, trust_score, risk_level)
        auto_flag = trust_score < 50

        return {
            "medicine_id": medicine_id,
            "trust_score": trust_score,
            "risk_level": risk_level,
            "flag_severity": int(flag_severity),
            "signals": signals,
            "recommendation": recommendation,
            "auto_flag": auto_flag,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  Signal gathering (one async method per signal source)               #
    # ------------------------------------------------------------------ #

    async def _gather_supply_chain_signal(self, transaction_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Query AnomalyDetector for supply-chain anomalies.

        The detector returns ``anomaly_score`` in [0, 1] where higher means
        more anomalous.  This maps directly to our risk score.
        """
        if transaction_data is None or self.anomaly_detector is None:
            return {"score": self._NEUTRAL_RISK, "source": "supply_chain", "available": False, "reasons": []}

        try:
            # Support both sync and async detect() interfaces
            detect_result = self.anomaly_detector.detect(transaction_data)
            if asyncio.iscoroutine(detect_result):
                detect_result = await detect_result

            anomaly_score = detect_result.get("anomaly_score", 0.5)
            is_anomaly = detect_result.get("is_anomaly", False)
            reasons = detect_result.get("anomaly_reasons", [])

            # Clamp to [0, 1]
            risk_score = max(0.0, min(1.0, float(anomaly_score)))

            return {
                "score": round(risk_score, 6),
                "source": "supply_chain",
                "available": True,
                "is_anomaly": is_anomaly,
                "reasons": reasons,
            }
        except Exception as exc:
            logger.error("Supply chain anomaly detection failed: %s", exc, exc_info=True)
            return {"score": self._NEUTRAL_RISK, "source": "supply_chain", "available": False, "reasons": [], "error": str(exc)}

    async def _gather_geographic_signal(self, location: Optional[Dict[str, float]]) -> Dict[str, Any]:
        """
        Query HeatmapEngine for geographic / hotspot proximity risk.

        The engine returns a ``risk_level`` string that we map to a numeric
        score via ``_GEO_RISK_LEVEL_MAP``.
        """
        if location is None or self.heatmap_engine is None:
            return {"score": self._NEUTRAL_RISK, "source": "geographic_risk", "available": False, "nearest_hotspot": None}

        try:
            lat = location.get("lat", 0.0)
            lng = location.get("lng", 0.0)

            # Support both sync and async get_zone_risk_level() interfaces
            zone_result = self.heatmap_engine.get_zone_risk_level(lat, lng)
            if asyncio.iscoroutine(zone_result):
                zone_result = await zone_result

            risk_level_str = zone_result.get("risk_level", "moderate")
            nearest_hotspot = zone_result.get("nearest_hotspot", None)
            distance_km = zone_result.get("distance_km", None)

            # Map textual risk level to numeric score
            risk_score = self._GEO_RISK_LEVEL_MAP.get(risk_level_str.lower(), self._NEUTRAL_RISK)

            result: Dict[str, Any] = {
                "score": round(risk_score, 6),
                "source": "geographic_risk",
                "available": True,
                "risk_level_detail": risk_level_str,
                "nearest_hotspot": nearest_hotspot,
            }
            if distance_km is not None:
                result["distance_km"] = distance_km
            return result
        except Exception as exc:
            logger.error("Geographic risk assessment failed: %s", exc, exc_info=True)
            return {"score": self._NEUTRAL_RISK, "source": "geographic_risk", "available": False, "nearest_hotspot": None, "error": str(exc)}

    async def _gather_external_signal(
        self,
        actor_reputation: Optional[float] = None,
        shortage_flag: bool = False,
        recall_flag: bool = False,
        drug_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute external risk factors from drug shortage status, recall
        notices, actor reputation, and adverse event signals (OpenFDA).

        Sub-factor weights within external factors:
            - Actor reputation:    30%  (unknown -> 0.5 risk)
            - Adverse events:      30%  (from OpenFDA if available)
            - Drug shortage:       20%  (bool -> 0.0 or 0.7)
            - Drug recall:         20%  (bool -> 0.0 or 1.0)
        """
        sub_scores: Dict[str, float] = {}
        details: List[str] = []
        alerts: List[Any] = []

        # Actor reputation: 0.0 (worst) to 1.0 (perfect).  Risk = 1 - reputation.
        if actor_reputation is not None:
            clamped_reputation = max(0.0, min(1.0, float(actor_reputation)))
            sub_scores["reputation"] = 1.0 - clamped_reputation
            if clamped_reputation < 0.5:
                details.append(f"low actor reputation ({clamped_reputation:.2f})")
        else:
            sub_scores["reputation"] = self._NEUTRAL_RISK  # unknown

        # Adverse events (OpenFDA) -- folded into external signal
        if drug_name is not None and self.adverse_monitor is not None:
            try:
                analysis = self.adverse_monitor.analyze_drug(drug_name)
                if asyncio.iscoroutine(analysis):
                    analysis = await analysis
                ae_risk = max(0.0, min(1.0, float(analysis.get("counterfeit_risk_score", 0.5))))
                sub_scores["adverse_events"] = ae_risk
                alerts = analysis.get("alerts", [])
                if ae_risk > 0.5:
                    details.append(f"elevated adverse event signal ({ae_risk:.2f})")
            except Exception as exc:
                logger.error("Adverse event lookup failed for '%s': %s", drug_name, exc, exc_info=True)
                sub_scores["adverse_events"] = self._NEUTRAL_RISK
        else:
            sub_scores["adverse_events"] = self._NEUTRAL_RISK

        # Shortage: binary flag contributing moderate risk
        if shortage_flag:
            sub_scores["shortage"] = 0.7
            details.append("drug currently on shortage list")
        else:
            sub_scores["shortage"] = 0.0

        # Recall: binary flag contributing maximum risk
        if recall_flag:
            sub_scores["recall"] = 1.0
            details.append("drug currently under recall")
        else:
            sub_scores["recall"] = 0.0

        # Weighted combination of sub-factors
        composite = (
            sub_scores["reputation"] * 0.30
            + sub_scores["adverse_events"] * 0.30
            + sub_scores["shortage"] * 0.20
            + sub_scores["recall"] * 0.20
        )
        composite = max(0.0, min(1.0, composite))

        result: Dict[str, Any] = {
            "score": round(composite, 6),
            "source": "external_factors",
            "available": True,
            "sub_scores": sub_scores,
            "details": details,
        }
        if alerts:
            result["alerts"] = alerts
        return result

    # ------------------------------------------------------------------ #
    #  Score computation                                                   #
    # ------------------------------------------------------------------ #

    def _compute_trust_score(self, signal_scores: Dict[str, float]) -> int:
        """
        Compute a weighted trust score from individual signal risk scores.

        Each signal score is in [0, 1] where 1 = highest risk.  The weighted
        average gives the overall risk, and trust = 100 * (1 - risk), clamped
        to the integer range [0, 100].

        Parameters
        ----------
        signal_scores : dict
            Mapping of signal name to risk score (0.0 - 1.0).

        Returns
        -------
        int
            Trust score in [0, 100].
        """
        weighted_risk = 0.0
        total_weight = 0.0

        for signal_name, weight in self.WEIGHTS.items():
            risk = signal_scores.get(signal_name, self._NEUTRAL_RISK)
            # Clamp individual signal to [0, 1]
            risk = max(0.0, min(1.0, float(risk)))
            weighted_risk += risk * weight
            total_weight += weight

        # Normalise in case weights don't sum to exactly 1.0
        if total_weight > 0:
            weighted_risk /= total_weight

        trust = int(round((1.0 - weighted_risk) * 100))
        return max(0, min(100, trust))

    # ------------------------------------------------------------------ #
    #  Mapping helpers                                                     #
    # ------------------------------------------------------------------ #

    def _map_to_risk_level(self, trust_score: int) -> str:
        """
        Map a trust score to a human-readable risk level string.

        Parameters
        ----------
        trust_score : int
            Trust score in [0, 100].

        Returns
        -------
        str
            One of ``"low"``, ``"medium"``, ``"high"``, ``"critical"``.
        """
        for level, (low_bound, high_bound) in self.TRUST_THRESHOLDS.items():
            if low_bound <= trust_score <= high_bound:
                return level
        # Fallback: if trust_score is somehow out of range, pick the closest
        if trust_score > 100:
            return "low"
        return "critical"

    def _map_to_severity(self, trust_score: int) -> FlagSeverity:
        """
        Map a trust score to a ``FlagSeverity`` enum value suitable for the
        on-chain ``flagDrug(medicineId, severity)`` call.

        Parameters
        ----------
        trust_score : int
            Trust score in [0, 100].

        Returns
        -------
        FlagSeverity
            ``Low`` (0), ``Medium`` (1), ``High`` (2), or ``Critical`` (3).
        """
        if trust_score >= 80:
            return FlagSeverity.Low
        elif trust_score >= 50:
            return FlagSeverity.Medium
        elif trust_score >= 20:
            return FlagSeverity.High
        else:
            return FlagSeverity.Critical

    # ------------------------------------------------------------------ #
    #  Signal status                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _determine_signal_status(score: float) -> str:
        """
        Convert a numeric risk score to a human-readable status label.

        Thresholds:
            score < 0.2  -> "pass"
            score < 0.4  -> "normal"
            score < 0.6  -> "warning"
            score < 0.8  -> "elevated"
            score >= 0.8 -> "critical"

        Parameters
        ----------
        score : float
            Risk score in [0, 1].

        Returns
        -------
        str
            Status label.
        """
        if score < 0.2:
            return "pass"
        elif score < 0.4:
            return "normal"
        elif score < 0.6:
            return "warning"
        elif score < 0.8:
            return "elevated"
        else:
            return "critical"

    # ------------------------------------------------------------------ #
    #  Recommendation generation                                           #
    # ------------------------------------------------------------------ #

    def _generate_recommendation(
        self,
        signals: Dict[str, Dict[str, Any]],
        trust_score: int,
        risk_level: str,
    ) -> str:
        """
        Generate a human-readable recommendation string based on which signals
        are elevated and the overall trust score.

        The recommendation captures the most important findings so that a
        supply-chain operator can immediately understand the risk.

        Parameters
        ----------
        signals : dict
            Full signals dict with score and status per signal.
        trust_score : int
            Composite trust score in [0, 100].
        risk_level : str
            Overall risk level string.

        Returns
        -------
        str
            Human-readable recommendation.
        """
        # Collect the names of elevated or worse signals
        problem_signals: List[str] = []
        critical_signals: List[str] = []

        signal_display_names: Dict[str, str] = {
            "supply_chain": "supply chain anomaly",
            "geographic_risk": "geographic risk",
            "external_factors": "external risk factor",
        }

        for signal_key, signal_data in signals.items():
            status = signal_data.get("status", "normal")
            display = signal_display_names.get(signal_key, signal_key)
            if status == "critical":
                critical_signals.append(display)
            elif status in ("elevated", "warning"):
                problem_signals.append(display)

        # Build recommendation based on severity
        if risk_level == "critical":
            if critical_signals:
                issues = ", ".join(critical_signals)
                return (
                    f"CRITICAL: Multiple high-severity signals detected ({issues}) "
                    f"-- possible counterfeit. Immediate quarantine and investigation required."
                )
            elif problem_signals:
                issues = ", ".join(problem_signals)
                return (
                    f"CRITICAL: Severe risk indicators ({issues}) "
                    f"-- auto-flagged on blockchain with Critical severity. Escalate immediately."
                )
            else:
                return (
                    "CRITICAL: Trust score is extremely low across multiple dimensions "
                    "-- auto-flagged on blockchain with Critical severity. Escalate immediately."
                )

        elif risk_level == "high":
            all_issues = critical_signals + problem_signals
            if all_issues:
                issues = ", ".join(all_issues)
                return (
                    f"Flag for manual inspection -- elevated {issues} signals detected. "
                    f"Auto-flagged on blockchain. Do not distribute until verified."
                )
            else:
                return (
                    "Flag for manual inspection -- composite risk score indicates elevated risk "
                    "across multiple signals. Auto-flagged on blockchain."
                )

        elif risk_level == "medium":
            all_issues = critical_signals + problem_signals
            if all_issues:
                issues = ", ".join(all_issues)
                return (
                    f"Warning: moderate risk detected in {issues}. "
                    f"Recommend additional verification before distribution."
                )
            else:
                return (
                    "Warning: moderate overall risk. "
                    "Consider additional verification before distribution."
                )

        else:  # "low"
            return "No issues detected -- medicine appears authentic and supply chain is intact."

    # ------------------------------------------------------------------ #
    #  Batch scoring                                                       #
    # ------------------------------------------------------------------ #

    async def score_batch(
        self,
        medicines: List[Dict[str, Any]],
        concurrency: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Score multiple medicines concurrently with controlled parallelism.

        Each entry in ``medicines`` should be a dict of keyword arguments
        suitable for :meth:`score_medicine` (must include ``medicine_id``).

        Parameters
        ----------
        medicines : list of dict
            Each dict contains kwargs for ``score_medicine``.
        concurrency : int
            Maximum number of medicines scored simultaneously.

        Returns
        -------
        list of dict
            Risk assessment results in the same order as input.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: List[Optional[Dict[str, Any]]] = [None] * len(medicines)

        async def _score_one(index: int, kwargs: Dict[str, Any]) -> None:
            async with semaphore:
                try:
                    results[index] = await self.score_medicine(**kwargs)
                except Exception as exc:
                    logger.error(
                        "Batch scoring failed for medicine %s: %s",
                        kwargs.get("medicine_id", "unknown"),
                        exc,
                        exc_info=True,
                    )
                    results[index] = {
                        "medicine_id": kwargs.get("medicine_id"),
                        "trust_score": 0,
                        "risk_level": "critical",
                        "flag_severity": int(FlagSeverity.Critical),
                        "signals": {},
                        "recommendation": f"Scoring failed due to error: {exc}",
                        "auto_flag": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": str(exc),
                    }

        tasks = [_score_one(i, med) for i, med in enumerate(medicines)]
        await asyncio.gather(*tasks)
        return results  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    #  Utility: should auto-flag on chain?                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def should_auto_flag(result: Dict[str, Any]) -> bool:
        """
        Determine whether a scoring result warrants automatic on-chain flagging.

        Returns ``True`` when ``trust_score < 50`` (High or Critical severity).
        """
        return result.get("trust_score", 100) < 50

    @staticmethod
    def get_flag_args(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        If the result requires on-chain flagging, return the arguments for
        ``core.flagDrug(medicineId, severity)``.  Returns ``None`` if no
        flagging is needed.

        Returns
        -------
        dict or None
            ``{"medicine_id": int, "severity": int}`` or ``None``.
        """
        trust = result.get("trust_score", 100)
        if trust >= 50:
            return None

        medicine_id = result.get("medicine_id")
        if trust < 20:
            severity = int(FlagSeverity.Critical)
        else:
            severity = int(FlagSeverity.High)

        return {"medicine_id": medicine_id, "severity": severity}

    # ------------------------------------------------------------------ #
    #  Summary / analytics helpers                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Produce an aggregate summary across multiple scoring results.

        Useful for dashboard analytics and batch-level monitoring.

        Parameters
        ----------
        results : list of dict
            List of individual ``score_medicine`` results.

        Returns
        -------
        dict
            Summary with counts, averages, and the list of auto-flagged IDs.
        """
        if not results:
            return {
                "total": 0,
                "average_trust_score": 0.0,
                "risk_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0},
                "auto_flagged_ids": [],
                "auto_flagged_count": 0,
            }

        total = len(results)
        avg_trust = sum(r.get("trust_score", 0) for r in results) / total

        distribution: Dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        flagged_ids: List[int] = []

        for r in results:
            level = r.get("risk_level", "critical")
            distribution[level] = distribution.get(level, 0) + 1
            if r.get("auto_flag", False):
                mid = r.get("medicine_id")
                if mid is not None:
                    flagged_ids.append(mid)

        return {
            "total": total,
            "average_trust_score": round(avg_trust, 2),
            "risk_distribution": distribution,
            "auto_flagged_ids": flagged_ids,
            "auto_flagged_count": len(flagged_ids),
        }

    # ------------------------------------------------------------------ #
    #  Repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        modules = []
        if self.anomaly_detector is not None:
            modules.append("AnomalyDetector")
        if self.heatmap_engine is not None:
            modules.append("HeatmapEngine")
        if self.adverse_monitor is not None:
            modules.append("AdverseEventMonitor")
        available = ", ".join(modules) if modules else "none"
        return f"RiskScorer(modules=[{available}])"
