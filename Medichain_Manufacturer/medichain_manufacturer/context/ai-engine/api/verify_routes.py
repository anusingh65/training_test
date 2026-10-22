"""
Pill Image Verification Routes for MediChain AI Engine.

Endpoints:
  POST /api/verify-image   -- Upload a pill image for CNN-based authenticity
                              verification.  Optionally compares the generated
                              embedding hash against the on-chain contentHash
                              for a given medicine ID.
  POST /api/verify-hash    -- Compare a provided hash against the on-chain
                              contentHash without uploading an image.

The PillVerifier model produces:
  - confidence (float): probability the pill is authentic
  - prediction (str): "authentic" | "suspicious" | "counterfeit"
  - embedding_hash (str): SHA-256 of the 128-dim embedding vector
  - embedding (ndarray): raw 128-dim vector (not returned to the client)
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from PIL import Image

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Response models                                                            #
# --------------------------------------------------------------------------- #

class VerificationResult(BaseModel):
    """JSON schema for a pill verification response."""
    confidence: float = Field(..., ge=0.0, le=1.0, description="Probability of authenticity")
    prediction: str = Field(..., description="Classification: authentic, suspicious, or counterfeit")
    embedding_hash: str = Field(..., description="SHA-256 hash of the embedding vector (0x-prefixed)")
    on_chain_match: Optional[bool] = Field(None, description="True if embedding hash matches on-chain contentHash")
    on_chain_content_hash: Optional[str] = Field(None, description="The on-chain contentHash for comparison")
    medicine_id: Optional[int] = Field(None, description="Medicine ID if provided")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")


class HashVerificationResult(BaseModel):
    """JSON schema for a hash-only verification response."""
    medicine_id: int
    hash_provided: str
    on_chain_match: bool
    on_chain_content_hash: Optional[str] = None


# --------------------------------------------------------------------------- #
#  Routes                                                                     #
# --------------------------------------------------------------------------- #

@router.post("/verify-image", response_model=VerificationResult)
async def verify_image(
    request: Request,
    file: UploadFile = File(..., description="Pill photograph (JPEG, PNG, or WebP)"),
    medicine_id: Optional[int] = Query(None, description="On-chain medicine ID for hash comparison"),
):
    """Verify a pill image using the CNN-based PillVerifier.

    The uploaded image is resized and fed through EfficientNet-B0 with a
    custom classification head.  The model outputs an authenticity confidence
    score, a categorical prediction, and a 128-dimensional embedding vector
    whose SHA-256 hash can be compared against the on-chain contentHash.

    If ``medicine_id`` is provided and a blockchain connection is available,
    the endpoint will additionally verify that the computed embedding hash
    matches the medicine's on-chain contentHash.

    **Accepted formats:** JPEG, PNG, WebP, BMP, TIFF.

    Returns a ``VerificationResult`` JSON object.
    """
    start_time = time.perf_counter()

    # -- Validate model availability ---------------------------------------- #
    pill_verifier = request.app.state.pill_verifier
    if pill_verifier is None:
        raise HTTPException(
            status_code=503,
            detail="PillVerifier model is not loaded. The service is starting up or the model failed to initialise.",
        )

    # -- Read and decode the uploaded image --------------------------------- #
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to decode uploaded image: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=f"Could not decode the uploaded image: {exc}",
        )

    # -- Run verification --------------------------------------------------- #
    try:
        result = pill_verifier.verify(image)
    except Exception as exc:
        logger.error("PillVerifier.verify() failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image verification failed: {exc}",
        )

    confidence: float = result["confidence"]
    prediction: str = result["prediction"]
    embedding_hash: str = result["embedding_hash"]

    # Increment stats counter.
    request.app.state.stats["total_verifications"] += 1
    request.app.state.stats["total_scans"] += 1

    # -- Optional on-chain comparison --------------------------------------- #
    on_chain_match: Optional[bool] = None
    on_chain_content_hash: Optional[str] = None

    if medicine_id is not None:
        bridge = request.app.state.bridge
        if bridge is not None:
            try:
                # Fetch the medicine record to get its contentHash.
                medicine = bridge.get_medicine(medicine_id)
                if medicine.get("exists"):
                    stored_hash = medicine.get("contentHash", "")
                    on_chain_content_hash = f"0x{stored_hash}" if not stored_hash.startswith("0x") else stored_hash

                    # The embedding_hash is "0x" + 64 hex chars.
                    # The on-chain contentHash is bytes32 (64 hex chars).
                    # Normalise both to lowercase hex without "0x" prefix for comparison.
                    local_hex = embedding_hash.lower().removeprefix("0x")
                    chain_hex = on_chain_content_hash.lower().removeprefix("0x")

                    # If the chain hash is all zeros, treat as "not set".
                    if chain_hex == "0" * 64:
                        on_chain_match = None  # not set
                    else:
                        on_chain_match = local_hex == chain_hex
                else:
                    logger.info("Medicine ID %d does not exist on-chain.", medicine_id)
            except Exception as exc:
                logger.warning(
                    "Could not compare on-chain hash for medicine %d: %s",
                    medicine_id,
                    exc,
                )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return VerificationResult(
        confidence=confidence,
        prediction=prediction,
        embedding_hash=embedding_hash,
        on_chain_match=on_chain_match,
        on_chain_content_hash=on_chain_content_hash,
        medicine_id=medicine_id,
        processing_time_ms=round(elapsed_ms, 2),
    )


@router.post("/verify-hash", response_model=HashVerificationResult)
async def verify_hash(
    request: Request,
    medicine_id: int = Query(..., description="On-chain medicine ID"),
    content_hash: str = Query(..., description="Hash to verify (hex string, with or without 0x prefix)"),
):
    """Compare a provided content hash against the on-chain contentHash.

    This endpoint does not require an image upload.  It simply fetches the
    medicine's on-chain contentHash and compares it against the supplied hash.

    Useful when the client has already computed the embedding hash locally
    and only needs the on-chain verification step.
    """
    bridge = request.app.state.bridge
    if bridge is None:
        raise HTTPException(
            status_code=503,
            detail="Blockchain bridge is not available.",
        )

    try:
        # Normalise the provided hash.
        hash_hex = content_hash.lower().removeprefix("0x")
        hash_bytes = bytes.fromhex(hash_hex)

        # Pad to 32 bytes if needed.
        if len(hash_bytes) < 32:
            hash_bytes = hash_bytes.rjust(32, b"\x00")
        elif len(hash_bytes) > 32:
            raise HTTPException(status_code=400, detail="Hash must be at most 32 bytes (64 hex chars).")

        match = bridge.verify_content_hash(medicine_id, hash_bytes)

        # Also fetch the stored hash for the response.
        medicine = bridge.get_medicine(medicine_id)
        stored_hash = medicine.get("contentHash", "")
        on_chain_hex = f"0x{stored_hash}" if not stored_hash.startswith("0x") else stored_hash

        return HashVerificationResult(
            medicine_id=medicine_id,
            hash_provided=f"0x{hash_hex}",
            on_chain_match=match,
            on_chain_content_hash=on_chain_hex,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Hash verification failed for medicine %d: %s", medicine_id, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Hash verification failed: {exc}",
        )
