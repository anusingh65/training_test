import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = DATA_DIR / "models"
PILL_IMAGES_DIR = DATA_DIR / "pill_images"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

# Blockchain
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "")
LOCAL_RPC_URL = os.getenv("LOCAL_RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
CORE_CONTRACT_ADDRESS = os.getenv("CORE_CONTRACT_ADDRESS", "")
SCANNER_CONTRACT_ADDRESS = os.getenv("SCANNER_CONTRACT_ADDRESS", "")
BATCH_CONTRACT_ADDRESS = os.getenv("BATCH_CONTRACT_ADDRESS", "")

# AI Engine
AI_ENGINE_PORT = int(os.getenv("AI_ENGINE_PORT", "8000"))
PILL_MODEL_PATH = os.getenv("PILL_MODEL_PATH", str(MODEL_DIR / "pill_cnn.pth"))

# OpenFDA
OPENFDA_BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov")

# Mode
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

# Ensure directories exist
for d in [DATA_DIR, MODEL_DIR, PILL_IMAGES_DIR, SYNTHETIC_DIR]:
    d.mkdir(parents=True, exist_ok=True)
