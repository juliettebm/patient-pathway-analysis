import streamlit as st
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from src.db_utils import get_db_connection

conn = get_db_connection()

st.title("🧪 Inferential Statistics & Clinical Modeling")
st.markdown("Ce module valide les hypothèses épidémiologiques à l'aide de tests d'inférence non-paramétriques et d'une modélisation linéaire robuste.")

# ==========================================
# 1. TEST DU CHI-DEUX (Seuil à 5)
# ==========================================
st.header("1. Association : Genre et Multimorbidité (5+ pathologies)")

df_chi = pd.read_sql("""
    SELECT p.gender,
           CASE 
               WHEN COUNT(DISTINCT c.condition_name) >= 5 THEN 'Multimorbide'
               ELSE 'Non-Multimorbide'
           END AS status
    FROM patients p
    LEFT JOIN conditions c ON p.patient_id = c.patient_id
    GROUP BY p.patient_id
""", conn)

contingency = pd.crosstab(df_chi["gender"], df_chi["status"])
chi2, p_chi, dof, exp = stats.chi2_contingency(contingency)

col1, col2 = st.columns([1, 2])
with col1:
    st.metric(label="p-value du Chi²", value=f"{p_chi:.4f}")
with col2:
    if p_chi < 0.05:
        st.success("📢 Rejet de H₀ : Association significative trouvée.")
    else:
        st.info("⚖️ Non-rejet de H₀ : Variables statistiquement indépendantes.")

with st.expander("Voir le tableau de contingence observé"):
    st.dataframe(contingency, use_container_width=True)

st.markdown("---")

# ==========================================
# 2. TESTS DE COMPARAISON (Visites)
# ==========================================
st.header("2. Analyse comparative du volume de soins")

df_visits = pd.read_sql("""
    SELECT 
        p.patient_id, p.gender,
        (julianday('now') - julianday(p.birth_date))/365.25 AS age,
        COUNT(e.encounter_id) AS nb_visits
    FROM patients p
    LEFT JOIN encounters e ON p.patient_id = e.patient_id
    GROUP BY p.patient_id
""", conn)

# Test de Mann-Whitney (Genre)
male_v = df_visits[df_visits["gender"] == "M"]["nb_visits"]
female_v = df_visits[df_visits["gender"] == "F"]["nb_visits"]
u_stat, p_mw = stats.mannwhitneyu(male_v, female_v)

# Test de Welch (Âge)
median_age = df_visits["age"].median()
young_v = df_visits[df_visits["age"] <= median_age]["nb_visits"]
old_v = df_visits[df_visits["age"] > median_age]["nb_visits"]
t_stat, p_welch = stats.ttest_ind(young_v, old_v, equal_var=False)

col_test1, col_test2 = st.columns(2)
with col_test1:
    st.subheader("Volume selon le Genre")
    st.metric("p-value Mann-Whitney U", f"{p_mw:.4f}")
    st.caption("Test non-paramétrique choisi en raison de l'asymétrie.")

with col_test2:
    st.subheader(f"Volume selon l'Âge (Seuil: {median_age:.0f} ans)")
    st.metric("p-value de Welch", f"{p_welch:.4f}")
    st.caption("Test de Welch appliqué pour s'affranchir de l'homoscédasticité.")

st.markdown("---")

# ==========================================
# 3. RÉGRESSION LINÉAIRE
# ==========================================
st.header("3. Modélisation OLS : Âge ➔ Total Visites")

X = df_visits[["age"]]
X = sm.add_constant(X)
y = df_visits["nb_visits"]
model = sm.OLS(y, X).fit()

coef_age = model.params["age"]
p_age = model.pvalues["age"]
r2 = model.rsquared

col_reg1, col_reg2 = st.columns([1, 2])
with col_reg1:
    st.metric("R² du modèle", f"{r2:.3f}")
    st.metric("Effet de l'Âge (β)", f"{coef_age:.3f}")
with col_reg2:
    st.markdown(f"""
    **Interprétation :** Chaque année d'âge supplémentaire est associée à une évolution de **{coef_age:.3f}** visites. 
    L'âge seul explique environ **{r2*100:.1f}%** de la variance du volume de soins.
    """)

with st.expander("Consulter le rapport OLS complet"):
    st.text(model.summary().as_text())

conn.close()