# Patient Pathway Analysis

[![CI](https://github.com/juliettebm/patient-pathway-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/juliettebm/patient-pathway-analysis/actions/workflows/ci.yml)
![Reproducibility](https://img.shields.io/badge/reproducibility-fixture--tested-yellow)

End-to-end SQL, statistics and Streamlit demonstrator built from
[Synthea](https://synthea.mitre.org/) synthetic health records.

> [!IMPORTANT]
> This repository demonstrates a data pipeline; it does **not** demonstrate
> clinical performance. The cohort contains no real patients. Associations and
> very small p-values reflect the Synthea generation mechanism, the selected
> sample and its size. They are neither clinical discoveries nor evidence that
> the effects generalise to a real population.

## What this project validates

The statistical analyses are positive-control checks: they verify that ingestion,
SQL grouping and statistical code recover patterns present in the generated data.
For example, the previously reported obesity result (`p = 8.55e-26`) should be read
as “the pipeline detects this simulator-dependent pattern”, not “obesity has a
newly discovered clinical effect”. No causal or external-validity claim is made.

## Pipeline

```mermaid
flowchart LR
    A[Synthea generator] --> B[Raw CSV exports]
    B -->|schema and contract validation| C[SQLite database]
    C --> D[Reusable SQL queries]
    D --> E[Statistical checks]
    D --> F[Streamlit dashboard]
    E --> F
    T[pytest fixtures] -. validate ingestion .-> C
    T -. validate expected query results .-> D
```

The executable ingestion lives in `src/pipeline.py`; canonical queries live in
`src/queries.py`. The notebooks remain exploratory presentations, while these
modules are the tested source of truth.

## Reproduce

```bash
git clone https://github.com/juliettebm/patient-pathway-analysis.git
cd patient-pathway-analysis
python -m pip install -r requirements.txt
```

Generate Synthea CSV output and place `patients.csv`, `encounters.csv`,
`conditions.csv` and `procedures.csv` in `data/raw/`, then run:

```bash
python scripts/build_database.py
pytest -q
python scripts/verify_results.py
streamlit run streamlit_app/app.py
```

The loader validates required Synthea columns, creates stable identifiers for
condition and procedure rows, preserves SQLite primary/foreign-key constraints,
checks referential integrity, and only replaces the target database after a
successful build.

## Test coverage

The tests use a small deterministic synthetic fixture and cover:

- the generator-export contract (required files and columns);
- case-insensitive Synthea headers and derived deceased status;
- stable unique row identifiers;
- row loading, primary keys and foreign-key enforcement;
- zero-encounter patients retained by `LEFT JOIN`;
- distinct-condition multimorbidity counting;
- mutually exclusive obesity comparison groups.

These are software and data-contract tests. They do not validate Synthea as a
model of clinical reality.

CI runs the deterministic fixture tests and syntax smoke test on Python 3.12.10
with exact dependency versions. Because the full Synthea export is intentionally
not committed, full-cohort reproducibility is reported separately: after building
the database, `scripts/verify_results.py` compares canonical calculations with
`results/reference_metrics.json` and fails on unexplained drift. The snapshot is a
software-regression reference, not a clinical benchmark.

## Database and data dictionary

| Table | Grain | Primary key | Description |
|---|---|---|---|
| `patients` | one row per synthetic person | `patient_id` | Demographics and vital status |
| `encounters` | one row per generated visit | `encounter_id` | Dated healthcare encounters |
| `conditions` | one condition occurrence | `condition_id` | Generated diagnoses/findings |
| `procedures` | one procedure occurrence | `procedure_id` | Generated clinical procedures |

See the complete field-level [data dictionary](docs/data_dictionary.md).

## Analyses

- SQL cohort KPIs, visit counts, multimorbidity and pathway chronology;
- chi-square check of gender and 5+ distinct conditions;
- Mann-Whitney comparison of visit counts by generated obesity status;
- Welch comparison across generated age groups;
- descriptive OLS diagnostic of age and visit count.

The 5+ threshold is project-specific: Synthea records dense longitudinal histories,
so it is used to isolate a smaller complex subgroup. It is not presented as a
universal clinical definition. Mann-Whitney is used for skewed visit counts and
Welch's test avoids assuming equal group variance. Statistical significance alone
is never interpreted as clinical importance.

## Project layout

```text
data/raw/                 Synthea CSV exports (not tracked)
database/                 generated SQLite database (not tracked)
docs/data_dictionary.md   field definitions and provenance
notebooks/                exploratory SQL and statistical walkthroughs
scripts/build_database.py reproducible ingestion command
scripts/verify_results.py full-cohort result-drift check
src/pipeline.py            validation and SQLite build
src/queries.py             canonical parameterised SQL
src/analysis.py            canonical statistical calculations
streamlit_app/             interactive presentation
tests/                     deterministic pipeline and SQL tests
results/                   versioned software-regression snapshot
```

## Limitations

- Synthetic-data results do not establish real-world performance or validity.
- Synthea's rules can directly or indirectly encode the detected associations.
- P-values shrink with sample size and do not measure effect importance.
- The dashboard is educational and is not a medical device or decision aid.
- Real evaluation would require an independently governed clinical dataset,
  prespecified endpoints, bias assessment and external validation.

## Data source and licence

Walonoski, J., et al. (2017). *Synthea: An approach, method, and software
mechanism for generating synthetic patients and the synthetic electronic health
care record.* Journal of the American Medical Informatics Association.

Code is released under the [MIT License](LICENSE). No real patient information is
included in this repository.
