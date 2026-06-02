import streamlit as st
import pandas as pd
from src.db_utils import get_db_connection

conn = get_db_connection()

st.title("📊 Cohort Overview")

# ==========================
# KPI
# ==========================
nb_patients = pd.read_sql("SELECT COUNT(*) AS n FROM patients", conn).iloc[0,0]

avg_age = pd.read_sql("""
    SELECT AVG((julianday('now') - julianday(birth_date))/365.25) FROM patients
""", conn).iloc[0,0]

avg_visits = pd.read_sql("""
    SELECT AVG(nb_visits)
    FROM (SELECT patient_id, COUNT(*) AS nb_visits FROM encounters GROUP BY patient_id)
""", conn).iloc[0,0]

gender_df = pd.read_sql("SELECT gender, COUNT(*) AS count FROM patients GROUP BY gender", conn)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patients", f"{nb_patients:,}")
col2.metric("Average Age", f"{avg_age:.1f} ans")
col3.metric("Average Visits", f"{avg_visits:.1f}")
col4.metric("Gender Groups", gender_df.shape[0])

st.markdown("---")

# ==========================
# Population structure
# ==========================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 👥 Gender Distribution")
    st.bar_chart(gender_df.set_index("gender"))

with col_right:
    st.markdown("### ⏳ Structure d'âge")
    # Extraction des âges
    age_df = pd.read_sql("""
        SELECT (julianday('now') - julianday(birth_date))/365.25 AS age
        FROM patients
    """, conn)
    # Création d'un histogramme propre par tranches de 10 ans
    age_counts = pd.cut(
        age_df["age"], 
        bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 
        right=False
    ).value_counts().sort_index()
    
    # Transformation de l'index pour un affichage propre (ex: "[30, 40)" devient "30-39 ans")
    age_counts.index = age_counts.index.astype(str) 
    
    st.bar_chart(age_counts)
    st.caption("Distribution par tranche d'âge décennale.")

st.markdown("---")
st.caption("Data source: Synthea synthetic dataset | SQL + Statistics + BI Project")
conn.close()