import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_published_obesity_result_matches_reference_snapshot():
    reference = json.loads((ROOT / "results" / "reference_metrics.json").read_text(encoding="utf-8"))
    expected = reference["metrics"]["obesity_p_value"]
    expected_text = f"{expected:.2e}"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    notebook = (ROOT / "notebooks" / "03_statistical_analysis.ipynb").read_text(encoding="utf-8")
    assert expected_text in readme
    assert expected_text in notebook


def test_public_surfaces_state_educational_synthetic_scope():
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    app = (ROOT / "streamlit_app" / "app.py").read_text(encoding="utf-8").lower()
    statistics = (ROOT / "streamlit_app" / "pages" / "4_Statistics.py").read_text(encoding="utf-8").lower()
    assert "synthetic" in readme and "not" in readme and "clinical" in readme
    assert "educational" in app and "not clinically validated" in app
    assert "educational demonstrator" in statistics and "not clinical" in statistics
