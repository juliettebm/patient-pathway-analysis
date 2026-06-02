import streamlit as st
import pandas as pd
import sqlite3

from src.db_utils import get_db_connection
conn = get_db_connection()

st.title("👤 Patient Explorer — Clinical Journey")

# =========================
# PATIENT SELECTION
# =========================

patient_ids = pd.read_sql("""
SELECT DISTINCT patient_id
FROM patients
ORDER BY patient_id
""", conn)

selected_patient = st.selectbox(
    "Select a patient ID",
    patient_ids["patient_id"].tolist()
)

# =========================
# PATIENT PROFILE
# =========================

info = pd.read_sql(f"""
SELECT *
FROM patients
WHERE patient_id = '{selected_patient}'
""", conn)

st.subheader("Patient profile")
st.dataframe(info, use_container_width=True)

# =========================
# ENCOUNTERS TIMELINE
# =========================

timeline = pd.read_sql(f"""
SELECT encounter_date, encounter_type
FROM encounters
WHERE patient_id = '{selected_patient}'
ORDER BY encounter_date
""", conn)

st.subheader("Medical timeline")

st.dataframe(timeline, use_container_width=True)

if not timeline.empty:
    st.line_chart(
        pd.DataFrame(
            {"visits": range(len(timeline))},
            index=pd.to_datetime(timeline["encounter_date"])
        )
    )

# =========================
# CONDITIONS
# =========================

conditions = pd.read_sql(f"""
SELECT condition_name, start_date
FROM conditions
WHERE patient_id = '{selected_patient}'
ORDER BY start_date
""", conn)

st.subheader("Diagnoses")

st.dataframe(conditions, use_container_width=True)

# =========================
# PROCEDURES
# =========================

procedures = pd.read_sql(f"""
SELECT procedure_name, procedure_date
FROM procedures
WHERE patient_id = '{selected_patient}'
ORDER BY procedure_date
""", conn)

st.subheader("Procedures")

st.dataframe(procedures, use_container_width=True)

# =========================
# SUMMARY (VERY IMPORTANT FOR JURY)
# =========================

st.markdown("---")
st.subheader("Clinical summary")

st.info(f"""
Patient ID: {selected_patient}

- Number of encounters: {len(timeline)}
- Number of diagnoses: {len(conditions)}
- Number of procedures: {len(procedures)}
""")

st.caption("Data source: Synthea synthetic dataset | Patient-level clinical exploration")