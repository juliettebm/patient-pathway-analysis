# Data dictionary

All records are synthetic and originate from Synthea CSV exports. Dates are stored
as ISO-like text in SQLite. Nullable means that the source may omit the value.

## `patients`

| Field | Type | Nullable | Source / meaning |
|---|---|---:|---|
| `patient_id` | TEXT | no | Synthea `patients.Id`; synthetic person identifier |
| `gender` | TEXT | no | Synthea `GENDER`; constrained to `M` or `F` in this dataset contract |
| `birth_date` | TEXT | no | Synthea `BIRTHDATE` |
| `city` | TEXT | yes | Synthea `CITY`; generated residence |
| `deceased` | INTEGER | no | Derived: 1 when `DEATHDATE` is populated, otherwise 0 |
| `death_date` | TEXT | yes | Synthea `DEATHDATE` |

## `encounters`

| Field | Type | Nullable | Source / meaning |
|---|---|---:|---|
| `encounter_id` | TEXT | no | Synthea `encounters.Id` |
| `patient_id` | TEXT | no | Synthea `PATIENT`; foreign key to `patients` |
| `encounter_date` | TEXT | yes | Synthea `START` |
| `encounter_type` | TEXT | yes | Synthea `ENCOUNTERCLASS` |

## `conditions`

| Field | Type | Nullable | Source / meaning |
|---|---|---:|---|
| `condition_id` | TEXT | no | Stable hash of patient, code, start and description plus duplicate index |
| `patient_id` | TEXT | no | Synthea `PATIENT`; foreign key to `patients` |
| `condition_name` | TEXT | no | Synthea `DESCRIPTION`; generated diagnosis or finding label |
| `start_date` | TEXT | yes | Synthea `START` |

## `procedures`

| Field | Type | Nullable | Source / meaning |
|---|---|---:|---|
| `procedure_id` | TEXT | no | Stable hash of patient, encounter, start and description plus duplicate index |
| `patient_id` | TEXT | no | Synthea `PATIENT`; foreign key to `patients` |
| `procedure_name` | TEXT | no | Synthea `DESCRIPTION` |
| `procedure_date` | TEXT | yes | Synthea `START` |

## Derived analytical fields

| Field | Definition |
|---|---|
| `age` | `(as_of_date - birth_date) / 365.25`; dashboard freezes `as_of_date` at 2025-01-01 |
| `nb_visits` | Count of encounter identifiers, including zero for patients with no encounter |
| `nb_chronic_groups` | Number of distinct chronic-disease groups a patient has (`CHRONIC_CONDITION_GROUPS` in `src/queries.py`) |
| `status` | `Multimorbid` at 2+ distinct chronic groups, otherwise `Not multimorbid`; project-specific list, not clinician-reviewed, not a validated definition |
| `has_obesity` | At least one condition exactly matching Synthea's obesity finding label |
