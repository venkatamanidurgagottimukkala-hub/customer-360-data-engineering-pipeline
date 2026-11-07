# Customer 360 Data Engineering Pipeline — Design Decisions

## 1. Overview

This document explains the technical decisions, implementation approaches, assumptions and trade-offs made while developing the Customer 360 Data Engineering Pipeline.

The objective was to build a reproducible, scalable and testable data processing solution that integrates multiple customer-related datasets into a unified Customer 360 view.

## 2. Technology Selection

### Python

Python was selected as the primary programming language because of its data engineering capabilities, extensive libraries and readability.

### Pandas

Pandas was selected for:
- CSV ingestion and processing.
- Data validation.
- Data transformation.
- Aggregation and joining datasets.
- Vectorized data processing.

### SQLite

SQLite was selected as the database because:
- It requires no separate database server.
- It supports SQL queries and relational data.
- It is lightweight and suitable for a self-contained project.
- It simplifies local development and testing.

### Faker

Faker was selected to generate realistic synthetic customer information without using actual customer data.

### Pytest

Pytest was selected to automate validation, ingestion and pipeline failure tests.

## 3. Synthetic Data Generation

The pipeline generates four datasets:

- Customers
- Accounts
- Orders
- Interactions

A fixed random seed is used to support reproducible data generation.

Deterministic identifiers are generated for primary keys.

The benchmark generated 120,295 records using 15,000 customers.

Synthetic data allows the pipeline to be tested at different volumes without exposing personal or confidential customer information.

## 4. Data Validation Strategy

The validation layer checks data quality before publishing records.

The implemented checks include:

- Missing values.
- Duplicate primary keys.
- Invalid foreign key references.
- Invalid date values.
- Records dated before customer creation.
- Non-positive or malformed order amounts.
- Invalid categorical values.

Records passing validation are sent to downstream processing.

Rejected records are separated into quarantine CSV files with explanations of the validation failures.

### Duplicate Handling

The first occurrence of a primary key is retained.

Subsequent occurrences of the same primary key are rejected.

This provides deterministic duplicate handling.

### Referential Integrity

Accounts, orders and interactions must reference an existing valid customer.

Records with invalid customer references are rejected rather than incorrectly associated with another customer.

## 5. Customer 360 Transformation

The Customer 360 dataset is created by aggregating account, order and interaction information at customer level.

The transformation calculates:

- Total accounts.
- Active accounts.
- Total orders.
- Total order amount.
- Latest order date.
- Total interactions.
- Latest interaction date.

Left joins are used to preserve customers even when they have no related orders or interactions.

For customers without orders or interactions, counts are set to zero and the corresponding latest event dates remain null.

## 6. Idempotency and Run Identification

A deterministic run ID is generated using the SHA-256 hashing algorithm.

The hash is calculated using the contents of the source CSV files.

If the source files remain unchanged, the generated run ID remains the same.

Published CSV files are overwritten rather than appended, preventing duplicate records when the same input is processed repeatedly.

The current SQLite implementation also replaces existing tables with the latest dataset state.

This supports repeatable execution but does not maintain historical snapshots.

## 7. Data Lineage

The published source datasets include:

- `run_id`
- `source_file`

These fields help identify the source execution and original input file associated with each published record.

Rejected datasets also include `rejection_reason` to explain why a record was excluded.

## 8. Failure Handling and Observability

Python logging is used to record pipeline execution stages.

The pipeline records:
- Execution start and end times.
- Processing duration.
- Pipeline status.
- Input record counts.
- Processed record counts.
- Rejected record counts.
- Run ID.
- Reconciliation status.
- Failure reason.

The execution summary is stored in:

`outputs/run_summary.json`

Pipeline logs are stored in:

`outputs/pipeline.log`

Exceptions are logged and re-raised so that failures are visible to the caller.

An automated failure test verifies that a simulated ingestion failure stops execution before database storage.

A subsequent successful execution verifies recovery from that early-stage failure.

## 9. Reconciliation Strategy

Reconciliation checks are performed after database storage.

The implementation currently performs 16 checks covering:

- Source, valid and rejected record counts.
- Database record counts.
- Customer 360 record count.
- Order amount totals.
- Foreign key integrity.
- Customer-level account counts.
- Customer-level order counts.
- Customer-level interaction counts.

The reconciliation report is saved as JSON.

The pipeline is marked successful only when all reconciliation checks pass.

## 10. Performance Optimization

The initial validation implementation used row-by-row processing through Pandas `iterrows()`.

Benchmarking identified validation as the main performance bottleneck.

The validation implementation was optimized using vectorized Pandas operations, including:

- `isna()`
- `duplicated()`
- `isin()`
- `to_datetime()`
- `to_numeric()`

### Benchmark Comparison

| Metric | Before | After |
|---|---:|---:|
| Records processed | 120,295 | 120,295 |
| Validation time | 63.03 seconds | 0.33 seconds |
| Total execution time | 78.91 seconds | 16.14 seconds |

The optimization reduced validation time by approximately 99.48%, achieving approximately 191 times faster validation in the measured benchmark.

All 16 automated tests continued to pass after the optimization.

## 11. Testing Strategy

Pytest is used to verify important pipeline behaviours.

Current automated coverage includes:

- Valid schema acceptance.
- Missing and unexpected schema columns.
- Missing source files.
- Duplicate primary keys.
- Missing values.
- Invalid customer references.
- Invalid dates.
- Invalid order amounts.
- Invalid categorical values.
- Empty customer datasets.
- Records before customer creation.
- Pipeline failure before database storage.

Current test result:

**16 passed, 0 failed.**

## 12. Assumptions and Trade-offs

### Customer Identity

The implementation uses