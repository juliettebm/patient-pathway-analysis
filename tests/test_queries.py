import sqlite3

import pandas as pd

from src.analysis import run_analysis
from src.pipeline import OBESITY_CONDITION, SCHEMA
from src.queries import MULTIMORBIDITY, OBESITY_VISITS, PATIENT_VISITS


def database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)", [
        ("p1", "F", "1980-01-01", "Paris", 0, None),
        ("p2", "M", "2000-01-01", "Lyon", 0, None),
        ("p3", "F", "1990-01-01", "Nice", 0, None),
    ])
    conn.executemany("INSERT INTO encounters VALUES (?, ?, ?, ?)", [
        ("e1", "p1", "2020-01-01", "outpatient"),
        ("e2", "p1", "2020-02-01", "outpatient"),
        ("e3", "p2", "2020-01-01", "outpatient"),
    ])
    conn.executemany("INSERT INTO conditions VALUES (?, ?, ?, ?)", [
        ("c1", "p1", OBESITY_CONDITION, "2019-01-01"),
        ("c2", "p1", "Hypertension", "2019-01-01"),
        ("c3", "p1", "Diabetes", "2019-01-01"),
    ])
    return conn


def test_patient_visits_keeps_patients_without_encounters():
    with database() as conn:
        result = pd.read_sql(PATIENT_VISITS, conn, params={"as_of_date": "2025-01-01"})
    assert dict(zip(result.patient_id, result.nb_visits)) == {"p1": 2, "p2": 1, "p3": 0}


def test_multimorbidity_counts_distinct_conditions():
    with database() as conn:
        result = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": 3})
    assert result.set_index("patient_id").loc["p1", "status"] == "Multimorbid"
    assert result.set_index("patient_id").loc["p2", "status"] == "Not multimorbid"


def test_obesity_query_assigns_mutually_exclusive_groups():
    with database() as conn:
        result = pd.read_sql(OBESITY_VISITS, conn, params={"condition": OBESITY_CONDITION})
    assert result.set_index("patient_id")["has_obesity"].to_dict() == {"p1": 1, "p2": 0, "p3": 0}


def test_canonical_analysis_smoke_test():
    with database() as conn:
        result = run_analysis(conn, as_of_date="2025-01-01", threshold=2)
    assert result.cohort_size == 3
    assert result.obesity_median_visits == 2
    assert result.other_median_visits == 0.5
    assert 0 <= result.obesity_p_value <= 1
