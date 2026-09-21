"""Canonical, reusable SQL queries used by notebooks, tests and dashboard."""

PATIENT_VISITS = """
SELECT p.patient_id, p.gender,
       (julianday(:as_of_date) - julianday(p.birth_date)) / 365.25 AS age,
       COUNT(e.encounter_id) AS nb_visits
FROM patients AS p
LEFT JOIN encounters AS e ON e.patient_id = p.patient_id
GROUP BY p.patient_id, p.gender, p.birth_date
"""

MULTIMORBIDITY = """
SELECT p.patient_id, p.gender,
       CASE WHEN COUNT(DISTINCT c.condition_name) >= :threshold
            THEN 'Multimorbid' ELSE 'Not multimorbid' END AS status
FROM patients AS p
LEFT JOIN conditions AS c ON c.patient_id = p.patient_id
GROUP BY p.patient_id, p.gender
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
