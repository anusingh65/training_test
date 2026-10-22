"""
Training script for PillVerifier CNN.

Usage (from ai-engine/ directory):
    python -m models.train_pill_cnn
    python -m models.train_pill_cnn --epochs 20 --batch_size 16
    python -m models.train_pill_cnn --demo_mode
    python -m models.train_pill_cnn --demo_mode --epochs 5

Flags:
    --data_dir   Root of the pill image dataset (default: data/pill_images)
    --epochs     Maximum training epochs (default: 15)
    --batch_size Batch size for DataLoader (default: 32)
    --lr         Initial learning rate (default: 1e-4)
    --patience   Early-stopping patience on val loss (default: 5)
    --demo_mode  When set, synthesizes a small dataset suitable for a demo:
                 - Downloads ~100 pill images from the NLM RxImage API
                 - Creates a counterfeit split via aggressive augmentation
                   (Gaussian blur, colour shift, additive noise)
                 - Splits 80/20 into train / val

Expected real-data directory layout:
    data/pill_images/
        train/
            authentic/
            counterfeit/
        val/
            authentic/
            counterfeit/

Outputs:
    Best model checkpoint: data/models/pill_cnn.pth

Training recipe:
    Optimizer: Adam (lr=1e-4)
    Scheduler: ReduceLROnPlateau (factor=0.5, patience=2, min_lr=1e-6)
    Loss: CrossEntropyLoss
    Augmentation: RandomHorizontalFlip, RandomRotation(30),
                  ColorJitter, RandomAffine
    Early stopping on validation loss with configurable patience.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sure `from config import ...` and `from models.pill_verifier import ...`
# resolve correctly no matter how this script is launched.
# ---------------------------------------------------------------------------
_AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))

import argparse
import io
import json
import math
import os
import random
import shutil
import time
import urllib.request
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from PIL import Image, ImageFilter
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets

from config import MODEL_DIR, PILL_IMAGES_DIR
from models.pill_verifier import PillVerifier

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ========================================================================== #
#  Demo dataset builder                                                       #
# ========================================================================== #

def _fetch_pill_image(url: str, timeout: int = 15) -> Image.Image:
    """Download a single image from *url* and return as PIL RGB Image."""
    req = urllib.request.Request(url, headers={"User-Agent": "MediChain/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return img


def _get_rximage_urls(limit: int = 100) -> List[str]:
    """
    Query the NLM RxImage REST API for pill thumbnail URLs.

    The API returns JSON with an ``nlmRxImages`` array; each element has
    an ``imageUrl`` field.  We ask for *limit* results and return whatever
    the server gives us.

    If the API call fails (network down, rate-limited, etc.) we fall back
    to generating purely synthetic coloured pill images so that the demo
    can still run offline.
    """
    api_url = (
        f"https://rximage.nlm.nih.gov/api/rximage/1/rxnav?"
        f"resolution=120&rLimit={limit}"
    )
    urls: List[str] = []
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "MediChain/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
        for entry in body.get("nlmRxImages", []):
            img_url = entry.get("imageUrl")
            if img_url:
                urls.append(img_url)
    except Exception as exc:
        print(f"[demo] RxImage API request failed ({exc}). Will generate synthetic pills.")
    return urls[:limit]


def _generate_synthetic_pill(size: int = 224) -> Image.Image:
    """
    Create a simple synthetic pill image: coloured ellipse on a white
    background.  Used as fallback when the RxImage API is unreachable.
    """
    from PIL import ImageDraw

    img = Image.new("RGB", (size, size), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    # Random pastel colour for the pill body
    r = random.randint(120, 240)
    g = random.randint(120, 240)
    b = random.randint(120, 240)
    margin = size // 6
    # Draw pill shape (ellipse)
    bbox = [margin, margin + size // 6, size - margin, size - margin - size // 6]
    draw.ellipse(bbox, fill=(r, g, b), outline=(r - 40, g - 40, b - 40), width=2)
    # Optionally draw a score line
    if random.random() > 0.5:
        mid_y = size // 2
        draw.line([(margin + 10, mid_y), (size - margin - 10, mid_y)],
                  fill=(r - 60, g - 60, b - 60), width=1)
    return img


def _make_counterfeit(image: Image.Image) -> Image.Image:
    """
    Apply aggressive augmentation to an *authentic* image to simulate a
    counterfeit pill.  One or more of the following are applied at random:

    - Gaussian blur (radius 2-4)
    - Colour channel shift (swap or tint channels)
    - Additive Gaussian noise
    - Brightness / contrast distortion
    """
    img = image.copy()
    arr = np.array(img, dtype=np.float32)

    # Always apply blur
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(2.0, 4.0)))
    arr = np.array(img, dtype=np.float32)

    # Colour shift: randomly tint a channel
    channel = random.randint(0, 2)
    shift = random.uniform(30, 80) * random.choice([-1, 1])
    arr[:, :, channel] = np.clip(arr[:, :, channel] + shift, 0, 255)

    # Additive noise
    noise = np.random.normal(0, random.uniform(15, 35), arr.shape).astype(np.float32)
    arr = np.clip(arr + noise, 0, 255)

    # Brightness distortion
    factor = random.uniform(0.6, 0.85)
    arr = np.clip(arr * factor, 0, 255)

    return Image.fromarray(arr.astype(np.uint8))


def build_demo_dataset(root: Path, target_count: int = 100) -> None:
    """
    Build a small demo dataset under *root* with train/val splits.

    Steps:
        1. Attempt to download pill images via RxImage API.
        2. If fewer than 20 images obtained, fill up with synthetic pills.
        3. For each authentic image create a counterfeit variant.
        4. Split 80 / 20 into train / val directories.
    """
    print(f"[demo] Building demo dataset at {root} ...")
    root = Path(root)

    # Temporary staging directory
    staging = root / "_staging"
    staging.mkdir(parents=True, exist_ok=True)

    # ---- Step 1 & 2: Collect authentic images ----------------------------
    urls = _get_rximage_urls(limit=target_count)
    authentic_images: List[Image.Image] = []

    for idx, url in enumerate(urls):
        try:
            img = _fetch_pill_image(url)
            img = img.resize((224, 224), Image.LANCZOS)
            authentic_images.append(img)
            if (idx + 1) % 20 == 0 or idx == len(urls) - 1:
                print(f"  Downloaded {idx + 1}/{len(urls)} images")
        except Exception:
            continue  # skip broken URLs silently

    # Fill with synthetic if not enough
    shortfall = max(0, 30 - len(authentic_images))
    if shortfall > 0:
        print(f"  Generating {shortfall} synthetic pill images as supplement ...")
        for _ in range(shortfall):
            authentic_images.append(_generate_synthetic_pill())

    # Also pad up to at least target_count // 2 with synthetic
    while len(authentic_images) < target_count // 2:
        authentic_images.append(_generate_synthetic_pill())

    total = len(authentic_images)
    print(f"  Total authentic images collected: {total}")

    # ---- Step 3: Generate counterfeits -----------------------------------
    counterfeit_images: List[Image.Image] = []
    for img in authentic_images:
        counterfeit_images.append(_make_counterfeit(img))

    # ---- Step 4: Split 80 / 20 ------------------------------------------
    indices = list(range(total))
    random.shuffle(indices)
    split = int(0.8 * total)
    train_idx = indices[:split]
    val_idx = indices[split:]

    for split_name, idx_list in [("train", train_idx), ("val", val_idx)]:
        for cls_name, img_list in [("authentic", authentic_images),
                                   ("counterfeit", counterfeit_images)]:
            out_dir = root / split_name / cls_name
            out_dir.mkdir(parents=True, exist_ok=True)
            for i, idx in enumerate(idx_list):
                fname = out_dir / f"{cls_name}_{i:04d}.png"
                img_list[idx].save(fname)

    # Clean up staging
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)

    train_auth = len(list((root / "train" / "authentic").glob("*.png")))
    train_fake = len(list((root / "train" / "counterfeit").glob("*.png")))
    val_auth = len(list((root / "val" / "authentic").glob("*.png")))
    val_fake = len(list((root / "val" / "counterfeit").glob("*.png")))
    print(
        f"  Dataset ready: train=({train_auth} auth, {train_fake} fake) "
        f"val=({val_auth} auth, {val_fake} fake)"
    )


# ========================================================================== #
#  Augmented training transforms                                              #
# ========================================================================== #

def get_train_transforms() -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=30),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])


def get_val_transforms() -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])


# ========================================================================== #
#  Training loop                                                              #
# ========================================================================== #

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
) -> Tuple[float, float]:
    """Train for one epoch, returning (average_loss, accuracy)."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

        if (batch_idx + 1) % max(1, len(loader) // 5) == 0:
            print(
                f"    Epoch {epoch} [{batch_idx+1}/{len(loader)}]  "
                f"loss={loss.item():.4f}"
            )

    avg_loss = running_loss / max(total, 1)
    accuracy = correct / max(total, 1)
    return avg_loss, accuracy


@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    """Evaluate on the validation set, returning (average_loss, accuracy)."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    avg_loss = running_loss / max(total, 1)
    accuracy = correct / max(total, 1)
    return avg_loss, accuracy


def run_training(
    data_dir: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    patience: int,
    save_path: Path,
) -> None:
    """
    Full training pipeline.

    1. Build DataLoaders from ``data_dir/train`` and ``data_dir/val``.
    2. Instantiate :class:`PillVerifier` (no pre-existing weights).
    3. Train with Adam + ReduceLROnPlateau + early stopping.
    4. Save the best model to *save_path*.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'=' * 60}")
    print(f"  PillVerifier Training")
    print(f"  Device:      {device}")
    print(f"  Data dir:    {data_dir}")
    print(f"  Epochs:      {epochs}")
    print(f"  Batch size:  {batch_size}")
    print(f"  LR:          {lr}")
    print(f"  Patience:    {patience}")
    print(f"  Save path:   {save_path}")
    print(f"{'=' * 60}\n")

    # ------------------------------------------------------------------
    # Datasets & Loaders
    # ------------------------------------------------------------------
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(
            f"Expected train/ and val/ directories under {data_dir}. "
            "Run with --demo_mode to auto-generate a demo dataset."
        )

    train_dataset = datasets.ImageFolder(root=str(train_dir), transform=get_train_transforms())
    val_dataset = datasets.ImageFolder(root=str(val_dir), transform=get_val_transforms())

    num_workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        drop_last=False,
    )

    class_names = train_dataset.classes  # alphabetical: ['authentic', 'counterfeit']
    print(f"  Classes:      {class_names}")
    print(f"  Train size:   {len(train_dataset)}")
    print(f"  Val size:     {len(val_dataset)}\n")

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    verifier = PillVerifier(model_path=None, num_classes=len(class_names), device=str(device))
    model = verifier.model
    model.train()
    print(f"  {verifier}\n")

    # ------------------------------------------------------------------
    # Optimiser, scheduler, loss
    # ------------------------------------------------------------------
    # Only optimise parameters that require grad
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.Adam(trainable_params, lr=lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2, min_lr=1e-6, verbose=True,
    )
    criterion = nn.CrossEntropyLoss()

    # ------------------------------------------------------------------
    # Training loop with early stopping
    # ------------------------------------------------------------------
    best_val_loss = math.inf
    epochs_no_improve = 0
    best_state = None
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    for epoch in range(1, epochs + 1):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step(val_loss)
        elapsed = time.time() - t0

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"  Epoch {epoch:3d}/{epochs}  "
            f"train_loss={train_loss:.4f}  train_acc={train_acc:.4f}  "
            f"val_loss={val_loss:.4f}  val_acc={val_acc:.4f}  "
            f"lr={current_lr:.2e}  "
            f"time={elapsed:.1f}s"
        )

        # Check improvement
        if val_loss < best_val_loss - 1e-6:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
            print(f"    ** New best val_loss={val_loss:.4f} (saving checkpoint)")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"\n  Early stopping triggered (no improvement for {patience} epochs).")
                break

    # ------------------------------------------------------------------
    # Save best model
    # ------------------------------------------------------------------
    if best_state is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(best_state, str(save_path))
        print(f"\n  Best model saved to {save_path}")
        print(f"  Best val_loss = {best_val_loss:.4f}")
    else:
        print("\n  WARNING: No best state captured (training may have been trivial).")

    # ------------------------------------------------------------------
    # Quick verification sanity check
    # ------------------------------------------------------------------
    print("\n  Running post-training sanity check ...")
    verifier_check = PillVerifier(
        model_path=str(save_path) if save_path.exists() else None,
        num_classes=len(class_names),
        device=str(device),
    )
    # Grab one image from the val set for a test prediction
    sample_img_path = None
    for cls_dir in val_dir.iterdir():
        if cls_dir.is_dir():
            for img_file in cls_dir.iterdir():
                if img_file.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    sample_img_path = img_file
                    break
        if sample_img_path:
            break

    if sample_img_path:
        sample_img = Image.open(sample_img_path).convert("RGB")
        result = verifier_check.verify(sample_img)
        print(f"    Sample: {sample_img_path.name}")
        print(f"    Prediction:     {result['prediction']}")
        print(f"    Confidence:     {result['confidence']:.4f}")
        print(f"    Embedding hash: {result['embedding_hash'][:18]}...")
        print(f"    Embedding dim:  {result['embedding'].shape}")
    else:
        print("    No sample image found for sanity check.")

    print(f"\n{'=' * 60}")
    print("  Training complete.")
    print(f"{'=' * 60}\n")


# ========================================================================== #
#  CLI entry point                                                            #
# ========================================================================== #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the PillVerifier CNN (EfficientNet-B0 based).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=str(PILL_IMAGES_DIR),
        help="Root directory containing train/ and val/ subdirectories.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=15,
        help="Maximum number of training epochs.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for training and validation.",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Initial learning rate for Adam optimiser.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=5,
        help="Early-stopping patience (epochs without val loss improvement).",
    )
    parser.add_argument(
        "--demo_mode",
        action="store_true",
        help=(
            "Build a small demo dataset automatically. Downloads pill images "
            "from RxImage API and generates counterfeit versions via augmentation."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    save_path = MODEL_DIR / "pill_cnn.pth"

    if args.demo_mode:
        # Check if dataset already exists and has content
        train_dir = data_dir / "train"
        if train_dir.exists() and any(train_dir.rglob("*.png")):
            print("[demo] Demo dataset already exists. Skipping generation.")
        else:
            build_demo_dataset(root=data_dir, target_count=100)

    run_training(
        data_dir=data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
        save_path=save_path,
    )


if __name__ == "__main__":
    main()
