"""
Blockchain Bridge for MediChain AI Engine.

Provides a high-level Python interface to the PharmaChainCore,
PharmaChainScanner, and PharmaChainBatch smart contracts via web3.py.

All write operations are signed locally using the configured private key
and submitted through the JSON-RPC provider.  Read operations use
``eth_call`` and do not require gas.

Coordinate values are stored on-chain as ``int256`` scaled by 1e6.
This module transparently converts between float degrees and the
on-chain representation using helpers from ``utils.geo_utils``.
"""

from __future__ import annotations

import json
import logging
import time
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError, TransactionNotFound
from web3.middleware import ExtraDataToPOAMiddleware

import sys, os

# ---------------------------------------------------------------------------
# Ensure the ai-engine package root is importable regardless of how the
# module is invoked (direct script execution, pytest, etc.).
# ---------------------------------------------------------------------------
_AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))

from config import (
    LOCAL_RPC_URL,
    PRIVATE_KEY,
    CORE_CONTRACT_ADDRESS,
    SCANNER_CONTRACT_ADDRESS,
    BATCH_CONTRACT_ADDRESS,
)
from utils.geo_utils import (
    coords_to_contract_int,
    contract_int_to_coords,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  On-chain enums mirrored in Python
# ---------------------------------------------------------------------------

class MedicineState(IntEnum):
    """Maps to the ``State`` enum in PharmaChainCore.sol."""
    Manufactured = 0
    InTransit = 1
    AtDistributor = 2
    AtPharmacy = 3
    Dispensed = 4
    Flagged = 5


class ActorRole(IntEnum):
    """Maps to the ``Role`` enum in PharmaChainCore.sol."""
    NoRole = 0
    Manufacturer = 1
    Distributor = 2
    Pharmacy = 3
    Consumer = 4
    Regulator = 5
    Admin = 6


class FlagSeverity(IntEnum):
    """Maps to the ``FlagSeverity`` enum in PharmaChainCore.sol."""
    Low = 0
    Medium = 1
    High = 2
    Critical = 3


# ---------------------------------------------------------------------------
#  Bridge
# ---------------------------------------------------------------------------

class BlockchainBridge:
    """High-level gateway to MediChain smart contracts.

    Parameters
    ----------
    rpc_url:
        JSON-RPC endpoint (e.g. ``http://127.0.0.1:8545``).
    private_key:
        Hex-encoded private key used to sign write transactions.
    core_address:
        Deployed address of the ``PharmaChainCore`` contract.
    scanner_address:
        Deployed address of the ``PharmaChainScanner`` contract.
    batch_address:
        Deployed address of the ``PharmaChainBatch`` contract.
    """

    # Directory that contains ABI JSON files
    _ABI_DIR = Path(__file__).resolve().parent / "abis"

    def __init__(
        self,
        rpc_url: str = LOCAL_RPC_URL,
        private_key: str = PRIVATE_KEY,
        core_address: str = CORE_CONTRACT_ADDRESS,
        scanner_address: str = SCANNER_CONTRACT_ADDRESS,
        batch_address: str = BATCH_CONTRACT_ADDRESS,
    ) -> None:
        # ---- provider ----
        if rpc_url.startswith("ws"):
            self.w3 = Web3(Web3.WebsocketProvider(rpc_url))
        else:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Inject POA middleware for Ganache / local dev chains that include
        # non-standard ``extraData`` fields longer than 32 bytes.
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        if not self.w3.is_connected():
            logger.warning(
                "Web3 provider at %s is not reachable. "
                "Read/write calls will fail until the node is available.",
                rpc_url,
            )

        # ---- account ----
        self.private_key: str = private_key
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
            self.address: str = self.account.address
        else:
            self.account = None
            self.address = ""
            logger.warning("No private key configured; write operations are disabled.")

        # ---- contracts ----
        core_abi = self._load_abi("PharmaChainCore.json")
        scanner_abi = self._load_abi("PharmaChainScanner.json")
        batch_abi = self._load_abi("PharmaChainBatch.json")

        self.core: Optional[Contract] = None
        self.scanner: Optional[Contract] = None
        self.batch: Optional[Contract] = None

        if core_address:
            self.core = self.w3.eth.contract(
                address=Web3.to_checksum_address(core_address),
                abi=core_abi,
            )
        else:
            logger.warning("CORE_CONTRACT_ADDRESS not set; core contract unavailable.")

        if scanner_address:
            self.scanner = self.w3.eth.contract(
                address=Web3.to_checksum_address(scanner_address),
                abi=scanner_abi,
            )
        else:
            logger.warning("SCANNER_CONTRACT_ADDRESS not set; scanner contract unavailable.")

        if batch_address:
            self.batch = self.w3.eth.contract(
                address=Web3.to_checksum_address(batch_address),
                abi=batch_abi,
            )
        else:
            logger.warning("BATCH_CONTRACT_ADDRESS not set; batch contract unavailable.")

        logger.info(
            "BlockchainBridge initialised  rpc=%s  account=%s  core=%s  scanner=%s  batch=%s",
            rpc_url,
            self.address or "(none)",
            core_address or "(none)",
            scanner_address or "(none)",
            batch_address or "(none)",
        )

    # ------------------------------------------------------------------ #
    #  READ methods                                                       #
    # ------------------------------------------------------------------ #

    def get_medicine(self, medicine_id: int) -> Dict[str, Any]:
        """Fetch full medicine record from ``PharmaChainCore.medicines(id)``.

        Returns a dictionary with human-readable keys.  The ``state`` field
        is returned both as an integer and its enum label.
        """
        if self.core is None:
            raise RuntimeError("Core contract is not configured.")

        try:
            result = self.core.functions.medicines(medicine_id).call()
        except ContractLogicError as exc:
            logger.error("medicines(%s) reverted: %s", medicine_id, exc)
            raise

        # result is a tuple matching the ABI output order
        (
            mid,
            name,
            batch_number,
            manufacturer,
            manufacture_date,
            expiry_date,
            content_hash,
            state,
            current_holder,
            flag_count,
            exists,
        ) = result

        return {
            "id": mid,
            "name": name,
            "batchNumber": batch_number,
            "manufacturer": manufacturer,
            "manufactureDate": manufacture_date,
            "expiryDate": expiry_date,
            "contentHash": content_hash.hex() if isinstance(content_hash, bytes) else content_hash,
            "state": int(state),
            "stateLabel": MedicineState(state).name if state <= max(MedicineState) else f"Unknown({state})",
            "currentHolder": current_holder,
            "flagCount": flag_count,
            "exists": exists,
        }

    def get_custody_history(self, medicine_id: int) -> List[Dict[str, Any]]:
        """Return the full custody chain for a medicine.

        Each entry contains ``from``, ``to``, ``timestamp``, ``fromState``,
        ``toState``, and decoded GPS coordinates.
        """
        if self.core is None:
            raise RuntimeError("Core contract is not configured.")

        try:
            records = self.core.functions.getCustodyHistory(medicine_id).call()
        except ContractLogicError as exc:
            logger.error("getCustodyHistory(%s) reverted: %s", medicine_id, exc)
            raise

        history: List[Dict[str, Any]] = []
        for rec in records:
            from_addr, to_addr, ts, from_state, to_state, lat_int, lng_int = rec
            lat, lng = contract_int_to_coords(lat_int, lng_int)
            history.append({
                "from": from_addr,
                "to": to_addr,
                "timestamp": ts,
                "fromState": int(from_state),
                "fromStateLabel": MedicineState(from_state).name if from_state <= max(MedicineState) else f"Unknown({from_state})",
                "toState": int(to_state),
                "toStateLabel": MedicineState(to_state).name if to_state <= max(MedicineState) else f"Unknown({to_state})",
                "latitude": lat,
                "longitude": lng,
            })
        return history

    def get_scan_history(self, medicine_id: int) -> List[Dict[str, Any]]:
        """Return all scan events for a medicine from the Scanner contract."""
        if self.scanner is None:
            raise RuntimeError("Scanner contract is not configured.")

        try:
            records = self.scanner.functions.getScanHistory(medicine_id).call()
        except ContractLogicError as exc:
            logger.error("getScanHistory(%s) reverted: %s", medicine_id, exc)
            raise

        scans: List[Dict[str, Any]] = []
        for rec in records:
            mid, scanner_addr, ts, lat_int, lng_int, location, device_id = rec
            lat, lng = contract_int_to_coords(lat_int, lng_int)
            scans.append({
                "medicineId": mid,
                "scanner": scanner_addr,
                "timestamp": ts,
                "latitude": lat,
                "longitude": lng,
                "location": location,
                "deviceId": device_id,
            })
        return scans

    def get_actor(self, address: str) -> Dict[str, Any]:
        """Fetch actor (supply-chain participant) details by address."""
        if self.core is None:
            raise RuntimeError("Core contract is not configured.")

        checksum = Web3.to_checksum_address(address)

        try:
            result = self.core.functions.actors(checksum).call()
        except ContractLogicError as exc:
            logger.error("actors(%s) reverted: %s", address, exc)
            raise

        addr, name, role, is_active, license_number, lat_int, lng_int = result
        lat, lng = contract_int_to_coords(lat_int, lng_int)

        return {
            "address": addr,
            "name": name,
            "role": int(role),
            "roleLabel": ActorRole(role).name if role <= max(ActorRole) else f"Unknown({role})",
            "isActive": is_active,
            "licenseNumber": license_number,
            "latitude": lat,
            "longitude": lng,
        }

    def is_registered(self, medicine_id: int) -> bool:
        """Check whether a medicine ID has been registered on-chain."""
        if self.core is None:
            raise RuntimeError("Core contract is not configured.")

        try:
            return self.core.functions.isMedicineRegistered(medicine_id).call()
        except ContractLogicError as exc:
            logger.error("isMedicineRegistered(%s) reverted: %s", medicine_id, exc)
            raise

    def verify_content_hash(self, medicine_id: int, hash_bytes32: bytes) -> bool:
        """Verify that a medicine's content hash matches the on-chain record.

        Parameters
        ----------
        medicine_id:
            Numeric ID of the medicine.
        hash_bytes32:
            The 32-byte hash to verify.  If a hex string is supplied it will
            be converted to ``bytes`` automatically.
        """
        if self.core is None:
            raise RuntimeError("Core contract is not configured.")

        # Accept hex strings for convenience
        if isinstance(hash_bytes32, str):
            hash_bytes32 = bytes.fromhex(hash_bytes32.removeprefix("0x"))

        # Ensure it is exactly 32 bytes (pad with leading zeros if shorter)
        if len(hash_bytes32) < 32:
            hash_bytes32 = hash_bytes32.rjust(32, b"\x00")
        elif len(hash_bytes32) > 32:
            raise ValueError("hash_bytes32 must be at most 32 bytes")

        try:
            return self.core.functions.verifyContentHash(medicine_id, hash_bytes32).call()
        except ContractLogicError as exc:
            logger.error("verifyContentHash(%s, ...) reverted: %s", medicine_id, exc)
            raise

    def get_scan_stats(self) -> Dict[str, int]:
        """Return aggregate scanning statistics from the Scanner contract."""
        if self.scanner is None:
            raise RuntimeError("Scanner contract is not configured.")

        try:
            total_scans, unique_medicines, unique_scanners, velocity_alerts = (
                self.scanner.functions.getStats().call()
            )
        except ContractLogicError as exc:
            logger.error("getStats() reverted: %s", exc)
            raise

        return {
            "totalScans": total_scans,
            "uniqueMedicines": unique_medicines,
            "uniqueScanners": unique_scanners,
            "velocityAlerts": velocity_alerts,
        }

    # ------------------------------------------------------------------ #
    #  WRITE methods                                                      #
    # ------------------------------------------------------------------ #

    def flag_drug(self, medicine_id: int, severity: int) -> str:
        """Flag a medicine as suspicious or counterfeit.

        Parameters
        ----------
        medicine_id:
            On-chain medicine ID to flag.
        severity:
            ``FlagSeverity`` enum value (0-3).

        Returns
        -------
        str
            Transaction hash (hex-encoded, ``0x``-prefixed).
        """
        if self.core is None:
            raise RuntimeError("Core contract is not configured.")

        if severity not in range(4):
            raise ValueError(f"severity must be 0..3, got {severity}")

        contract_fn = self.core.functions.flagDrug(medicine_id, severity)
        tx_hash = self._send_transaction(contract_fn)
        logger.info(
            "flagDrug(medicine=%s, severity=%s) => tx %s",
            medicine_id,
            FlagSeverity(severity).name,
            tx_hash,
        )
        return tx_hash

    def log_scan(
        self,
        medicine_id: int,
        lat: float,
        lng: float,
        location: str,
        device_id: str,
    ) -> str:
        """Log a single drug scan event on the Scanner contract.

        Parameters
        ----------
        medicine_id:
            On-chain medicine ID.
        lat, lng:
            GPS coordinates in decimal degrees (float).
        location:
            Human-readable location string (e.g. ``"Mumbai Warehouse"``).
        device_id:
            Identifier of the scanning device.

        Returns
        -------
        str
            Transaction hash.
        """
        if self.scanner is None:
            raise RuntimeError("Scanner contract is not configured.")

        lat_int, lng_int = coords_to_contract_int(lat, lng)
        contract_fn = self.scanner.functions.logScan(
            medicine_id,
            lat_int,
            lng_int,
            location,
            device_id,
        )
        tx_hash = self._send_transaction(contract_fn)
        logger.info(
            "logScan(medicine=%s, lat=%.6f, lng=%.6f, loc=%s, dev=%s) => tx %s",
            medicine_id, lat, lng, location, device_id, tx_hash,
        )
        return tx_hash

    def log_batch_scan(
        self,
        medicine_ids: List[int],
        lat: float,
        lng: float,
        location: str,
        device_id: str,
    ) -> str:
        """Log a batch scan of multiple medicines in a single transaction.

        Parameters
        ----------
        medicine_ids:
            List of on-chain medicine IDs.
        lat, lng:
            GPS coordinates in decimal degrees (float).
        location:
            Human-readable location string.
        device_id:
            Identifier of the scanning device.

        Returns
        -------
        str
            Transaction hash.
        """
        if self.batch is None:
            raise RuntimeError("Batch contract is not configured.")

        if not medicine_ids:
            raise ValueError("medicine_ids must not be empty")

        lat_int, lng_int = coords_to_contract_int(lat, lng)
        contract_fn = self.batch.functions.logBatchScan(
            medicine_ids,
            lat_int,
            lng_int,
            location,
            device_id,
        )
        tx_hash = self._send_transaction(contract_fn)
        logger.info(
            "logBatchScan(ids=%s, lat=%.6f, lng=%.6f, loc=%s, dev=%s) => tx %s",
            medicine_ids, lat, lng, location, device_id, tx_hash,
        )
        return tx_hash

    # ------------------------------------------------------------------ #
    #  HELPERS                                                            #
    # ------------------------------------------------------------------ #

    def _load_abi(self, filename: str) -> list:
        """Load an ABI JSON array from the ``abis/`` directory.

        Parameters
        ----------
        filename:
            Name of the JSON file inside ``blockchain/abis/``, e.g.
            ``"PharmaChainCore.json"``.

        Returns
        -------
        list
            Parsed ABI suitable for ``web3.eth.contract(abi=...)``.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        json.JSONDecodeError
            If the file is not valid JSON.
        """
        abi_path = self._ABI_DIR / filename
        if not abi_path.exists():
            raise FileNotFoundError(f"ABI file not found: {abi_path}")

        with open(abi_path, "r", encoding="utf-8") as f:
            abi = json.load(f)

        if not isinstance(abi, list):
            raise ValueError(
                f"Expected a JSON array in {abi_path}, got {type(abi).__name__}"
            )

        logger.debug("Loaded ABI %s (%d entries)", filename, len(abi))
        return abi

    def _send_transaction(self, contract_fn) -> str:
        """Build, sign, and broadcast a write transaction.

        Parameters
        ----------
        contract_fn:
            A bound contract function, e.g.
            ``self.core.functions.flagDrug(1, 2)``.

        Returns
        -------
        str
            The transaction hash as a hex string (``0x``-prefixed).

        Raises
        ------
        RuntimeError
            If no private key is configured, or the transaction reverts.
        """
        if not self.private_key or self.account is None:
            raise RuntimeError(
                "Cannot send transaction: no private key configured."
            )

        nonce = self.w3.eth.get_transaction_count(self.address)

        # Estimate gas; add a 20 % buffer to avoid out-of-gas on edge cases.
        try:
            gas_estimate = contract_fn.estimate_gas({"from": self.address})
        except ContractLogicError as exc:
            raise RuntimeError(f"Transaction would revert: {exc}") from exc

        gas_limit = int(gas_estimate * 1.2)

        # Build the raw transaction dictionary.
        tx = contract_fn.build_transaction(
            {
                "from": self.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": self.w3.eth.chain_id,
            }
        )

        # Sign locally.
        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)

        # Broadcast.
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        hex_hash = tx_hash.hex()

        logger.debug("Transaction sent: %s  (gas_limit=%d)", hex_hash, gas_limit)

        # Wait for the receipt so callers know whether it succeeded.
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        except Exception as exc:
            logger.error("Timed out waiting for tx %s: %s", hex_hash, exc)
            # Return the hash anyway; the caller can poll later.
            return hex_hash

        if receipt["status"] != 1:
            raise RuntimeError(
                f"Transaction {hex_hash} was mined but reverted (status=0). "
                f"Gas used: {receipt['gasUsed']}"
            )

        logger.debug(
            "Transaction %s confirmed in block %s (gas used: %s)",
            hex_hash,
            receipt["blockNumber"],
            receipt["gasUsed"],
        )
        return hex_hash


# ---------------------------------------------------------------------------
#  Module-level convenience singleton
# ---------------------------------------------------------------------------

_default_bridge: Optional[BlockchainBridge] = None


def get_bridge() -> BlockchainBridge:
    """Return (or lazily create) a module-level ``BlockchainBridge`` singleton.

    Uses default configuration from ``config.py``.
    """
    global _default_bridge
    if _default_bridge is None:
        _default_bridge = BlockchainBridge()
    return _default_bridge
