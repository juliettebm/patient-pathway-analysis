"""Reproducible Synthea CSV -> SQLite ingestion pipeline.

Synthea is the data generator.  This module validates its CSV contract and
loads the subset used by the project without silently dropping SQL constraints.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pandas as pd


OBESITY_CONDITION = "Body mass index 30+ - obesity (finding)"

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    birth_date TEXT NOT NULL,
    city TEXT,
    deceased INTEGER NOT NULL CHECK (deceased IN (0, 1)),
    death_date TEXT
);
CREATE TABLE encounters (
    encounter_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    encounter_date TEXT,
    encounter_type TEXT
);
CREATE TABLE conditions (
    condition_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    condition_name TEXT NOT NULL,
    start_date TEXT
);
CREATE TABLE procedures (
    procedure_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    procedure_name TEXT NOT NULL,
    procedure_date TEXT
);
"""

REQUIRED_COLUMNS = {
    "patients": {"id", "gender", "birthdate", "city", "deathdate"},
    "encounters": {"id", "patient", "start", "encounterclass"},
    "conditions": {"code", "patient", "description", "start"},
    "procedures": {"start", "patient", "encounter", "description"},
}


def _read_csv(raw_dir: Path, table: str) -> pd.DataFrame:
    frame = pd.read_csv(raw_dir / f"{table}.csv", dtype=str)
    frame.columns = frame.columns.str.strip().str.lower()
    missing = REQUIRED_COLUMNS[table] - set(frame.columns)
    if missing:
        raise ValueError(f"{table}.csv missing columns: {', '.join(sorted(missing))}")
    return frame


def _stable_ids(frame: pd.DataFrame, columns: list[str], prefix: str) -> pd.Series:
    def digest(row: pd.Series) -> str:
        value = "|".join("" if pd.isna(row[c]) else str(row[c]) for c in columns)
        return f"{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:20]}"

    base = frame.apply(digest, axis=1)
    occurrence = base.groupby(base).cumcount().astype(str)
    return base + "-" + occurrence


def transform(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Validate and transform four Synthea exports into project tables."""
    raw_dir = Path(raw_dir)
    raw = {name: _read_csv(raw_dir, name) for name in REQUIRED_COLUMNS}

    patients = raw["patients"].rename(columns={
        "id": "patient_id", "birthdate": "birth_date", "deathdate": "death_date"
    })[["patient_id", "gender", "birth_date", "city", "death_date"]]
    patients["deceased"] = patients["death_date"].notna().astype(int)
    patients = patients[["patient_id", "gender", "birth_date", "city", "deceased", "death_date"]]

    encounters = raw["encounters"].rename(columns={
        "id": "encounter_id", "patient": "patient_id", "start": "encounter_date",
        "encounterclass": "encounter_type",
    })[["encounter_id", "patient_id", "encounter_date", "encounter_type"]]

    conditions_raw = raw["conditions"]
    conditions = conditions_raw.rename(columns={
        "patient": "patient_id", "description": "condition_name", "start": "start_date"
    })[["patient_id", "condition_name", "start_date"]]
    conditions.insert(0, "condition_id", _stable_ids(
        conditions_raw, ["patient", "code", "start", "description"], "condition"
    ))

    procedures_raw = raw["procedures"]
    procedures = procedures_raw.rename(columns={
        "patient": "patient_id", "description": "procedure_name", "start": "procedure_date"
    })[["patient_id", "procedure_name", "procedure_date"]]
    procedures.insert(0, "procedure_id", _stable_ids(
        procedures_raw, ["patient", "encounter", "start", "description"], "procedure"
    ))
    return {"patients": patients, "encounters": encounters,
            "conditions": conditions, "procedures": procedures}


def build_database(raw_dir: str | Path, database_path: str | Path) -> Path:
    """Build a new constrained SQLite database atomically at ``database_path``."""
    frames = transform(raw_dir)
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = database_path.with_suffix(database_path.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        conn = sqlite3.connect(temporary)
        try:
            conn.executescript(SCHEMA)
            for table, frame in frames.items():
                frame.to_sql(table, conn, if_exists="append", index=False)
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise ValueError(f"foreign-key violations: {violations[:5]}")
            conn.commit()
        finally:
            # sqlite3.Connection's context manager commits/rolls back but does
            # not close; an explicit close is required before os.replace on Windows.
            conn.close()
        temporary.replace(database_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return database_path
