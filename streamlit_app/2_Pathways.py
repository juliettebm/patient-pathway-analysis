import streamlit as st
import pandas as pd
from src.db_utils import get_db_connection

conn = get_db_connection()

st.title("⏱️ Care Pathways & Healthcare Utilization")

# ==========================
# KPI (Seuil à 5 conforme à la note méthodologique)
# ==========================
nb_patients = pd.read_sql("SELECT COUNT(*) FROM patients", conn).iloc[0,0]

avg_visits = pd.read_sql("""
    SELECT AVG(nb_visits) FROM (SELECT COUNT(*) AS nb_visits FROM encounters GROUP BY patient_id)
""", conn).iloc[0,0]

# Correction de la requête : On compte les maladies distinctes avec un seuil de 5
chronic_count = pd.read_sql("""
    SELECT COUNT(*)
    FROM (
        SELECT patient_id 
        FROM conditions 
        GROUP BY patient_id 
        HAVING COUNT(DISTINCT condition_name) >= 5
    )
""", conn).iloc[0,0]

col1, col2, col3 = st.columns(3)
col1.metric("Patients", f"{nb_patients:,}")
col2.metric("Average Visits", f"{avg_visits:.1f}")
col3.metric("Severe Chronic Patients (5+)", chronic_count)

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
# Chronic patients (Seuil à 5)
# ==========================
chronic = pd.read_sql("""
    SELECT patient_id, COUNT(DISTINCT condition_name) AS nb_conditions
    FROM conditions
    GROUP BY patient_id
    HAVING COUNT(DISTINCT condition_name) >= 5
    ORDER BY nb_conditions DESC
""", conn)

st.markdown("### Complex Multimorbid Patients (>= 5 conditions)")
st.dataframe(chronic.head(20), use_container_width=True)

st.markdown("---")
st.caption("Data source: Synthea synthetic dataset | SQL + Healthcare Analytics")
conn.close()