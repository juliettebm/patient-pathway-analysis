"""Reusable statistical analysis functions for the synthetic cohort."""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass

import pandas as pd
from scipy import stats
import statsmodels.api as sm

from src.pipeline import OBESITY_CONDITION
from src.queries import MULTIMORBIDITY, OBESITY_VISITS, PATIENT_VISITS


@dataclass(frozen=True)
class AnalysisResults:
    cohort_size: int
    chi2: float
    chi2_p_value: float
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

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def run_analysis(conn: sqlite3.Connection, *, as_of_date: str = "2025-01-01",
                 threshold: int = 5) -> AnalysisResults:
    """Run canonical checks; results apply only to the supplied synthetic cohort."""
    multimorbidity = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": threshold})
    contingency = pd.crosstab(multimorbidity["gender"], multimorbidity["status"])
    chi2, chi2_p, _, _ = stats.chi2_contingency(contingency)

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
    model = sm.OLS(visits["nb_visits"], sm.add_constant(visits[["age"]])).fit()
    return AnalysisResults(
        cohort_size=len(visits), chi2=float(chi2), chi2_p_value=float(chi2_p),
        obesity_u=float(obesity_u), obesity_p_value=float(obesity_p),
        obesity_median_visits=float(obese.median()), other_median_visits=float(other.median()),
        age_split=age_split, welch_t=float(welch_t), welch_p_value=float(welch_p),
        age_coefficient=float(model.params["age"]), age_p_value=float(model.pvalues["age"]),
        r_squared=float(model.rsquared),
    )
