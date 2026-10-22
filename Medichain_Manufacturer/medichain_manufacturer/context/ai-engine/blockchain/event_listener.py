"""
Blockchain Event Listener for MediChain.

Runs as an ``asyncio`` background task, polling smart-contract event logs
every few seconds.  Parsed events are enriched with on-chain data (medicine
details, actor names) and forwarded to an ``alert_callback`` which typically
pushes them to connected WebSocket clients.

When ``SIMULATION_MODE`` is enabled the listener replays a stream of
synthetic events instead of polling the chain, making it possible to
demonstrate the full UI without a running blockchain node.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

import sys

_AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))

from config import SIMULATION_MODE
from blockchain.bridge import (
    BlockchainBridge,
    MedicineState,
    ActorRole,
    FlagSeverity,
    get_bridge,
)
from utils.geo_utils import contract_int_to_coords

logger = logging.getLogger(__name__)

# Type alias for the callback signature.
AlertCallback = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

# How often the listener polls the node for new events (seconds).
_POLL_INTERVAL: float = 2.0

# How often the internal event buffer is flushed to the callback (seconds).
_FLUSH_INTERVAL: float = 10.0

# Synthetic-mode: base delay between replayed events (seconds).
_SIMULATION_EVENT_INTERVAL: float = 3.0


# ---------------------------------------------------------------------------
#  Listener
# ---------------------------------------------------------------------------

class BlockchainEventListener:
    """Background event listener that tracks on-chain activity.

    Parameters
    ----------
    bridge:
        An initialised :class:`BlockchainBridge` used for reading event logs
        and enriching events with on-chain data.
    alert_callback:
        An ``async`` callable that receives a dict describing a parsed event.
        Typically this pushes the event to a WebSocket broadcast channel.
    """

    def __init__(
        self,
        bridge: Optional[BlockchainBridge] = None,
        alert_callback: Optional[AlertCallback] = None,
    ) -> None:
        self.bridge: BlockchainBridge = bridge or get_bridge()
        self.alert_callback: Optional[AlertCallback] = alert_callback
        self.running: bool = False

        # Internal event buffer used for batch flushing.
        self._buffer: List[Dict[str, Any]] = []
        self._last_flush: float = time.monotonic()

        # Block cursors -- start from the current head so we only see new events.
        self._last_core_block: int = 0
        self._last_scanner_block: int = 0

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                          #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        """Begin listening.  Runs until :meth:`stop` is called.

        This method is designed to be wrapped in ``asyncio.create_task()``
        so it executes concurrently with the rest of the application.
        """
        self.running = True
        logger.info(
            "BlockchainEventListener starting (simulation=%s)", SIMULATION_MODE
        )

        # Initialise block cursors to the current head so we do not replay
        # the entire chain history on first start.
        try:
            current_block = self.bridge.w3.eth.block_number
            self._last_core_block = current_block
            self._last_scanner_block = current_block
            logger.info("Starting from block %d", current_block)
        except Exception:
            logger.warning(
                "Could not read current block number; starting from 0."
            )

        if SIMULATION_MODE:
            await self._run_simulation_loop()
        else:
            await self._run_poll_loop()

    async def stop(self) -> None:
        """Signal the listener to stop after the current iteration."""
        logger.info("BlockchainEventListener stopping.")
        self.running = False

    # ------------------------------------------------------------------ #
    #  Real polling loop                                                  #
    # ------------------------------------------------------------------ #

    async def _run_poll_loop(self) -> None:
        """Core loop that polls event logs from the chain."""
        while self.running:
            try:
                await self._poll_events()
            except Exception:
                logger.exception("Error during event poll cycle; will retry.")

            # Flush the buffer periodically.
            now = time.monotonic()
            if now - self._last_flush >= _FLUSH_INTERVAL:
                await self._flush_buffer()
                self._last_flush = now

            await asyncio.sleep(_POLL_INTERVAL)

        # Final flush on shutdown.
        await self._flush_buffer()

    async def _poll_events(self) -> None:
        """Poll for new events from all tracked contracts."""
        try:
            latest_block = self.bridge.w3.eth.block_number
        except Exception:
            logger.warning("Cannot reach provider; skipping poll cycle.")
            return

        # --- Core contract events ---
        if self.bridge.core is not None and latest_block > self._last_core_block:
            from_block = self._last_core_block + 1
            await self._poll_core_events(from_block, latest_block)
            self._last_core_block = latest_block

        # --- Scanner contract events ---
        if self.bridge.scanner is not None and latest_block > self._last_scanner_block:
            from_block = self._last_scanner_block + 1
            await self._poll_scanner_events(from_block, latest_block)
            self._last_scanner_block = latest_block

    async def _poll_core_events(self, from_block: int, to_block: int) -> None:
        """Fetch and dispatch events from the PharmaChainCore contract."""
        core = self.bridge.core

        # DrugFlagged
        try:
            flagged_filter = core.events.DrugFlagged.create_filter(
                fromBlock=from_block, toBlock=to_block
            )
            for event in flagged_filter.get_all_entries():
                await self._process_drug_flagged(event)
        except Exception:
            logger.debug("DrugFlagged filter failed (event may not exist yet).")

        # CustodyTransferred
        try:
            custody_filter = core.events.CustodyTransferred.create_filter(
                fromBlock=from_block, toBlock=to_block
            )
            for event in custody_filter.get_all_entries():
                await self._process_custody_transferred(event)
        except Exception:
            logger.debug("CustodyTransferred filter failed.")

        # MedicineRegistered
        try:
            registered_filter = core.events.MedicineRegistered.create_filter(
                fromBlock=from_block, toBlock=to_block
            )
            for event in registered_filter.get_all_entries():
                await self._process_medicine_registered(event)
        except Exception:
            logger.debug("MedicineRegistered filter failed.")

    async def _poll_scanner_events(self, from_block: int, to_block: int) -> None:
        """Fetch and dispatch events from the PharmaChainScanner contract."""
        scanner = self.bridge.scanner

        # DrugScanned
        try:
            scanned_filter = scanner.events.DrugScanned.create_filter(
                fromBlock=from_block, toBlock=to_block
            )
            for event in scanned_filter.get_all_entries():
                await self._process_drug_scanned(event)
        except Exception:
            logger.debug("DrugScanned filter failed.")

        # VelocityAlert
        try:
            velocity_filter = scanner.events.VelocityAlert.create_filter(
                fromBlock=from_block, toBlock=to_block
            )
            for event in velocity_filter.get_all_entries():
                await self._process_velocity_alert(event)
        except Exception:
            logger.debug("VelocityAlert filter failed.")

    # ------------------------------------------------------------------ #
    #  Event processors                                                   #
    # ------------------------------------------------------------------ #

    async def _process_drug_scanned(self, event) -> None:
        """Parse a ``DrugScanned`` event and enrich it with medicine data."""
        args = event["args"]
        medicine_id = args["medicineId"]

        lat, lng = contract_int_to_coords(args["latitude"], args["longitude"])

        # Attempt to enrich with medicine details.
        medicine_name = ""
        try:
            med = self.bridge.get_medicine(medicine_id)
            medicine_name = med.get("name", "")
        except Exception:
            logger.debug("Could not enrich DrugScanned for medicine %s", medicine_id)

        payload = {
            "type": "DrugScanned",
            "medicineId": medicine_id,
            "medicineName": medicine_name,
            "scanner": args["scanner"],
            "latitude": lat,
            "longitude": lng,
            "location": args["location"],
            "deviceId": args["deviceId"],
            "timestamp": args["timestamp"],
            "blockNumber": event.get("blockNumber"),
            "transactionHash": event.get("transactionHash", b"").hex()
            if isinstance(event.get("transactionHash"), bytes)
            else str(event.get("transactionHash", "")),
        }

        await self._emit(payload)

    async def _process_velocity_alert(self, event) -> None:
        """Parse a ``VelocityAlert`` event -- this is a high-priority alert."""
        args = event["args"]
        medicine_id = args["medicineId"]

        medicine_name = ""
        try:
            med = self.bridge.get_medicine(medicine_id)
            medicine_name = med.get("name", "")
        except Exception:
            pass

        payload = {
            "type": "VelocityAlert",
            "severity": "high",
            "medicineId": medicine_id,
            "medicineName": medicine_name,
            "distanceKm": args["distanceKm"],
            "timeDeltaSeconds": args["timeDeltaSeconds"],
            "speedKmh": args["speedKmh"],
            "timestamp": args["timestamp"],
            "blockNumber": event.get("blockNumber"),
            "transactionHash": event.get("transactionHash", b"").hex()
            if isinstance(event.get("transactionHash"), bytes)
            else str(event.get("transactionHash", "")),
            "message": (
                f"Velocity anomaly detected for medicine {medicine_id} "
                f"({medicine_name}): {args['speedKmh']} km/h over "
                f"{args['distanceKm']} km in {args['timeDeltaSeconds']}s"
            ),
        }

        await self._emit(payload)

    async def _process_drug_flagged(self, event) -> None:
        """Parse a ``DrugFlagged`` event."""
        args = event["args"]
        medicine_id = args["medicineId"]

        medicine_name = ""
        try:
            med = self.bridge.get_medicine(medicine_id)
            medicine_name = med.get("name", "")
        except Exception:
            pass

        severity_int = args["severity"]
        severity_label = (
            FlagSeverity(severity_int).name
            if severity_int <= max(FlagSeverity)
            else f"Unknown({severity_int})"
        )

        payload = {
            "type": "DrugFlagged",
            "severity": severity_label.lower(),
            "medicineId": medicine_id,
            "medicineName": medicine_name,
            "flaggedBy": args["flaggedBy"],
            "severityCode": severity_int,
            "timestamp": args["timestamp"],
            "blockNumber": event.get("blockNumber"),
            "transactionHash": event.get("transactionHash", b"").hex()
            if isinstance(event.get("transactionHash"), bytes)
            else str(event.get("transactionHash", "")),
            "message": (
                f"Medicine {medicine_id} ({medicine_name}) flagged with "
                f"severity {severity_label} by {args['flaggedBy']}"
            ),
        }

        await self._emit(payload)

    async def _process_custody_transferred(self, event) -> None:
        """Parse a ``CustodyTransferred`` event."""
        args = event["args"]
        medicine_id = args["medicineId"]

        medicine_name = ""
        from_name = args["from"]
        to_name = args["to"]
        try:
            med = self.bridge.get_medicine(medicine_id)
            medicine_name = med.get("name", "")
        except Exception:
            pass
        try:
            actor_from = self.bridge.get_actor(args["from"])
            from_name = actor_from.get("name") or args["from"]
        except Exception:
            pass
        try:
            actor_to = self.bridge.get_actor(args["to"])
            to_name = actor_to.get("name") or args["to"]
        except Exception:
            pass

        from_state = args["fromState"]
        to_state = args["toState"]
        from_label = MedicineState(from_state).name if from_state <= max(MedicineState) else str(from_state)
        to_label = MedicineState(to_state).name if to_state <= max(MedicineState) else str(to_state)

        payload = {
            "type": "CustodyTransferred",
            "medicineId": medicine_id,
            "medicineName": medicine_name,
            "from": args["from"],
            "fromName": from_name,
            "to": args["to"],
            "toName": to_name,
            "fromState": from_state,
            "fromStateLabel": from_label,
            "toState": to_state,
            "toStateLabel": to_label,
            "timestamp": args["timestamp"],
            "blockNumber": event.get("blockNumber"),
            "transactionHash": event.get("transactionHash", b"").hex()
            if isinstance(event.get("transactionHash"), bytes)
            else str(event.get("transactionHash", "")),
            "message": (
                f"Medicine {medicine_id} ({medicine_name}) custody transferred "
                f"from {from_name} to {to_name} ({from_label} -> {to_label})"
            ),
        }

        await self._emit(payload)

    async def _process_medicine_registered(self, event) -> None:
        """Parse a ``MedicineRegistered`` event."""
        args = event["args"]
        medicine_id = args["medicineId"]

        payload = {
            "type": "MedicineRegistered",
            "medicineId": medicine_id,
            "name": args["name"],
            "batchNumber": args["batchNumber"],
            "manufacturer": args["manufacturer"],
            "timestamp": args["timestamp"],
            "blockNumber": event.get("blockNumber"),
            "transactionHash": event.get("transactionHash", b"").hex()
            if isinstance(event.get("transactionHash"), bytes)
            else str(event.get("transactionHash", "")),
            "message": (
                f"New medicine registered: {args['name']} (ID {medicine_id}, "
                f"batch {args['batchNumber']})"
            ),
        }

        await self._emit(payload)

    # ------------------------------------------------------------------ #
    #  Buffer / emit                                                     #
    # ------------------------------------------------------------------ #

    async def _emit(self, payload: Dict[str, Any]) -> None:
        """Immediately dispatch a single event via the callback, and also
        buffer it for batch processing."""
        # Always add a server-side receive timestamp.
        payload.setdefault(
            "receivedAt", datetime.now(timezone.utc).isoformat()
        )

        logger.info("Event: %s (medicine=%s)", payload["type"], payload.get("medicineId"))

        # Immediate delivery.
        if self.alert_callback is not None:
            try:
                await self.alert_callback(payload)
            except Exception:
                logger.exception("alert_callback raised for event %s", payload["type"])

        # Buffer for batch flushing.
        self._buffer.append(payload)

    async def _flush_buffer(self) -> None:
        """Flush the accumulated event buffer.

        This could be extended to write events to a database, push to an
        analytics pipeline, or emit a ``batch`` WebSocket message.
        """
        if not self._buffer:
            return

        count = len(self._buffer)
        logger.debug("Flushing %d buffered events", count)

        # If the callback supports batch delivery, we could call it here with
        # the full buffer.  For now we simply clear the buffer since events
        # were already individually dispatched in ``_emit``.
        self._buffer.clear()

    # ------------------------------------------------------------------ #
    #  Simulation mode                                                    #
    # ------------------------------------------------------------------ #

    async def _run_simulation_loop(self) -> None:
        """Replay synthetic events for demo / development purposes.

        Generates a varied stream of plausible events without needing a
        live blockchain node.
        """
        logger.info("Running in SIMULATION_MODE -- replaying synthetic events.")

        # Synthetic medicine catalogue for realistic event generation.
        _medicines = [
            {"id": 1, "name": "Paracetamol 500mg", "batch": "BATCH-2025-001"},
            {"id": 2, "name": "Amoxicillin 250mg", "batch": "BATCH-2025-002"},
            {"id": 3, "name": "Metformin 850mg", "batch": "BATCH-2025-003"},
            {"id": 4, "name": "Ibuprofen 400mg", "batch": "BATCH-2025-004"},
            {"id": 5, "name": "Azithromycin 500mg", "batch": "BATCH-2025-005"},
            {"id": 6, "name": "Omeprazole 20mg", "batch": "BATCH-2025-006"},
        ]

        # Synthetic locations along an Indian supply chain.
        _locations = [
            {"name": "Mumbai Warehouse", "lat": 19.076090, "lng": 72.877426},
            {"name": "Delhi Distribution Center", "lat": 28.613939, "lng": 77.209023},
            {"name": "Bangalore Pharmacy Hub", "lat": 12.971599, "lng": 77.594566},
            {"name": "Chennai Port Facility", "lat": 13.082680, "lng": 80.270721},
            {"name": "Kolkata Regional Store", "lat": 22.572646, "lng": 88.363895},
            {"name": "Hyderabad Central Depot", "lat": 17.385044, "lng": 78.486671},
        ]

        _actors = [
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
            "0x3333333333333333333333333333333333333333",
            "0x4444444444444444444444444444444444444444",
        ]

        _event_types = [
            "DrugScanned",
            "DrugScanned",
            "DrugScanned",       # weighted towards scans
            "CustodyTransferred",
            "CustodyTransferred",
            "DrugFlagged",
            "VelocityAlert",
            "MedicineRegistered",
        ]

        sim_medicine_counter = 100  # IDs for newly "registered" medicines

        while self.running:
            event_type = random.choice(_event_types)
            med = random.choice(_medicines)
            loc = random.choice(_locations)
            now_ts = int(time.time())

            if event_type == "DrugScanned":
                payload = {
                    "type": "DrugScanned",
                    "medicineId": med["id"],
                    "medicineName": med["name"],
                    "scanner": random.choice(_actors),
                    "latitude": loc["lat"] + random.uniform(-0.01, 0.01),
                    "longitude": loc["lng"] + random.uniform(-0.01, 0.01),
                    "location": loc["name"],
                    "deviceId": f"SIM-DEVICE-{random.randint(100, 999)}",
                    "timestamp": now_ts,
                    "blockNumber": random.randint(1000, 99999),
                    "transactionHash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                }

            elif event_type == "CustodyTransferred":
                from_idx = random.randint(0, len(_actors) - 1)
                to_idx = (from_idx + random.randint(1, len(_actors) - 1)) % len(_actors)
                from_state = random.randint(0, 3)
                to_state = min(from_state + 1, 4)
                payload = {
                    "type": "CustodyTransferred",
                    "medicineId": med["id"],
                    "medicineName": med["name"],
                    "from": _actors[from_idx],
                    "fromName": f"Actor-{from_idx}",
                    "to": _actors[to_idx],
                    "toName": f"Actor-{to_idx}",
                    "fromState": from_state,
                    "fromStateLabel": MedicineState(from_state).name,
                    "toState": to_state,
                    "toStateLabel": MedicineState(to_state).name,
                    "timestamp": now_ts,
                    "blockNumber": random.randint(1000, 99999),
                    "transactionHash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    "message": (
                        f"Medicine {med['id']} ({med['name']}) custody transferred "
                        f"from Actor-{from_idx} to Actor-{to_idx} "
                        f"({MedicineState(from_state).name} -> {MedicineState(to_state).name})"
                    ),
                }

            elif event_type == "DrugFlagged":
                severity = random.choices(
                    [FlagSeverity.Low, FlagSeverity.Medium, FlagSeverity.High, FlagSeverity.Critical],
                    weights=[40, 30, 20, 10],
                )[0]
                payload = {
                    "type": "DrugFlagged",
                    "severity": severity.name.lower(),
                    "medicineId": med["id"],
                    "medicineName": med["name"],
                    "flaggedBy": random.choice(_actors),
                    "severityCode": int(severity),
                    "timestamp": now_ts,
                    "blockNumber": random.randint(1000, 99999),
                    "transactionHash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    "message": (
                        f"Medicine {med['id']} ({med['name']}) flagged with "
                        f"severity {severity.name}"
                    ),
                }

            elif event_type == "VelocityAlert":
                dist = random.randint(200, 2000)
                time_delta = random.randint(60, 600)
                speed = int(dist / (time_delta / 3600))
                payload = {
                    "type": "VelocityAlert",
                    "severity": "high",
                    "medicineId": med["id"],
                    "medicineName": med["name"],
                    "distanceKm": dist,
                    "timeDeltaSeconds": time_delta,
                    "speedKmh": speed,
                    "timestamp": now_ts,
                    "blockNumber": random.randint(1000, 99999),
                    "transactionHash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    "message": (
                        f"Velocity anomaly detected for medicine {med['id']} "
                        f"({med['name']}): {speed} km/h over {dist} km in {time_delta}s"
                    ),
                }

            elif event_type == "MedicineRegistered":
                sim_medicine_counter += 1
                payload = {
                    "type": "MedicineRegistered",
                    "medicineId": sim_medicine_counter,
                    "name": f"Simulated Drug #{sim_medicine_counter}",
                    "batchNumber": f"SIM-BATCH-{sim_medicine_counter}",
                    "manufacturer": random.choice(_actors),
                    "timestamp": now_ts,
                    "blockNumber": random.randint(1000, 99999),
                    "transactionHash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    "message": (
                        f"New medicine registered: Simulated Drug #{sim_medicine_counter} "
                        f"(ID {sim_medicine_counter}, batch SIM-BATCH-{sim_medicine_counter})"
                    ),
                }
            else:
                continue

            await self._emit(payload)

            # Periodically flush the buffer.
            now = time.monotonic()
            if now - self._last_flush >= _FLUSH_INTERVAL:
                await self._flush_buffer()
                self._last_flush = now

            # Jittered delay between synthetic events.
            delay = _SIMULATION_EVENT_INTERVAL + random.uniform(-1.0, 1.0)
            await asyncio.sleep(max(0.5, delay))

        # Final flush.
        await self._flush_buffer()


# ---------------------------------------------------------------------------
#  Convenience function for application startup
# ---------------------------------------------------------------------------

async def start_event_listener(
    bridge: Optional[BlockchainBridge] = None,
    alert_callback: Optional[AlertCallback] = None,
) -> BlockchainEventListener:
    """Create and start a :class:`BlockchainEventListener` as a background task.

    Returns the listener instance so the caller can later call ``stop()``.

    Usage::

        listener = await start_event_listener(bridge, my_ws_broadcast)
        # ... later, during shutdown ...
        await listener.stop()
    """
    listener = BlockchainEventListener(bridge=bridge, alert_callback=alert_callback)
    asyncio.create_task(listener.start())
    return listener
