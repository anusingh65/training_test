"""
PillVerifier: CNN-based pill authenticity verification using EfficientNet-B0.

Architecture:
    Base: EfficientNet-B0 (pretrained on ImageNet)
    Strategy: Freeze all layers except last 2 blocks + custom classifier head
    Custom head: 1280 -> 512 -> 128 -> num_classes (2)
    Also exposes 128-dim embedding for on-chain fingerprinting and similarity search.

Input:  RGB PIL Image (resized internally to 224x224)
Output: dict with {confidence, prediction, embedding_hash, embedding}

Classification thresholds:
    confidence >= 0.85  -> "authentic"
    0.50 <= conf < 0.85 -> "suspicious"
    confidence < 0.50   -> "counterfeit"
"""

import sys
from pathlib import Path

# Ensure ai-engine root is on sys.path so `from config import ...` works
# regardless of how this module is invoked.
_AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))

import hashlib
from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from torchvision import models


class PillClassifierHead(nn.Module):
    """
    Custom classifier head that replaces EfficientNet's default classifier.

    Layers:
        Dropout(0.3) -> Linear(1280, 512) -> ReLU -> Dropout(0.2)
        -> Linear(512, 128) -> ReLU -> Linear(128, num_classes)

    The 128-dim activation (output of layer index 4, the second Linear)
    serves as the pill embedding used for similarity matching and
    blockchain fingerprinting.
    """

    def __init__(self, in_features: int = 1280, num_classes: int = 2):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Dropout(p=0.3),          # 0
            nn.Linear(in_features, 512), # 1
            nn.ReLU(inplace=True),       # 2
            nn.Dropout(p=0.2),           # 3
            nn.Linear(512, 128),         # 4
            nn.ReLU(inplace=True),       # 5
            nn.Linear(128, num_classes), # 6
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


class PillVerifier:
    """
    CNN-based pill verification using EfficientNet-B0 with transfer learning.

    Parameters
    ----------
    model_path : str or Path, optional
        Path to a saved state dict (.pth). If provided *and* the file exists,
        weights are loaded. Otherwise the model starts from ImageNet pre-trained
        weights (useful for inference in simulation / demo mode).
    num_classes : int
        Number of output classes (default 2: authentic / counterfeit).
    device : str or torch.device, optional
        Force a specific device. Auto-detected if ``None``.
    """

    # ------------------------------------------------------------------ #
    #  Thresholds                                                         #
    # ------------------------------------------------------------------ #
    AUTHENTIC_THRESHOLD = 0.85
    SUSPICIOUS_THRESHOLD = 0.50

    # ImageNet channel-wise stats used by torchvision pretrained models
    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]
    INPUT_SIZE = 224

    def __init__(
        self,
        model_path: Optional[str] = None,
        num_classes: int = 2,
        device: Optional[str] = None,
    ):
        # Resolve device ------------------------------------------------
        if device is not None:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.num_classes = num_classes
        self.transform = self._get_transforms()

        # Build the model (EfficientNet-B0 + custom head) ---------------
        self.model = self._build_model()

        # Optionally load trained weights --------------------------------
        if model_path is not None and Path(model_path).is_file():
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"[PillVerifier] Loaded weights from {model_path}")
        else:
            if model_path is not None:
                print(
                    f"[PillVerifier] Weights file not found at {model_path}. "
                    "Using ImageNet-pretrained backbone (untrained head)."
                )
            else:
                print("[PillVerifier] No model_path provided. Using ImageNet-pretrained backbone.")

        self.model.to(self.device)
        self.model.eval()

        # Placeholder filled by forward hook during `get_embedding`
        self._embedding_buffer: Optional[torch.Tensor] = None
        # Register forward hook on the 128-dim layer (layers[4] = Linear(512,128))
        self._hook_handle = self.model.classifier.layers[5].register_forward_hook(
            self._embedding_hook
        )

    # ------------------------------------------------------------------ #
    #  Transforms                                                         #
    # ------------------------------------------------------------------ #

    def _get_transforms(self) -> transforms.Compose:
        """
        Build the standard inference transform pipeline:
        Resize -> CenterCrop -> ToTensor -> Normalize.
        """
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=self.IMAGENET_MEAN, std=self.IMAGENET_STD),
        ])

    # ------------------------------------------------------------------ #
    #  Model construction                                                 #
    # ------------------------------------------------------------------ #

    def _build_model(self) -> models.EfficientNet:
        """
        Construct EfficientNet-B0 with custom classifier head.

        Freezing strategy:
            All named parameters are collected into a list. Every parameter
            *except* the last 20 is frozen (requires_grad = False). This
            keeps the last ~2 convolutional blocks and the full classifier
            trainable, while the early feature extractor stays fixed.
        """
        # Load pretrained EfficientNet-B0
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=weights)

        # Freeze early layers: keep last 20 parameters trainable ----------
        all_params = list(model.parameters())
        num_params = len(all_params)
        freeze_until = max(0, num_params - 20)

        for idx, param in enumerate(all_params):
            if idx < freeze_until:
                param.requires_grad = False

        # Replace the classifier with our custom head ----------------------
        in_features = model.classifier[1].in_features  # 1280 for B0
        model.classifier = PillClassifierHead(
            in_features=in_features,
            num_classes=self.num_classes,
        )

        return model

    # ------------------------------------------------------------------ #
    #  Forward hook for embedding extraction                              #
    # ------------------------------------------------------------------ #

    def _embedding_hook(
        self,
        module: nn.Module,
        input_tensor: Tuple[torch.Tensor, ...],
        output: torch.Tensor,
    ) -> None:
        """
        Forward hook attached to the ReLU *after* the 128-dim linear layer
        (layers[5]). Captures the 128-dimensional activation vector.
        """
        self._embedding_buffer = output.detach().cpu()

    # ------------------------------------------------------------------ #
    #  Embedding extraction                                               #
    # ------------------------------------------------------------------ #

    def get_embedding(self, image: Image.Image) -> np.ndarray:
        """
        Extract the 128-dimensional embedding vector for a pill image.

        Parameters
        ----------
        image : PIL.Image.Image
            An RGB pill photograph.

        Returns
        -------
        np.ndarray
            Shape ``(128,)`` float32 embedding.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            _ = self.model(tensor)

        # The hook has filled self._embedding_buffer
        embedding = self._embedding_buffer.squeeze(0).numpy().astype(np.float32)
        return embedding

    # ------------------------------------------------------------------ #
    #  Full verification pipeline                                         #
    # ------------------------------------------------------------------ #

    def verify(self, image: Image.Image) -> Dict:
        """
        Run full pill verification.

        Parameters
        ----------
        image : PIL.Image.Image
            An RGB pill photograph.

        Returns
        -------
        dict
            {
                "confidence": float,        # softmax probability of the predicted class
                "prediction": str,           # "authentic" | "suspicious" | "counterfeit"
                "embedding_hash": str,       # "0x" + SHA-256 hex of embedding bytes
                "embedding": np.ndarray,     # 128-dim float32 vector
            }
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = torch.softmax(logits, dim=1).squeeze(0)

        # Class 0 = authentic, Class 1 = counterfeit
        authentic_prob = probabilities[0].item()
        counterfeit_prob = probabilities[1].item()

        # The "confidence" is the authentic-class probability
        confidence = authentic_prob

        # Apply thresholds
        if confidence >= self.AUTHENTIC_THRESHOLD:
            prediction = "authentic"
        elif confidence >= self.SUSPICIOUS_THRESHOLD:
            prediction = "suspicious"
        else:
            prediction = "counterfeit"

        # Retrieve embedding that was captured by the hook during the forward pass
        embedding = self._embedding_buffer.squeeze(0).numpy().astype(np.float32)
        embedding_hash = self._hash_embedding(embedding)

        return {
            "confidence": round(confidence, 6),
            "prediction": prediction,
            "embedding_hash": embedding_hash,
            "embedding": embedding,
        }

    # ------------------------------------------------------------------ #
    #  Hashing                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hash_embedding(embedding: np.ndarray) -> str:
        """
        Compute a deterministic SHA-256 hash of the embedding vector.

        The embedding is cast to float32, its raw bytes are hashed, and the
        result is returned as ``"0x" + <64-char hex digest>``.
        """
        raw_bytes = embedding.astype(np.float32).tobytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        return f"0x{digest}"

    # ------------------------------------------------------------------ #
    #  Embedding comparison                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def compare_embeddings(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embedding vectors.

        Parameters
        ----------
        emb1, emb2 : np.ndarray
            1-D float arrays (typically shape ``(128,)``).

        Returns
        -------
        float
            Cosine similarity in [-1.0, 1.0].
        """
        emb1 = emb1.astype(np.float64).flatten()
        emb2 = emb2.astype(np.float64).flatten()

        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 < 1e-12 or norm2 < 1e-12:
            return 0.0

        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    # ------------------------------------------------------------------ #
    #  Cleanup                                                            #
    # ------------------------------------------------------------------ #

    def __del__(self):
        """Remove the forward hook to avoid memory leaks."""
        if hasattr(self, "_hook_handle") and self._hook_handle is not None:
            self._hook_handle.remove()

    def __repr__(self) -> str:
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        return (
            f"PillVerifier(device={self.device}, classes={self.num_classes}, "
            f"trainable_params={trainable:,}, total_params={total:,})"
        )
