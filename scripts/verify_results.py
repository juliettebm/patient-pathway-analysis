"""Fail when canonical database results drift from the versioned snapshot."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import run_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=ROOT / "database" / "patient_journey.db")
    parser.add_argument("--reference", type=Path, default=ROOT / "results" / "reference_metrics.json")
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    with sqlite3.connect(args.database) as conn:
        actual = run_analysis(conn, as_of_date=reference["as_of_date"]).to_dict()
    failures = []
    for name, expected in reference["metrics"].items():
        observed = actual[name]
        tolerance = reference["absolute_tolerances"].get(name, 0.0)
        if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=tolerance):
            failures.append(f"{name}: expected {expected} ± {tolerance}, got {observed}")
    if failures:
        print("Result drift detected:\n- " + "\n- ".join(failures))
        return 1
    print("Canonical results match the versioned snapshot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
