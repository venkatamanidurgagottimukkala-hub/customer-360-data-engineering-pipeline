# Customer 360 Data Engineering Pipeline - Design Decisions

## 1. Overview

This document explains the technical decisions, implementation approaches, assumptions and trade-offs made while developing the Customer 360 Data Engineering Pipeline.

The objective is to build a reproducible, scalable and testable data processing solution that integrates multiple customer-related datasets into a unified Customer 360 view.

The pipeline processes customer, account, order and interaction datasets, validates their quality, resolves duplicate customer identities and produces consolidated customer information.

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

SQLite was selected because:
- It requires no separate database server.
- It supports SQL queries and relational data.
- It is lightweight and suitable for a self-contained project.
- It simplifies local development and testing.

### Faker

Faker was selected to generate realistic synthetic customer information without using actual customer data.

### Pytest

Pytest was selected to automate validation, ingestion, pipeline failure and identity-resolution tests.

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

## 5. Customer Identity Resolution

Customer identity resolution is implemented to identify duplicate customer records using normalized email addresses and phone numbers.

### Normalization

Before comparison:
- Email addresses are converted to lowercase and whitespace is removed.
- Phone numbers are normalized by removing formatting characters.
- Supported Indian country-code prefixes are handled during phone normalization.

### Matching Rules

The implementation follows deterministic matching rules:

1. **Same normalized email and phone:** Records are automatically matched.
2. **Same email but different phone:** Records are flagged for manual review.
3. **Same phone but different email:** Records are flagged for manual review.
4. **Similar names alone:** Names are not sufficient to automatically merge customer records.
5. **Missing email or phone:** Records without both usable identifiers are not automatically merged.

### Canonical Customer Selection

When duplicate identities are detected, the lexicographically smallest customer ID is selected as the canonical customer ID.

This ensures deterministic identity resolution.

### Foreign Key Mapping

After resolving customer identities, account, order and interaction records are mapped to their corresponding canonical customer IDs.

This ensures that related records remain associated with the resolved customer during downstream validation and Customer 360 transformation.

### Identity Resolution Outputs

The pipeline produces:

- `outputs/customer_identity_mapping.csv` - maps original customer IDs to canonical customer IDs.
- `outputs/identity_manual_review.csv` - identifies uncertain identity matches requiring manual review.

This approach avoids aggressive matching and reduces the risk of incorrectly merging different customers.

## 6. Customer 360 Transformation

The Customer 360 dataset is created by aggregating account, order and interaction information at customer-level.

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

## 7. Idempotency and Run Identification

A deterministic run ID is generated using the SHA-256 hashing algorithm.

The hash is calculated using the contents of the source CSV files.

If the source files remain unchanged, the generated run ID remains the same.

Published CSV files are overwritten rather than appended, preventing duplicate records when the same input is processed repeatedly.

The current-state SQLite tables are replaced with the latest processed dataset state.

Two additional history tables preserve selected historical information:

- `pipeline_run_history` records unique logical pipeline runs using their deterministic run IDs.
- `interaction_event_history` preserves the first-seen version of each interaction event.

Repeated processing of identical input does not create duplicate logical run-history entries or duplicate interaction events.

This provides limited history tracking, rather than full historical snapshots of every dataset.

## 8. Data Lineage

The published source datasets include:

- `run_id`
- `source_file`

These fields help identify the source execution and original input file associated with each published record.

Rejected datasets additionally include `rejection_reason` to explain why a record was excluded.

Identity mapping and manual-review outputs provide traceability between original and canonical customer IDs.

The Customer 360 output is currently published separately and does not include the same source-level lineage columns.

## 9. Failure Handling and Observability

Python logging is used to record pipeline execution stages.

The pipeline records:

- Execution start and end times.
- Processing duration.
- Pipeline status.
- Input record counts.
- Processed record counts.
- Rejected record counts.
- Run ID.
- Identity-resolution metrics.
- Reconciliation status.
- Failure reason.

The execution summary is stored in:

`outputs/run_summary.json`

Pipeline logs are stored in:

`outputs/pipeline.log`

Exceptions are logged and re-raised so that failures are visible to the caller.

An automated failure test verifies that a simulated ingestion failure stops execution before database storage.

## 10. Reconciliation Strategy

Reconciliation checks are performed after database storage.

The implementation currently performs 16 checks covering:

- Source, valid and rejected record counts.
- Customer identity merge adjustments.
- Database record counts.
- Customer 360 record count.
- Order