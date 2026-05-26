import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FRANKFURTER_API = os.getenv("FRANKFURTER_API", "https://api.frankfurter.app")

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")

# Google Vision
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
USE_MOCK_OCR = os.getenv("USE_MOCK_OCR", "true").lower() == "true"

# Agent config
MAX_CLARIFICATION_ATTEMPTS = 3
MATCH_TOLERANCE_PERCENT = 0.005  # 0.5%

# Supported banks
SUPPORTED_BANKS = ["Maybank", "CIMB", "Public Bank", "RHB", "Hong Leong"]

# Print config on startup
def print_config():
    print("🔧 Configuration:")
    print(f"  - Firebase: {'✅' if os.path.exists(FIREBASE_SERVICE_ACCOUNT_PATH) else '❌'}")
    print(f"  - Google Vision: {'✅' if GOOGLE_APPLICATION_CREDENTIALS else '❌ (using mock)'}")
    print(f"  - Mock OCR: {'✅' if USE_MOCK_OCR else '❌'}")
    print(f"  - LLM: {'✅' if OPENAI_API_KEY else '❌ (deterministic mode)'}")
    print(f"  - Exports dir: {EXPORTS_DIR}")