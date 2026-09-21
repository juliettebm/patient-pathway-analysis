import streamlit as st

st.set_page_config(
    page_title="Patient Pathway Analysis",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Patient Pathway Analysis System")

st.markdown("""
### Educational Patient-Pathway Dashboard

This synthetic-data demonstrator explores generated patient pathways using:

- SQL relational modeling
- Healthcare KPIs
- Statistical inference
- Patient-level exploration

Use the navigation menu on the left to explore the different modules.
""")

st.sidebar.title("Navigation")
st.sidebar.info("Select a module above")

st.info("Educational use only — not clinically validated and not a decision-support tool.")

st.markdown("---")
st.caption("Data source: Synthea synthetic health dataset | Educational project")
