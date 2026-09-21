"""Reusable statistical checks for the synthetic cohort."""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from src.pipeline import OBESITY_CONDITION
from src.queries import MULTIMORBIDITY, MULTIMORBIDITY_THRESHOLD, OBESITY_VISITS, PATIENT_FOLLOWUP, PATIENT_VISITS


@dataclass(frozen=True)
class AnalysisResults:
    cohort_size: int
    chi2: float
    chi2_p_value: float
    fisher_odds_ratio: float
    fisher_p_value: float
    minimum_expected_count: float
    multimorbid_share: float
    obesity_u: float
    obesity_p_value: float
    obesity_median_visits: float
    other_median_visits: float
    age_split: float
    welch_t: float
    welch_p_value: float
    age_coefficient: float
    age_p_value: float
    r_squared: float
    adjusted_obesity_rate_ratio: float
    adjusted_obesity_p_value: float
    holm_adjusted_p_values: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


def run_analysis(conn: sqlite3.Connection, *, as_of_date: str = "2025-01-01",
                 threshold: int = MULTIMORBIDITY_THRESHOLD) -> AnalysisResults:
    """Run descriptive software checks; none of the outputs are causal estimates."""
    burden = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": threshold})
    contingency = pd.crosstab(burden["gender"], burden["status"])
    if contingency.shape != (2, 2):
        raise ValueError("Fisher's exact test requires a 2x2 gender/status table")
    chi2, chi2_p, _, expected = stats.chi2_contingency(contingency)
    fisher_odds, fisher_p = stats.fisher_exact(contingency.to_numpy())

    visits = pd.read_sql(PATIENT_VISITS, conn, params={"as_of_date": as_of_date})
    obesity = pd.read_sql(OBESITY_VISITS, conn, params={"condition": OBESITY_CONDITION})
    obese = obesity.loc[obesity["has_obesity"] == 1, "nb_visits"]
    other = obesity.loc[obesity["has_obesity"] == 0, "nb_visits"]
    if obese.empty or other.empty:
        raise ValueError("analysis requires non-empty obesity and comparison groups")
    obesity_u, obesity_p = stats.mannwhitneyu(obese, other, alternative="two-sided")

    age_split = float(visits["age"].median())
    young = visits.loc[visits["age"] <= age_split, "nb_visits"]
    old = visits.loc[visits["age"] > age_split, "nb_visits"]
    welch_t, welch_p = stats.ttest_ind(young, old, equal_var=False)

    # Retained only as a descriptive diagnostic for comparison with the notebook.
    ols = sm.OLS(visits["nb_visits"], sm.add_constant(visits[["age"]])).fit()

    followup = pd.read_sql(PATIENT_FOLLOWUP, conn, params={
        "as_of_date": as_of_date, "condition": OBESITY_CONDITION,
    })
    design = sm.add_constant(followup[["has_obesity", "age_at_censoring", "deceased"]])
    count_model = sm.GLM(
        followup["nb_visits"], design, family=sm.families.NegativeBinomial(alpha=1.0),
        offset=np.log(followup["observed_years"]),
    ).fit()
    adjusted_p = float(count_model.pvalues["has_obesity"])
    test_names = ["gender_multimorbidity_fisher", "obesity_unadjusted", "age_split_welch",
                  "obesity_adjusted_count_model"]
    adjusted = multipletests([fisher_p, obesity_p, welch_p, adjusted_p], method="holm")[1]

    return AnalysisResults(
        cohort_size=len(visits), chi2=float(chi2), chi2_p_value=float(chi2_p),
        fisher_odds_ratio=float(fisher_odds), fisher_p_value=float(fisher_p),
        minimum_expected_count=float(expected.min()),
        multimorbid_share=float((burden["status"] == "Multimorbid").mean()),
        obesity_u=float(obesity_u), obesity_p_value=float(obesity_p),
        obesity_median_visits=float(obese.median()), other_median_visits=float(other.median()),
        age_split=age_split, welch_t=float(welch_t), welch_p_value=float(welch_p),
        age_coefficient=float(ols.params["age"]), age_p_value=float(ols.pvalues["age"]),
        r_squared=float(ols.rsquared),
        adjusted_obesity_rate_ratio=float(np.exp(count_model.params["has_obesity"])),
        adjusted_obesity_p_value=adjusted_p,
        holm_adjusted_p_values=dict(zip(test_names, map(float, adjusted))),
    )


def burden_sensitivity(conn: sqlite3.Connection, thresholds=(1, 2, 3, 4)) -> pd.DataFrame:
    """Share of the cohort classified 'multimorbid' and Fisher p-value per threshold."""
    rows = []
    for threshold in thresholds:
        burden = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": threshold})
        table = pd.crosstab(burden["gender"], burden["status"])
        p_value = stats.fisher_exact(table.to_numpy())[1] if table.shape == (2, 2) else float("nan")
        rows.append({"threshold": threshold,
                     "multimorbid_share": float((burden["status"] == "Multimorbid").mean()),
                     "fisher_p_value": float(p_value)})
    return pd.DataFrame(rows)
