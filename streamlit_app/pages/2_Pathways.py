import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `src`
from src.analysis import burden_sensitivity
from src.db_utils import get_db_connection
from src.queries import MULTIMORBID_PATIENTS, MULTIMORBIDITY_THRESHOLD

conn = get_db_connection()

st.title("⏱️ Care Pathways & Healthcare Utilization")

# ==========================
# KPI (Seuil à 5 conforme à la note méthodologique)
# ==========================
nb_patients = pd.read_sql("SELECT COUNT(*) FROM patients", conn).iloc[0,0]

avg_visits = pd.read_sql("""
    SELECT AVG(nb_visits) FROM (SELECT COUNT(*) AS nb_visits FROM encounters GROUP BY patient_id)
""", conn).iloc[0,0]

chronic = pd.read_sql(MULTIMORBID_PATIENTS, conn, params={"threshold": MULTIMORBIDITY_THRESHOLD})
chronic_count = len(chronic)

col1, col2, col3 = st.columns(3)
col1.metric("Patients", f"{nb_patients:,}")
col2.metric("Average Visits", f"{avg_visits:.1f}")
col3.metric(f"Multimorbid patients ({MULTIMORBIDITY_THRESHOLD}+ chronic groups)", chronic_count)

st.markdown("---")

# ==========================
# Visits distribution
# ==========================
visits = pd.read_sql("""
    SELECT patient_id, COUNT(*) AS nb_visits 
    FROM encounters 
    GROUP BY patient_id 
    ORDER BY nb_visits DESC
""", conn)

st.markdown("### Healthcare utilization")
st.bar_chart(visits.head(30).set_index("patient_id"))

# ==========================
# Top 10 users
# ==========================
st.markdown("### Top 10 healthcare users")
st.dataframe(visits.head(10), use_container_width=True)

# ==========================
# Multimorbid patients
# ==========================
st.markdown(f"### Multimorbid patients (>= {MULTIMORBIDITY_THRESHOLD} distinct chronic groups)")
st.caption("Counts distinct chronic-disease groups (CHRONIC_CONDITION_GROUPS in src/queries.py); the list is not clinician-reviewed and Synthea data are synthetic.")
st.dataframe(chronic.head(20), use_container_width=True)

st.markdown("### Threshold sensitivity")
st.caption("Share of the cohort classified as multimorbid, and the gender association, at other thresholds.")
st.dataframe(burden_sensitivity(conn), use_container_width=True)

st.markdown("---")
st.caption("Data source: Synthea synthetic dataset | SQL + Healthcare Analytics")
conn.close()
