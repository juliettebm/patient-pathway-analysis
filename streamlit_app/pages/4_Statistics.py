"""Presentation layer for canonical synthetic-cohort checks in ``src.analysis``."""
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.analysis import run_analysis
from src.db_utils import get_db_connection
from src.queries import MULTIMORBIDITY, MULTIMORBIDITY_THRESHOLD

AS_OF_DATE = "2025-01-01"
conn = get_db_connection()
results = run_analysis(conn, as_of_date=AS_OF_DATE)

st.title("Statistical pipeline validation")
st.warning(
    "Educational demonstrator using a synthetic Synthea cohort. These tests check "
    "whether the software recovers simulator-encoded patterns. They are not clinical "
    "discoveries, do not estimate real-world effects and must not guide care."
)
st.caption(f"Ages are frozen at {AS_OF_DATE} so results remain reproducible.")

st.header(f"1. Gender and multimorbidity ({MULTIMORBIDITY_THRESHOLD}+ chronic groups)")
st.metric("Fisher exact p-value", f"{results.fisher_p_value:.3g}")
st.caption(f"Odds ratio: {results.fisher_odds_ratio:.3g}; multimorbid share: "
           f"{results.multimorbid_share:.1%}.")
st.info(
    "Fisher's exact test is primary because it is exact and does not depend on "
    "expected counts. The chi-square result is only a diagnostic (minimum expected "
    f"count {results.minimum_expected_count:.2f}). Multimorbidity counts distinct chronic "
    "groups from a list fixed before the analysis and not reviewed by a clinician; "
    "the data are synthetic, so this is not a validated clinical endpoint."
)
with st.expander("Observed contingency table"):
    groups = pd.read_sql(MULTIMORBIDITY, conn, params={"threshold": MULTIMORBIDITY_THRESHOLD})
    st.dataframe(pd.crosstab(groups["gender"], groups["status"]), use_container_width=True)

st.header("2. Healthcare-use comparisons")
left, right = st.columns(2)
with left:
    st.subheader("Generated obesity pattern")
    st.metric("Mann-Whitney p-value", f"{results.obesity_p_value:.3g}")
    st.caption(
        f"U={results.obesity_u:,.0f}; medians: obesity={results.obesity_median_visits:.0f}, "
        f"other={results.other_median_visits:.0f}. Simulator-dependent pipeline check."
    )
with right:
    st.subheader(f"Generated age split ({results.age_split:.0f} years)")
    st.metric("Welch p-value", f"{results.welch_p_value:.3g}")
    st.caption(f"t={results.welch_t:.2f}. Not an estimate for a real population.")

st.header("3. OLS software diagnostic")
left, right = st.columns([1, 2])
with left:
    st.metric("Model R²", f"{results.r_squared:.3f}")
    st.metric("Age coefficient", f"{results.age_coefficient:.3f}")
with right:
    st.markdown(
        f"Within this generated cohort, one additional year is associated with "
        f"**{results.age_coefficient:.3f}** visits and age describes "
        f"**{results.r_squared * 100:.1f}%** of variance. This is descriptive, "
        "non-causal and has no demonstrated external validity."
    )

st.header("4. Exploratory adjusted count model")
st.metric("Adjusted obesity rate ratio", f"{results.adjusted_obesity_rate_ratio:.3f}")
st.caption(
    "Negative-binomial GLM adjusted for age at censoring, observed encounter-window "
    "duration and death status. This partial adjustment does not make groups equivalent, "
    "remove synthetic-generator bias or support a causal obesity effect."
)
st.write(f"Raw p-value: {results.adjusted_obesity_p_value:.3g}")
st.write("Holm-adjusted p-values across the four prespecified checks:",
         results.holm_adjusted_p_values)
st.warning(
    "The unadjusted Mann-Whitney comparison is descriptive: patients are not matched, "
    "age and follow-up differ, and obesity may be recorded later in life."
)
conn.close()
