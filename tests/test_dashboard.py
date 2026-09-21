from pathlib import Path
import sqlite3

from streamlit.testing.v1 import AppTest

from src.pipeline import OBESITY_CONDITION, SCHEMA


def test_landing_page_renders_as_educational_demonstrator():
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app" / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not app.exception
    assert any("Educational" in item.value for item in app.markdown)
    assert any("not clinically validated" in item.value for item in app.info)


def test_overview_page_executes_against_sqlite_fixture(tmp_path, monkeypatch):
    database = tmp_path / "dashboard.db"
    with sqlite3.connect(database) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)",
            ("p1", "F", "1980-01-01", "Paris", 0, None),
        )
        conn.execute(
            "INSERT INTO encounters VALUES (?, ?, ?, ?)",
            ("e1", "p1", "2024-01-01", "outpatient"),
        )
    monkeypatch.setenv("PATIENT_PATHWAY_DB", str(database))
    page = Path(__file__).resolve().parents[1] / "streamlit_app" / "pages" / "1_Overview.py"
    app = AppTest.from_file(str(page)).run(timeout=10)
    assert not app.exception
    assert app.metric[0].value == "1"


def _fixture_db(tmp_path, monkeypatch):
    database = tmp_path / "dashboard.db"
    patients, encounters, conditions = [], [], []
    for i in range(8):
        pid = f"p{i}"
        patients.append((pid, "F" if i % 2 else "M", f"{1960 + 5 * i}-01-01", "Paris", 0, None))
        for j in range(1 + i % 4 + (i % 3)):
            encounters.append((f"e{i}_{j}", pid, f"2023-0{1 + j}-01", "outpatient"))
        labels = ["Essential hypertension (disorder)", "Diabetes mellitus type 2 (disorder)", "Asthma (disorder)"] if i % 4 < 2 else ["Asthma (disorder)"]
        if i % 3 == 0:
            labels = labels + [OBESITY_CONDITION]
        conditions += [(f"c{i}_{k}", pid, name, "2019-01-01") for k, name in enumerate(labels)]
    with sqlite3.connect(database) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)", patients)
        conn.executemany("INSERT INTO encounters VALUES (?, ?, ?, ?)", encounters)
        conn.executemany("INSERT INTO conditions VALUES (?, ?, ?, ?)", conditions)
    monkeypatch.setenv("PATIENT_PATHWAY_DB", str(database))


def _page(name):
    return str(Path(__file__).resolve().parents[1] / "streamlit_app" / "pages" / name)


def test_pathways_page_executes(tmp_path, monkeypatch):
    _fixture_db(tmp_path, monkeypatch)
    app = AppTest.from_file(_page("2_Pathways.py")).run(timeout=20)
    assert not app.exception
    assert app.metric[0].value == "8"


def test_patient_explorer_page_executes(tmp_path, monkeypatch):
    _fixture_db(tmp_path, monkeypatch)
    app = AppTest.from_file(_page("3_Patient_Explorer.py")).run(timeout=20)
    assert not app.exception


def test_statistics_page_shows_scope_warning(tmp_path, monkeypatch):
    _fixture_db(tmp_path, monkeypatch)
    app = AppTest.from_file(_page("4_Statistics.py")).run(timeout=30)
    assert not app.exception
    assert any("Educational demonstrator" in w.value for w in app.warning)
