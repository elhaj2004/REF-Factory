import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REFERENCE_LIBRARY_DIR = Path(os.getenv("REF_LIBRARY_DIR", DATA_DIR / "reference_library"))
if not REFERENCE_LIBRARY_DIR.is_absolute():
    REFERENCE_LIBRARY_DIR = PROJECT_ROOT / REFERENCE_LIBRARY_DIR
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
CHROMA_DIR = DATA_DIR / "chroma_db"
SIBLING_PRES_FACTORY_ENV = PROJECT_ROOT.parent / "Pres-Factory" / ".env"


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    if not (os.getenv("OPENAI_COMPAT_API_KEY") or os.getenv("DINOOTOO_API_KEY")):
        load_dotenv(SIBLING_PRES_FACTORY_ENV, override=False)


def ensure_runtime_dirs() -> None:
    for directory in (DATA_DIR, REFERENCE_LIBRARY_DIR, UPLOAD_DIR, OUTPUT_DIR, CHROMA_DIR):
        directory.mkdir(parents=True, exist_ok=True)


load_environment()
ensure_runtime_dirs()
