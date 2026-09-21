"""CLI entry point: python scripts/build_database.py."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import build_database

if __name__ == "__main__":
    path = build_database(ROOT / "data" / "raw", ROOT / "database" / "patient_journey.db")
    print(f"Built {path}")
