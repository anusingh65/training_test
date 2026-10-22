"""
Real-data acquisition pipeline for MediChain AI Engine.

REAL DATA FIRST philosophy: always prefer publicly available, authoritative
pharmaceutical datasets over synthetic data.  Synthetic generators in
``data.synthetic`` exist only as a fallback when real data cannot be obtained
(e.g. no internet, API quota exceeded, CI environments).

Downloaders
-----------
* **C3PI**          -- NLM Computational Photography Project for Pill
                       Identification sample images (493 MB zip).
* **RxImage**       -- Individual pill images fetched via the NLM RxImage
                       REST API, filtered by colour.
* **OpenFDA**       -- Adverse-event reports for a given drug queried from
                       the openFDA Drug Event endpoint.
* **Training split**-- Organises downloaded pill images into a train / val
                       directory tree suitable for ``torchvision.datasets.ImageFolder``,
                       and synthesises a *counterfeit* class via image
                       augmentations (blur, colour shift, noise).

Usage
-----
    python -m data.download_real_data              # download everything
    python -m data.download_real_data --c3pi        # C3PI sample only
    python -m data.download_real_data --rximage 200 # 200 RxImage images
    python -m data.download_real_data --openfda metformin
    python -m data.download_real_data --split       # organise into train/val
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from PIL import Image, ImageFilter

# ---------------------------------------------------------------------------
#  Resolve config -- works whether you run as ``python -m data.download_real_data``
#  from ai-engine/ or directly with ``python data/download_real_data.py``.
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_AI_ENGINE_DIR = _THIS_DIR.parent

if str(_AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_DIR))

from config import (
    DATA_DIR,
    OPENFDA_BASE_URL,
    PILL_IMAGES_DIR,
)

# ---------------------------------------------------------------------------
#  Derived paths
# ---------------------------------------------------------------------------
C3PI_DIR = PILL_IMAGES_DIR / "c3pi"
RXIMAGE_DIR = PILL_IMAGES_DIR / "rximage"
ADVERSE_EVENTS_DIR = DATA_DIR / "adverse_events"
TRAIN_DIR = PILL_IMAGES_DIR / "train"
VAL_DIR = PILL_IMAGES_DIR / "val"

for _d in [C3PI_DIR, RXIMAGE_DIR, ADVERSE_EVENTS_DIR, TRAIN_DIR, VAL_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------
C3PI_SAMPLE_URL = "https://data.lhncbc.nlm.nih.gov/public/Pills/sampleData.zip"
RXIMAGE_API_BASE = "https://rximage.nlm.nih.gov/api/rximage/1/rxnav"

PILL_COLORS = [
    "blue", "brown", "gray", "green", "orange",
    "pink", "purple", "red", "white", "yellow",
]

# Supported image extensions when scanning directories for pill images.
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"}


# ========================================================================== #
#  1.  C3PI Sample Download                                                  #
# ========================================================================== #


def download_c3pi_sample() -> Path:
    """Download the NLM C3PI sample dataset (~493 MB) and extract it.

    The zip file is streamed in chunks to ``data/pill_images/c3pi/``.
    If the zip has already been downloaded and extracted, the function
    returns early.

    Returns
    -------
    Path
        The directory containing the extracted pill images.
    """
    zip_path = C3PI_DIR / "sampleData.zip"
    marker = C3PI_DIR / ".download_complete"

    if marker.exists():
        print(f"[C3PI] Already downloaded and extracted at {C3PI_DIR}")
        return C3PI_DIR

    print(f"[C3PI] Downloading sample data from {C3PI_SAMPLE_URL}")
    print("[C3PI] This is approximately 493 MB -- please be patient.")

    try:
        resp = requests.get(C3PI_SAMPLE_URL, stream=True, timeout=600)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[C3PI] ERROR: Failed to download -- {exc}")
        return C3PI_DIR

    total_bytes = int(resp.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 1024 * 256  # 256 KB

    with open(zip_path, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            fh.write(chunk)
            downloaded += len(chunk)
            if total_bytes:
                pct = downloaded / total_bytes * 100
                print(f"\r[C3PI] {downloaded / 1e6:.1f} / {total_bytes / 1e6:.1f} MB ({pct:.1f}%)", end="", flush=True)
            else:
                print(f"\r[C3PI] {downloaded / 1e6:.1f} MB downloaded", end="", flush=True)

    print()  # newline after progress bar

    # Extract -----------------------------------------------------------------
    print(f"[C3PI] Extracting to {C3PI_DIR} ...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(C3PI_DIR)
        marker.touch()
        print(f"[C3PI] Extraction complete. {len(list(C3PI_DIR.rglob('*')))} entries.")
    except zipfile.BadZipFile as exc:
        print(f"[C3PI] ERROR: Corrupt zip file -- {exc}")
    finally:
        # Remove zip to save space (images are what matter).
        if zip_path.exists():
            zip_path.unlink()
            print("[C3PI] Removed zip archive to save disk space.")

    return C3PI_DIR


# ========================================================================== #
#  2.  RxImage API Downloader                                                #
# ========================================================================== #


def _fetch_rximage_page(color: str, page: int = 1) -> Optional[Dict[str, Any]]:
    """Fetch a single page of pill results from the RxImage API.

    Returns the parsed JSON response or ``None`` on failure.
    """
    params = {
        "color": color,
        "imageType": "pill",
        "imageSize": "1",  # full-resolution
        "page": page,
    }
    try:
        resp = requests.get(RXIMAGE_API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        print(f"  [RxImage] WARNING: request failed for color={color}, page={page} -- {exc}")
        return None


def download_rximage_api(max_images: int = 500) -> Path:
    """Download pill images from the NLM RxImage REST API.

    Iterates over the ten standard pill colours, fetching pages of results
    until *max_images* images have been saved.  Images are written into
    ``data/pill_images/rximage/`` and a companion ``metadata.csv`` captures
    the NDC code, RxCUI, colour, shape, imprint, and local filename for
    every image.

    A polite 1-request-per-second rate limit is enforced.

    Parameters
    ----------
    max_images:
        Upper bound on the total number of images to download across all
        colours.  Defaults to 500.

    Returns
    -------
    Path
        The directory containing the downloaded images and metadata CSV.
    """
    csv_path = RXIMAGE_DIR / "metadata.csv"
    images_saved = 0

    # If we already have enough images, skip.
    existing_images = [
        f for f in RXIMAGE_DIR.iterdir()
        if f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if len(existing_images) >= max_images:
        print(f"[RxImage] Already have {len(existing_images)} images in {RXIMAGE_DIR} -- skipping.")
        return RXIMAGE_DIR

    print(f"[RxImage] Downloading up to {max_images} pill images from RxImage API ...")

    csv_fh = open(csv_path, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_fh, fieldnames=[
        "filename", "rxcui", "ndc", "color", "shape", "imprint", "name", "source_url",
    ])
    writer.writeheader()

    per_color = max(1, max_images // len(PILL_COLORS))

    for color in PILL_COLORS:
        if images_saved >= max_images:
            break

        color_count = 0
        page = 1

        while color_count < per_color and images_saved < max_images:
            data = _fetch_rximage_page(color, page)
            time.sleep(1)  # rate-limit: 1 req / sec

            if data is None:
                break

            nlm_rximages = data.get("nlmRxImages", [])
            if not nlm_rximages:
                break

            for item in nlm_rximages:
                if images_saved >= max_images or color_count >= per_color:
                    break

                img_url = item.get("imageUrl")
                if not img_url:
                    continue

                # Build a safe filename.
                ndc = item.get("ndc11", "unknown")
                rxcui = item.get("rxcui", "unknown")
                fname = f"{color}_{rxcui}_{ndc}_{images_saved:04d}.jpg"
                dest = RXIMAGE_DIR / fname

                try:
                    img_resp = requests.get(img_url, timeout=30)
                    img_resp.raise_for_status()
                    with open(dest, "wb") as f:
                        f.write(img_resp.content)
                except requests.RequestException as exc:
                    print(f"  [RxImage] WARNING: Could not download {img_url} -- {exc}")
                    time.sleep(1)
                    continue

                writer.writerow({
                    "filename": fname,
                    "rxcui": rxcui,
                    "ndc": ndc,
                    "color": color,
                    "shape": item.get("shape", ""),
                    "imprint": item.get("imprint", ""),
                    "name": item.get("name", ""),
                    "source_url": img_url,
                })

                images_saved += 1
                color_count += 1
                time.sleep(1)  # rate-limit

                if images_saved % 25 == 0:
                    print(f"  [RxImage] {images_saved} / {max_images} images saved ...")

            page += 1

    csv_fh.close()
    print(f"[RxImage] Done. {images_saved} images saved to {RXIMAGE_DIR}")
    print(f"[RxImage] Metadata written to {csv_path}")
    return RXIMAGE_DIR


# ========================================================================== #
#  3.  OpenFDA Adverse Events                                                #
# ========================================================================== #


def download_openfda_adverse_events(
    drug_name: str = "metformin",
    days_back: int = 365,
) -> Path:
    """Query the openFDA Drug Adverse Event endpoint for a given drug.

    Fetches up to 1 000 records (the API maximum per request) for the
    specified drug over the past *days_back* days and persists the raw
    JSON response to ``data/adverse_events/<drug_name>.json``.

    Parameters
    ----------
    drug_name:
        Generic drug name to search.  Defaults to ``"metformin"``.
    days_back:
        How far back in time to look (calendar days).  Defaults to 365.

    Returns
    -------
    Path
        Path to the saved JSON file.
    """
    from datetime import datetime, timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    date_range = f"[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"

    url = (
        f"{OPENFDA_BASE_URL}/drug/event.json"
        f"?search=patient.drug.openfda.generic_name:\"{drug_name}\""
        f"+AND+receivedate:{date_range}"
        f"&limit=1000"
    )

    out_path = ADVERSE_EVENTS_DIR / f"{drug_name.lower().replace(' ', '_')}.json"

    print(f"[OpenFDA] Querying adverse events for '{drug_name}' over last {days_back} days ...")
    print(f"[OpenFDA] URL: {url}")

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        print(f"[OpenFDA] ERROR: Request failed -- {exc}")
        # Write a stub so downstream code does not crash on missing file.
        payload = {
            "error": str(exc),
            "meta": {"drug_name": drug_name, "days_back": days_back},
            "results": [],
        }

    n_results = len(payload.get("results", []))
    print(f"[OpenFDA] Received {n_results} adverse-event records.")

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"[OpenFDA] Saved to {out_path}")
    return out_path


# ========================================================================== #
#  4.  Training Split Organisation                                           #
# ========================================================================== #


def _collect_pill_images() -> List[Path]:
    """Recursively collect all image files under ``PILL_IMAGES_DIR``.

    Excludes the ``train/`` and ``val/`` subtrees to avoid double-counting.
    """
    images: List[Path] = []
    exclude_prefixes = (str(TRAIN_DIR), str(VAL_DIR))

    for root, _dirs, files in os.walk(PILL_IMAGES_DIR):
        if any(root.startswith(ep) for ep in exclude_prefixes):
            continue
        for fname in files:
            if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                images.append(Path(root) / fname)

    return images


def _create_counterfeit_variant(src: Path, dest: Path) -> None:
    """Apply destructive augmentations to simulate a counterfeit pill image.

    Applies a random combination of Gaussian blur, colour shift, and
    additive Gaussian noise to make the output look like a low-quality
    counterfeit reproduction.

    Parameters
    ----------
    src:
        Source authentic pill image path.
    dest:
        Destination path for the generated counterfeit variant.
    """
    try:
        img = Image.open(src).convert("RGB")
    except Exception as exc:
        print(f"  [Split] WARNING: cannot open {src} -- {exc}")
        return

    # 1. Gaussian blur (always applied, varying radius)
    blur_radius = random.uniform(1.5, 4.0)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 2. Colour shift  (70 % chance)
    if random.random() < 0.7:
        arr = np.array(img, dtype=np.float32)
        shift = np.random.uniform(-30, 30, size=(1, 1, 3)).astype(np.float32)
        arr = np.clip(arr + shift, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    # 3. Additive Gaussian noise  (60 % chance)
    if random.random() < 0.6:
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, random.uniform(10, 30), arr.shape).astype(np.float32)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    # 4. Slight resize to mimic wrong tablet dimensions (40 % chance)
    if random.random() < 0.4:
        w, h = img.size
        scale = random.uniform(0.85, 0.95)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.BILINEAR)
        # Paste onto a canvas of original size to keep dimensions consistent.
        canvas = Image.new("RGB", (w, h), (245, 245, 245))
        offset_x = (w - new_w) // 2
        offset_y = (h - new_h) // 2
        canvas.paste(img, (offset_x, offset_y))
        img = canvas

    img.save(dest, quality=75)


def setup_pill_dataset_for_training(
    val_fraction: float = 0.15,
    counterfeit_ratio: float = 1.0,
) -> Path:
    """Organise downloaded pill images into a train/val directory tree.

    Creates the following layout::

        data/pill_images/
            train/
                authentic/
                counterfeit/
            val/
                authentic/
                counterfeit/

    *Authentic* images are the real pill photographs collected by earlier
    downloaders.  *Counterfeit* images are generated by applying
    destructive augmentations (blur, colour shift, noise) to a subset of
    authentic images.

    Parameters
    ----------
    val_fraction:
        Fraction of images reserved for validation.  Defaults to 0.15.
    counterfeit_ratio:
        Number of counterfeit images to generate per authentic image.
        Defaults to ``1.0`` (equal split).

    Returns
    -------
    Path
        ``PILL_IMAGES_DIR`` containing the ``train/`` and ``val/`` subtrees.
    """
    images = _collect_pill_images()

    if not images:
        print("[Split] No pill images found. Run --c3pi or --rximage first.")
        return PILL_IMAGES_DIR

    print(f"[Split] Found {len(images)} pill images. Organising train/val split ...")

    random.shuffle(images)
    split_idx = max(1, int(len(images) * (1.0 - val_fraction)))
    train_images = images[:split_idx]
    val_images = images[split_idx:]

    # Create subdirectories.
    for split_dir in [TRAIN_DIR, VAL_DIR]:
        for cls in ["authentic", "counterfeit"]:
            (split_dir / cls).mkdir(parents=True, exist_ok=True)

    def _populate_split(split_name: str, split_dir: Path, img_list: List[Path]) -> None:
        auth_dir = split_dir / "authentic"
        fake_dir = split_dir / "counterfeit"

        for idx, src in enumerate(img_list):
            # Copy authentic.
            dst_name = f"{idx:05d}{src.suffix.lower()}"
            auth_dst = auth_dir / dst_name
            shutil.copy2(src, auth_dst)

            # Generate counterfeit variant(s).
            n_fakes = max(1, int(counterfeit_ratio))
            for k in range(n_fakes):
                fake_name = f"{idx:05d}_fake{k}{src.suffix.lower()}"
                fake_dst = fake_dir / fake_name
                _create_counterfeit_variant(src, fake_dst)

            if (idx + 1) % 100 == 0:
                print(f"  [{split_name}] processed {idx + 1} / {len(img_list)} images")

    _populate_split("train", TRAIN_DIR, train_images)
    _populate_split("val", VAL_DIR, val_images)

    # Summary.
    train_auth = len(list((TRAIN_DIR / "authentic").iterdir()))
    train_fake = len(list((TRAIN_DIR / "counterfeit").iterdir()))
    val_auth = len(list((VAL_DIR / "authentic").iterdir()))
    val_fake = len(list((VAL_DIR / "counterfeit").iterdir()))

    print("[Split] Dataset summary:")
    print(f"  Train  -- authentic: {train_auth}, counterfeit: {train_fake}")
    print(f"  Val    -- authentic: {val_auth}, counterfeit: {val_fake}")
    print(f"[Split] Ready at {PILL_IMAGES_DIR}")

    return PILL_IMAGES_DIR


# ========================================================================== #
#  5.  Orchestrator                                                          #
# ========================================================================== #


def download_all(
    max_rximage: int = 500,
    openfda_drug: str = "metformin",
    openfda_days: int = 365,
) -> None:
    """Run every downloader in sequence and prepare the training split."""
    print("=" * 72)
    print("  MediChain -- Real Data Acquisition Pipeline")
    print("=" * 72)

    print("\n--- Step 1 / 4 : C3PI Sample ---")
    download_c3pi_sample()

    print("\n--- Step 2 / 4 : RxImage API ---")
    download_rximage_api(max_images=max_rximage)

    print("\n--- Step 3 / 4 : OpenFDA Adverse Events ---")
    download_openfda_adverse_events(drug_name=openfda_drug, days_back=openfda_days)

    print("\n--- Step 4 / 4 : Training Split ---")
    setup_pill_dataset_for_training()

    print("\n" + "=" * 72)
    print("  All downloads complete.")
    print("=" * 72)


# ========================================================================== #
#  CLI entry point                                                           #
# ========================================================================== #


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MediChain real-data acquisition pipeline.",
    )
    p.add_argument(
        "--all", action="store_true", default=False,
        help="Run every downloader (default when no flags are given).",
    )
    p.add_argument(
        "--c3pi", action="store_true", default=False,
        help="Download NLM C3PI sample data (493 MB).",
    )
    p.add_argument(
        "--rximage", type=int, nargs="?", const=500, default=None,
        metavar="N",
        help="Download N pill images from RxImage API (default 500).",
    )
    p.add_argument(
        "--openfda", type=str, nargs="?", const="metformin", default=None,
        metavar="DRUG",
        help="Download OpenFDA adverse events for DRUG (default metformin).",
    )
    p.add_argument(
        "--openfda-days", type=int, default=365,
        help="Look-back period in days for OpenFDA query (default 365).",
    )
    p.add_argument(
        "--split", action="store_true", default=False,
        help="Organise pill images into train/val splits.",
    )
    return p


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()

    # If no specific flag was provided, run everything.
    any_selected = args.c3pi or args.rximage is not None or args.openfda is not None or args.split
    if args.all or not any_selected:
        download_all(
            max_rximage=args.rximage or 500,
            openfda_drug=args.openfda or "metformin",
            openfda_days=args.openfda_days,
        )
    else:
        if args.c3pi:
            download_c3pi_sample()
        if args.rximage is not None:
            download_rximage_api(max_images=args.rximage)
        if args.openfda is not None:
            download_openfda_adverse_events(drug_name=args.openfda, days_back=args.openfda_days)
        if args.split:
            setup_pill_dataset_for_training()

    print("\nDone.")
