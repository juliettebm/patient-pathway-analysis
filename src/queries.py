"""Canonical, reusable SQL queries used by notebooks, tests and dashboard."""

ANALYSIS_DATE = "2025-01-01"

# Multimorbidity is counted on chronic-disease groups, not on raw Synthea labels.
# Synthea mixes diagnoses with social, administrative and acute entries, and the
# same disease appears under several labels (e.g. CKD stages 1-4). Each label
# below maps to one chronic group; a patient counts once per group. The list was
# fixed from label names alone, before any outcome was examined, and has NOT been
# reviewed by a clinician. Extend it after inspecting
# `SELECT condition_name, COUNT(*) FROM conditions GROUP BY 1` on a new export.
CHRONIC_CONDITION_GROUPS = {
    "hypertension": ["Essential hypertension (disorder)"],
    "diabetes": [
        "Diabetes mellitus type 2 (disorder)",
        "Disorder of kidney due to diabetes mellitus (disorder)",
        "Microalbuminuria due to type 2 diabetes mellitus (disorder)",
        "Proteinuria due to type 2 diabetes mellitus (disorder)",
        "Neuropathy due to type 2 diabetes mellitus (disorder)",
        "Nonproliferative diabetic retinopathy due to type II diabetes mellitus",
        "Proliferative diabetic retinopathy due to type II diabetes mellitus",
        "Macular edema and retinopathy due to type 2 diabetes mellitus (disorder)",
    ],
    "dyslipidemia": ["Hyperlipidemia (disorder)", "Hypertriglyceridemia (disorder)"],
    "metabolic_syndrome": ["Metabolic syndrome X (disorder)"],
    "obesity": ["Body mass index 30+ - obesity (finding)",
                "Body mass index 40+ - severely obese (finding)"],
    "ischemic_heart_disease": ["Ischemic heart disease (disorder)"],
    "heart_failure": ["Chronic congestive heart failure (disorder)", "Heart failure (disorder)"],
    "atrial_fibrillation": ["Atrial fibrillation (disorder)"],
    "stroke": ["Cerebrovascular accident (disorder)"],
    "valvular_heart_disease": [
        "Aortic valve stenosis (disorder)", "Aortic valve regurgitation (disorder)",
        "Mitral valve regurgitation (disorder)", "Mitral valve stenosis (disorder)",
        "Tricuspid valve regurgitation (disorder)", "Pulmonic valve stenosis (disorder)",
        "Pulmonic valve regurgitation (disorder)",
    ],
    "chronic_kidney_disease": [
        "Chronic kidney disease stage 1 (disorder)", "Chronic kidney disease stage 2 (disorder)",
        "Chronic kidney disease stage 3 (disorder)", "Chronic kidney disease stage 4 (disorder)",
        "End-stage renal disease (disorder)",
    ],
    "copd": ["Pulmonary emphysema (disorder)", "Chronic obstructive bronchitis (disorder)"],
    "asthma": ["Asthma (disorder)", "Childhood asthma (disorder)"],
    "chronic_sinusitis": ["Chronic sinusitis (disorder)"],
    "allergic_rhinitis": ["Perennial allergic rhinitis (disorder)",
                          "Perennial allergic rhinitis with seasonal variation (disorder)",
                          "Seasonal allergic rhinitis (disorder)"],
    "atopic_dermatitis": ["Atopic dermatitis (disorder)"],
    "cancer": [
        "Malignant neoplasm of breast (disorder)", "Neoplasm of prostate (disorder)",
        "Carcinoma in situ of prostate (disorder)", "Non-small cell lung cancer (disorder)",
        "Non-small cell carcinoma of lung  TNM stage 1 (disorder)",
        "Small cell carcinoma of lung (disorder)",
        "Primary small cell malignant neoplasm of lung  TNM stage 1 (disorder)",
        "Primary malignant neoplasm of colon (disorder)", "Malignant neoplasm of colon (disorder)",
        "Overlapping malignant neoplasm of colon (disorder)",
        "Metastatic malignant neoplasm to colon (disorder)",
        "Metastatic malignant neoplasm to prostate (disorder)",
        "Leukemia  disease (disorder)", "Multiple myeloma (disorder)",
    ],
    "dementia": ["Alzheimer's disease (disorder)",
                 "Familial Alzheimer's disease of early onset (disorder)"],
    "osteoporosis": ["Osteoporosis (disorder)"],
    "osteoarthritis": ["Osteoarthritis of knee (disorder)", "Osteoarthritis of hip (disorder)",
                       "Localized  primary osteoarthritis of the hand (disorder)"],
    "rheumatoid_arthritis": ["Rheumatoid arthritis (disorder)"],
    "gout": ["Gout"],
    "fibromyalgia": ["Fibromyalgia (disorder)", "Primary fibromyalgia syndrome (disorder)"],
    "chronic_pain": ["Chronic pain (finding)", "Chronic low back pain (finding)",
                     "Chronic neck pain (finding)"],
    "epilepsy": ["Epilepsy (disorder)", "Seizure disorder (disorder)"],
    "migraine": ["Chronic intractable migraine without aura (disorder)",
                 "Transformed migraine (disorder)"],
    "depression": ["Major depressive disorder (disorder)"],
    "anxiety_ptsd": ["Severe anxiety (panic) (finding)", "Posttraumatic stress disorder (disorder)"],
    "substance_use_disorder": ["Alcoholism (disorder)", "Dependent drug abuse (disorder)",
                               "Opioid abuse"],
    "sleep_apnea": ["Obstructive sleep apnea syndrome (disorder)", "Sleep apnea (disorder)"],
    "hypothyroidism": ["Idiopathic atrophic hypothyroidism (disorder)"],
    "chronic_hepatitis_c": ["Chronic hepatitis C (disorder)"],
    "hiv_aids": ["Human immunodeficiency virus infection (disorder)",
                 "Acquired immune deficiency syndrome (disorder)"],
    "neurodevelopmental_disability": ["Cerebral palsy (disorder)", "Intellectual disability (disorder)"],
}

# Single definition of "multimorbid": at least this many distinct chronic groups
# (the usual literature threshold is 2+). Fixed before results were examined.
MULTIMORBIDITY_THRESHOLD = 2


def _chronic_cte() -> str:
    rows = ", ".join(
        "('" + name.replace("'", "''") + "', '" + group + "')"
        for group, names in CHRONIC_CONDITION_GROUPS.items() for name in names
    )
    return f"WITH chronic(condition_name, chronic_group) AS (VALUES {rows})"


_CHRONIC_CTE = _chronic_cte()

PATIENT_VISITS = """
SELECT p.patient_id, p.gender,
       (julianday(:as_of_date) - julianday(p.birth_date)) / 365.25 AS age,
       COUNT(e.encounter_id) AS nb_visits
FROM patients AS p
LEFT JOIN encounters AS e ON e.patient_id = p.patient_id
GROUP BY p.patient_id, p.gender, p.birth_date
"""

MULTIMORBIDITY = _CHRONIC_CTE + """
SELECT p.patient_id, p.gender,
       COUNT(DISTINCT ch.chronic_group) AS nb_chronic_groups,
       CASE WHEN COUNT(DISTINCT ch.chronic_group) >= :threshold
            THEN 'Multimorbid' ELSE 'Not multimorbid' END AS status
FROM patients AS p
LEFT JOIN conditions AS c ON c.patient_id = p.patient_id
LEFT JOIN chronic AS ch ON ch.condition_name = c.condition_name
GROUP BY p.patient_id, p.gender
"""

MULTIMORBID_PATIENTS = _CHRONIC_CTE + """
SELECT c.patient_id, COUNT(DISTINCT ch.chronic_group) AS nb_chronic_groups
FROM conditions AS c
JOIN chronic AS ch ON ch.condition_name = c.condition_name
GROUP BY c.patient_id
HAVING COUNT(DISTINCT ch.chronic_group) >= :threshold
ORDER BY nb_chronic_groups DESC
"""

OBESITY_VISITS = """
SELECT p.patient_id,
       CASE WHEN EXISTS (
           SELECT 1 FROM conditions AS c
           WHERE c.patient_id = p.patient_id AND c.condition_name = :condition
       ) THEN 1 ELSE 0 END AS has_obesity,
       COUNT(e.encounter_id) AS nb_visits
FROM patients AS p
LEFT JOIN encounters AS e ON e.patient_id = p.patient_id
GROUP BY p.patient_id
"""

PATIENT_FOLLOWUP = """
SELECT p.patient_id,
       p.deceased,
       (julianday(COALESCE(p.death_date, :as_of_date)) - julianday(p.birth_date))
           / 365.25 AS age_at_censoring,
       CASE WHEN EXISTS (
           SELECT 1 FROM conditions AS c
           WHERE c.patient_id = p.patient_id AND c.condition_name = :condition
       ) THEN 1 ELSE 0 END AS has_obesity,
       COUNT(e.encounter_id) AS nb_visits,
       MAX(30.0, julianday(MAX(e.encounter_date)) - julianday(MIN(e.encounter_date)) + 1.0)
           / 365.25 AS observed_years
FROM patients AS p
JOIN encounters AS e ON e.patient_id = p.patient_id
WHERE date(e.encounter_date) <= date(COALESCE(p.death_date, :as_of_date))
GROUP BY p.patient_id, p.deceased, p.birth_date, p.death_date
"""
