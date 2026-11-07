# Customer 360 Data Engineering Pipeline

## 1. Project Overview

The Customer 360 Data Engineering Pipeline is a Python-based data engineering solution that integrates customer, account, order and interaction datasets into a unified Customer 360 view.

The pipeline performs source data ingestion, data validation, transformation, publishing, SQLite storage and reconciliation.

It is designed to support reliable data processing through deterministic data generation, duplicate detection, data quality checks, run tracking and automated testing.

## 2. Key Features

- Synthetic data generation using Faker and Pandas.
- Ingestion of multiple CSV source datasets.
- Schema validation and data quality checks.
- Duplicate primary key detection.
- Foreign key integrity validation.
- Date and business rule validation.
- Rejected record quarantine with rejection reasons.
- Unified Customer 360 transformation.
- Deterministic pipeline run identification.
- SQLite database storage.
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

Source Data Generation  
↓  
Raw CSV Datasets  
↓  
Data Ingestion  
↓  
Schema Validation  
↓  
Data Quality Validation  
↓  
Valid Records / Rejected Records  
↓  
Customer 360 Transformation  
↓  
CSV Publishing and SQLite Storage  
↓  
Data Reconciliation  
↓  
Execution Reports

## 5. Source Datasets

The pipeline processes four source datasets.

### Customers
Contains customer identity and contact information.

### Accounts
Contains customer account information, account types and account statuses.

### Orders
Contains product information, order amounts, order statuses and order dates.

### Interactions
Contains customer communication and interaction history.

## 6. Customer 360 Output

The unified Customer 360 dataset contains:

- Customer identification and contact details.
- Total account count.
- Active account count.
- Total order count.
- Total order amount.
- Latest order date.
- Total interaction count.
- Latest interaction date.

The transformation uses customer-level aggregation and left joins to retain customers even when they have no orders or interactions.

## 7. Data Quality and Validation

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

## 8. Idempotency and Traceability

The pipeline generates a deterministic run ID using SHA-256 hashing of the source CSV files.

The run ID and source filename are added to the published source datasets.

Repeated processing of unchanged input produces the same run ID and replaces the current output datasets rather than appending duplicate records.

## 9. Database Storage

The pipeline stores five tables in SQLite:

- customers
- accounts
- orders
- interactions
- customer_360

Database location:

`data/customer360.db`

## 10. Reconciliation

The reconciliation layer performs 16 automated checks, including:

- Source-to-valid-and-rejected record reconciliation.
- Database record count verification.
- Customer 360 record count verification.
- Order amount reconciliation.
- Foreign key integrity checks.
- Customer-level aggregation checks.

The results are saved to:

`outputs/reconciliation_report.json`

## 11. Performance Benchmark

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
- `to_numeric()`

**Result:** Validation became approximately 191 times faster, reducing validation execution time by approximately 99.48%.

Benchmark results are saved in:

`outputs/performance_benchmark.json`

## 12. Automated Testing

The project uses Pytest for automated testing.

Run the complete test suite:

```bash
python -m pytest -v
```

Current test results:

- Total tests: 16
- Passed: 16
- Failed: 0

The tests cover ingestion, schema validation, data quality rules and pipeline failure handling.

## 13. Project Setup

### Prerequisites

- Python 3.14 or compatible Python version.
- Git.
- PowerShell or terminal.

### Step 1: Clone the repository

```bash
git clone <your-github-repository-url>
```

### Step 2: Navigate to the project

```bash
cd <project-folder>
```

### Step 3: Create a virtual environment

```bash
python -m venv .venv
```

### Step 4: Activate the environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 5: Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 14. Running the Pipeline

### Generate raw datasets

```bash
python -m src.generate_raw_data
```

### Execute the complete pipeline

```bash
python main.py
```

### Run automated tests

```bash
python -m pytest -v
```

### Run the performance benchmark

```bash
python benchmark.py
```

## 15. Output Files

| Location | Description |
|---|---|
| `data/raw/` | Raw source CSV datasets |
| `data/processed/` | Validated and transformed datasets |
| `data/quarantine/` | Rejected records and rejection reasons |
| `data/customer360.db` | SQLite database |
| `outputs/pipeline.log` | Pipeline execution logs |
| `outputs/run_summary.json` | Pipeline execution summary |
| `outputs/reconciliation_report.json` | Reconciliation results |
| `outputs/performance_benchmark.json` | Benchmark results |

## 16. Design Considerations and Limitations

- Duplicate primary keys are handled deterministically by retaining the first occurrence and rejecting subsequent occurrences.
- Records with invalid customer references are rejected rather than incorrectly associated with another customer.
- The current implementation uses exact customer identifiers for relationship validation; fuzzy identity matching is not implemented.
- The SQLite tables represent the latest successful dataset state rather than a historical snapshot archive.
- Recovery testing currently verifies that an ingestion failure prevents database storage and that a subsequent successful run can complete.
- The current pipeline is designed as a reproducible local data engineering implementation.

## 17. Project Outcome

The project successfully demonstrates an end-to-end Customer 360 data engineering workflow.

Key verified results:

- 120,295 records processed in the performance benchmark.
- 15,000 unified Customer 360 records generated.
- 16 automated tests passed.
- 16 reconciliation checks passed.
- Approximately 191x faster validation after optimization.
- Successful execution of the integrated pipeline.