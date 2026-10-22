"""
Image preprocessing utilities for the MediChain pill verification CNN.

Provides helpers for loading, normalizing, hashing, and augmenting pill
images before they are fed into the EfficientNet-based verification model.
"""

import hashlib
import io
from pathlib import Path
from typing import List, Union

import torch
from PIL import Image
from torchvision import transforms

# --------------------------------------------------------------------------- #
#  Constants                                                                   #
# --------------------------------------------------------------------------- #

# EfficientNet expects 224x224 inputs normalised with ImageNet statistics.
INPUT_SIZE: int = 224
IMAGENET_MEAN: List[float] = [0.485, 0.456, 0.406]
IMAGENET_STD: List[float] = [0.229, 0.224, 0.225]

# --------------------------------------------------------------------------- #
#  Reusable transform pipelines                                                #
# --------------------------------------------------------------------------- #

_inference_transform = transforms.Compose(
    [
        transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)

_training_augmentations = transforms.Compose(
    [
        transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
        transforms.RandomRotation(degrees=30),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.3,
            hue=0.1,
        ),
        transforms.RandomPerspective(distortion_scale=0.3, p=0.5),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)


# --------------------------------------------------------------------------- #
#  Internal helpers                                                            #
# --------------------------------------------------------------------------- #


def _load_image(image_bytes_or_path: Union[bytes, str, Path]) -> Image.Image:
    """Load an image from raw bytes or a filesystem path.

    Parameters
    ----------
    image_bytes_or_path:
        Either raw image bytes, a string file path, or a ``pathlib.Path``.

    Returns
    -------
    PIL.Image.Image
        The loaded image converted to RGB.

    Raises
    ------
    TypeError
        If the input is not bytes, str, or Path.
    FileNotFoundError
        If a path is provided but does not exist.
    """
    if isinstance(image_bytes_or_path, bytes):
        return Image.open(io.BytesIO(image_bytes_or_path)).convert("RGB")

    if isinstance(image_bytes_or_path, (str, Path)):
        path = Path(image_bytes_or_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        return Image.open(path).convert("RGB")

    raise TypeError(
        f"Expected bytes, str, or Path, got {type(image_bytes_or_path).__name__}"
    )


# --------------------------------------------------------------------------- #
#  Public API                                                                  #
# --------------------------------------------------------------------------- #


def preprocess_pill_image(
    image_bytes_or_path: Union[bytes, str, Path],
) -> torch.Tensor:
    """Load and preprocess a pill image for EfficientNet inference.

    The image is resized to 224x224, converted to a float tensor, and
    normalised using ImageNet channel-wise mean and standard deviation.
    A batch dimension is **not** added; the caller should use
    ``tensor.unsqueeze(0)`` when batching is needed.

    Parameters
    ----------
    image_bytes_or_path:
        Raw image bytes, a string file path, or a ``pathlib.Path``
        pointing to the pill photograph.

    Returns
    -------
    torch.Tensor
        A ``(3, 224, 224)`` float tensor ready for the model.
    """
    image = _load_image(image_bytes_or_path)
    return _inference_transform(image)


def compute_image_hash(image_bytes: bytes) -> str:
    """Compute the SHA-256 hex digest of raw image bytes.

    This hash can be stored on-chain or compared to verify that an image
    has not been tampered with since it was first registered.

    Parameters
    ----------
    image_bytes:
        The raw bytes of the image file (e.g. JPEG / PNG payload).

    Returns
    -------
    str
        A 64-character lowercase hexadecimal SHA-256 digest.

    Raises
    ------
    TypeError
        If *image_bytes* is not of type ``bytes``.
    """
    if not isinstance(image_bytes, bytes):
        raise TypeError(
            f"Expected bytes for hashing, got {type(image_bytes).__name__}"
        )
    return hashlib.sha256(image_bytes).hexdigest()


def augment_for_training(
    image: Union[Image.Image, bytes, str, Path],
    num_augmentations: int = 5,
) -> List[torch.Tensor]:
    """Generate multiple augmented versions of a pill image for training.

    Each call to the augmentation pipeline produces a stochastic variant
    of the input (random rotation, flip, colour jitter, and perspective
    distortion), so calling this function repeatedly will yield different
    results.

    Parameters
    ----------
    image:
        A ``PIL.Image.Image``, raw image bytes, a file-path string, or a
        ``pathlib.Path``.  If not already a PIL Image it will be loaded
        via :func:`_load_image`.
    num_augmentations:
        How many augmented tensors to produce.  Defaults to ``5``.

    Returns
    -------
    list[torch.Tensor]
        A list of ``(3, 224, 224)`` tensors, each a uniquely augmented
        version of the source image.
    """
    if not isinstance(image, Image.Image):
        image = _load_image(image)

    return [_training_augmentations(image.copy()) for _ in range(num_augmentations)]
