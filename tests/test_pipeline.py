import sqlite3

import pandas as pd
import pytest

from src.pipeline import build_database, transform


@pytest.fixture
def synthea_csvs(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame([
        {"Id": "p1", "GENDER": "F", "BIRTHDATE": "1980-01-01", "CITY": "Paris", "DEATHDATE": None},
        {"Id": "p2", "GENDER": "M", "BIRTHDATE": "1970-01-01", "CITY": "Lyon", "DEATHDATE": "2020-01-01"},
    ]).to_csv(raw / "patients.csv", index=False)
    pd.DataFrame([
        {"Id": "e1", "PATIENT": "p1", "START": "2024-01-01", "ENCOUNTERCLASS": "outpatient"},
        {"Id": "e2", "PATIENT": "p1", "START": "2024-02-01", "ENCOUNTERCLASS": "emergency"},
        {"Id": "e3", "PATIENT": "p2", "START": "2019-01-01", "ENCOUNTERCLASS": "inpatient"},
    ]).to_csv(raw / "encounters.csv", index=False)
    pd.DataFrame([
        {"CODE": "1", "PATIENT": "p1", "DESCRIPTION": "Obesity", "START": "2020-01-01"},
        {"CODE": "1", "PATIENT": "p2", "DESCRIPTION": "Obesity", "START": "2021-01-01"},
    ]).to_csv(raw / "conditions.csv", index=False)
    pd.DataFrame([
        {"START": "2024-01-01", "PATIENT": "p1", "ENCOUNTER": "e1", "DESCRIPTION": "Blood test"},
    ]).to_csv(raw / "procedures.csv", index=False)
    return raw


def test_transform_is_case_insensitive_and_builds_unique_ids(synthea_csvs):
    tables = transform(synthea_csvs)
    assert list(tables["patients"]["deceased"]) == [0, 1]
    assert tables["conditions"]["condition_id"].is_unique
    assert tables["procedures"]["procedure_id"].is_unique


def test_build_database_preserves_constraints_and_rows(synthea_csvs, tmp_path):
    database = build_database(synthea_csvs, tmp_path / "patient_journey.db")
    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        assert conn.execute("SELECT COUNT(*) FROM encounters").fetchone()[0] == 3
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO encounters VALUES ('bad', 'missing', NULL, NULL)")


def test_missing_generator_column_fails_with_clear_message(synthea_csvs):
    patients = pd.read_csv(synthea_csvs / "patients.csv").drop(columns="GENDER")
    patients.to_csv(synthea_csvs / "patients.csv", index=False)
    with pytest.raises(ValueError, match="patients.csv missing columns: gender"):
        transform(synthea_csvs)
