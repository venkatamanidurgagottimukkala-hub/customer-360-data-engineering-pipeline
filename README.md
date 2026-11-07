# Customer 360 Data Engineering Pipeline

## 1. Project Overview

The Customer 360 Data Engineering Pipeline is a Python-based data engineering solution that integrates customer, account, order, and interaction datasets into a unified Customer 360 view.

The pipeline performs source data ingestion, schema validation, data quality checks, customer identity resolution, transformation, publishing, SQLite storage, and reconciliation.

It is designed to support reliable and reproducible data processing through deterministic data generation, duplicate detection, data lineage, run tracking, automated testing, and performance optimization.

## 2. Key Features

- Synthetic data generation using Faker and Pandas.
- Ingestion of multiple CSV source datasets.
- Schema and data quality validation.
- Duplicate primary key detection.
- Foreign key integrity validation.
- Date and business rule validation.
- Rejected record quarantine with rejection reasons.
- Deterministic customer identity resolution.
- Canonical customer ID assignment.
- Manual review flags for uncertain identity matches.
- Preservation of associated account, order, and interaction records during identity resolution.
- Unified Customer 360 transformation.
- Deterministic pipeline run identification.
- SQLite database storage.
- Interaction event history and pipeline run history.
- Automated reconciliation checks.
- Structured logging and execution summaries.
- Automated testing using Pytest.
- Performance benchmarking and vectorized validation optimization.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core pipeline development |
| Pandas | Data processing and transformation |
| Faker | Synthetic data generation |
| SQLite | Database storage |
| SQL | Data reconciliation |
| Pytest | Automated testing |
| Logging | Pipeline monitoring |
| JSON | Execution and reconciliation reports |

## 4. Architecture

The pipeline follows this processing flow:

1. Synthetic source data generation.
2. Raw CSV dataset creation.
3. Data ingestion and schema validation.
4. Customer data quality validation.
5. Customer identity resolution.
6. Canonical customer ID assignment.
7. Child dataset customer ID mapping.
8. Account, order, and interaction validation.
9. Customer 360 transformation.
10. CSV publishing and SQLite storage.
11. Data reconciliation.
12. Execution reports and logs.

For the detailed architecture diagram, see [`docs/architecture.md`](docs/architecture.md).

## 5. Source Datasets

The pipeline processes four source datasets.

### Customers

Contains customer identity and contact information, including customer ID, name, email, phone, and creation timestamp.

### Accounts

Contains customer account information, account types, account statuses, and creation timestamps.

### Orders

Contains product information, order amounts, order statuses, and order dates.

### Interactions

Contains customer communication and interaction history.

## 6. Customer Identity Resolution

The identity resolution module identifies potential duplicate customer records using normalized email addresses and phone numbers.

### Matching Rules

| Condition | Action |
|---|---|
| Same normalized email and phone | Automatically merge |
| Same email but different phone | Flag for manual review |
| Same phone but different email | Flag for manual review |
| Similar names alone | Do not automatically merge |

### Canonical Customer ID

The lexicographically smallest customer ID is selected as the canonical ID for automatically matched customer records.

Associated account, order, and interaction records are mapped to the canonical customer ID before foreign key validation.

The pipeline generates two identity-related reports:

- `outputs/customer_identity_mapping.csv`
- `outputs/identity_manual_review.csv`

These reports provide traceability for resolved identities and uncertain matches.

Fuzzy name matching is intentionally not used to avoid incorrectly merging customers based only on similar names.

## 7. Customer 360 Output

The unified Customer 360 dataset contains:

- Customer identification and contact details.
- Total account count.
- Active account count.
- Total order count.
- Total order amount.
- Latest order date.
- Total interaction count.
- Latest interaction date.

The transformation uses customer-level aggregation and left joins to retain customers even when they have no accounts, orders, or interactions.

## 8. Data Quality and Validation

The validation layer checks:

- Missing values.
- Duplicate primary keys.
- Invalid customer references.
- Invalid date values.
- Records dated before customer creation.
- Invalid order amounts.
- Invalid categorical values.

Invalid records are separated into quarantine datasets with rejection reasons.

The validation implementation uses vectorized Pandas operations to improve processing performance.

## 9. Idempotency and Traceability

The pipeline generates a deterministic run ID using SHA-256 hashing of the source CSV files.

The run ID and source filename are added to published source datasets.

Customer identity mapping and manual review reports also include the run ID.

Repeated processing of unchanged input produces the same run ID and replaces the current output datasets rather than appending duplicate records.

Rejected records are retained in quarantine datasets with their rejection reasons, supporting investigation and traceability.

## 10. Database Storage and History

The pipeline stores its current processed datasets in SQLite.

### Current-state tables

- `customers`
- `accounts`
- `orders`
- `interactions`
- `customer_360`

### History tables

- `pipeline_run_history`
- `interaction_event_history`

Database location:

`data/customer360.db`

The `pipeline_run_history` table records unique logical pipeline runs, including their run ID, recorded timestamp, and dataset record counts. Reprocessing identical input does not create another history entry for the same run ID.

The `interaction_event_history` table preserves the first-seen version of each interaction event. Duplicate events are not inserted again. If an existing interaction ID is encountered with different event details, the pipeline raises a conflict instead of silently overwriting the original event.

The current-state tables are replaced with the latest processed datasets during a successful run. Full historical snapshots of all customer, account, and order records, and versioned interaction changes, are not implemented.

## 11. Reconciliation

The reconciliation layer performs 16 automated checks, including:

- Source-to-valid-and-rejected record reconciliation.
- Merged customer count reconciliation.
- Database record count verification.
- Customer 360 record count verification.
- Order amount reconciliation.
- Foreign key integrity checks.
- Customer-level aggregation checks.

The results are saved to:

`outputs/reconciliation_report.json`

The successful pipeline execution completed all 16 reconciliation checks.

## 12. Performance Benchmark

A benchmark was conducted using 15,000 customers and 120,295 total records.

### Before and After Optimization

| Metric | Before | After |
|---|---:|---:|
| Total records | 120,295 | 120,295 |
| Validation time | 63.03 sec | 0.33 sec |
| Generation time | 14.70 sec | 14.61 sec |
| Transformation time | 1.18 sec | 1.19 sec |
| Total execution time | 78.91 sec | 16.14 sec |

### Optimization

The original validation implementation relied heavily on row-by-row processing using Pandas `iterrows()`.

It was optimized using vectorized Pandas operations such as:

- `isna()`
- `duplicated()`
- `isin()`
- `to_datetime()`

This reduced validation time significantly. Actual benchmark results may vary depending on the execution environment.

Benchmark details are available in `outputs/performance_benchmark.json`.

## 13. Project Structure

```text
customer-360-data-engineering-pipeline/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── quarantine/
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── design_decisions.md
│
├── outputs/
│   ├── customer_identity_mapping.csv
│   ├── identity_manual_review.csv
│   ├── performance_benchmark.json
│   ├── pipeline.log
│   ├── reconciliation_report.json
│   └── run_summary.json
│
├── src/
│   ├── data_generator.py
│   ├── generate_raw_data.py
│   ├── ingestion.py
│   ├── validation.py
│   ├── identity_resolution.py
│   ├── customer_360.py
│   ├── publishing.py
│   ├── storage.py
│   ├── reconciliation.py
│   └── schemas.py
│
├── tests/
│   ├── test_validation.py
│   ├── test_ingestion.py
│   ├── test_pipeline_failure.py
│   ├── test_identity_resolution.py
│   ├── test_identity_integration.py
│   └── test_storage_history.py
│
├── main.py
├── benchmark.py
├── requirements.txt
└── README.md
```

## 14. Setup and Execution

### Prerequisites

- Python 3.10 or later.
- pip.

### Step 1: Clone the repository

```bash
git clone https://github.com/venkatamanidurgagottimukkala-hub/customer-360-data-engineering-pipeline.git
cd customer-360-data-engineering-pipeline
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Generate raw datasets

```bash
python -m src.generate_raw_data
```

This generates the four synthetic CSV datasets in `data/raw/`. Running this command again regenerates those input files.

### Step 5: Execute the pipeline

```bash
python main.py
```

The pipeline processes the source datasets, resolves customer identities, generates the Customer 360 output, stores the results in SQLite, and performs reconciliation.

### Step 6: Run automated tests

```bash
python -m pytest -v
```

### Step 7: Run the performance benchmark

```bash
python benchmark.py
```

## 15. Execution Outputs

The pipeline generates the following outputs:

| Output | Description |
|---|---|
| `data/processed/` | Validated and processed datasets |
| `data/quarantine/` | Rejected records with rejection reasons |
| `data/customer360.db` | SQLite database |
| `outputs/run_summary.json` | Pipeline execution summary and metrics |
| `outputs/reconciliation_report.json` | Reconciliation results |
| `outputs/customer_identity_mapping.csv` | Customer identity mapping |
| `outputs/identity_manual_review.csv` | Potential identity conflicts |
| `outputs/pipeline.log` | Pipeline execution logs |
| `outputs/performance_benchmark.json` | Benchmark results |

## 16. Test Results

The project includes automated tests covering:

- Data validation.
- Data ingestion.
- Pipeline failure handling.
- Customer identity resolution.
- Identity resolution integration with dependent datasets.
- Interaction event history and database transaction handling.

The latest full test execution completed successfully with **27 passed tests**.

---

## Design and Implementation Documentation

- [Architecture](docs/architecture.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Design Decisions](docs/design_decisions.md)