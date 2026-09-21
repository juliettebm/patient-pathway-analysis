import sqlite3
import warnings

import pandas as pd
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning, SingularMatrixWarning

from src.analysis import burden_sensitivity, run_analysis
from src.pipeline import OBESITY_CONDITION, SCHEMA
from src.queries import MULTIMORBID_PATIENTS, MULTIMORBIDITY, OBESITY_VISITS, PATIENT_VISITS


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
        ("c2", "p1", "Essential hypertension (disorder)", "2019-01-01"),
        ("c3", "p1", "Diabetes mellitus type 2 (disorder)", "2019-01-01"),
    ])
    return conn


def test_patient_visits_keeps_patients_without_encounters():
    with database() as conn:
        result = pd.read_sql(PATIENT_VISITS, conn, params={"as_of_date": "2025-01-01"})
    assert dict(zip(result.patient_id, result.nb_visits)) == {"p1": 2, "p2": 1, "p3": 0}


def test_multimorbidity_counts_distinct_chronic_groups():
    with database() as conn:
        result = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": 2}).set_index("patient_id")
    assert result.loc["p1", "nb_chronic_groups"] == 3
    assert result.loc["p1", "status"] == "Multimorbid"
    assert result.loc["p2", "status"] == "Not multimorbid"


def test_obesity_query_assigns_mutually_exclusive_groups():
    with database() as conn:
        result = pd.read_sql(OBESITY_VISITS, conn, params={"condition": OBESITY_CONDITION})
    assert result.set_index("patient_id")["has_obesity"].to_dict() == {"p1": 1, "p2": 0, "p3": 0}


def test_canonical_analysis_smoke_test():
    # Three rows deliberately make the design rank-deficient; this test checks
    # orchestration only, not parameter identification.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", PerfectSeparationWarning)
        warnings.simplefilter("ignore", SingularMatrixWarning)
        with database() as conn:
            # Fisher needs a 2x2 gender/status table, so add a second man with
            # chronic conditions and no encounters.
            conn.execute("INSERT INTO patients VALUES ('p4', 'M', '1985-01-01', 'Lille', 0, NULL)")
            conn.executemany("INSERT INTO conditions VALUES (?, ?, ?, ?)", [
                ("c8", "p2", "Asthma (disorder)", "2019-01-01"),
                ("c9", "p2", "Essential hypertension (disorder)", "2019-01-01"),
            ])
            result = run_analysis(conn, as_of_date="2025-01-01", threshold=2)
    assert result.cohort_size == 4
    assert result.obesity_median_visits == 2
    assert result.other_median_visits == 0
    assert 0 <= result.obesity_p_value <= 1


def test_same_disease_labels_and_non_chronic_labels_count_once():
    with database() as conn:
        conn.executemany("INSERT INTO conditions VALUES (?, ?, ?, ?)", [
            ("c4", "p2", "Chronic kidney disease stage 1 (disorder)", "2019-01-01"),
            ("c5", "p2", "Chronic kidney disease stage 2 (disorder)", "2020-01-01"),
            ("c6", "p2", "Stress (finding)", "2019-01-01"),
            ("c7", "p2", "Acute viral pharyngitis (disorder)", "2019-01-01"),
        ])
        result = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": 2}).set_index("patient_id")
        listed = pd.read_sql(MULTIMORBID_PATIENTS, conn, params={"threshold": 2})
    assert result.loc["p2", "nb_chronic_groups"] == 1
    assert result.loc["p2", "status"] == "Not multimorbid"
    assert list(listed["patient_id"]) == ["p1"]


def test_burden_sensitivity_reports_each_threshold():
    with database() as conn:
        result = burden_sensitivity(conn, thresholds=(1, 3))
    assert list(result["threshold"]) == [1, 3]
    assert result["multimorbid_share"].between(0, 1).all()
