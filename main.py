import json
import logging
import pandas as pd

from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter

from src.ingestion import load_all_sources
from src.validation import validate_dataset
from src.identity_resolution import resolve_customer_identities
from src.publishing import publish_datasets
from src.customer_360 import build_customer_360
from src.storage import save_to_database
from src.reconciliation import run_reconciliation


# Define project directories
PROJECT_ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = PROJECT_ROOT / "outputs"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Configure logging
LOG_FILE = OUTPUT_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger("customer360")


# Main pipeline execution
def main():

    start_time = datetime.now(timezone.utc)

    start_counter = perf_counter()

    # Initialize execution metrics
    metrics = {
        "status": "RUNNING",
        "start_time": start_time.isoformat(),
        "end_time": None,
        "duration_seconds": None,
        "run_id": None,
        "input_counts": {},
        "processed_counts": {},
        "rejected_counts": {},
        "identity_resolution": {},
        "reconciliation_status": None,
        "reconciliation_checks": 0,
        "failure_reason": None
    }

    logger.info("CUSTOMER 360 PIPELINE STARTED")

    try:

        # STEP 1: INGESTION
        logger.info("Starting source data ingestion")

        datasets = load_all_sources()

        for name, df in datasets.items():

            metrics["input_counts"][name] = len(df)

        logger.info("Source data ingestion completed")

        # STEP 2: CUSTOMER VALIDATION
        logger.info("Starting customer validation")

        valid_customers, rejected_customers = validate_dataset(
            "customers",
            datasets["customers"]
        )

        logger.info(
            "Valid customers: %s | Rejected customers: %s",
            len(valid_customers),
            len(rejected_customers)
        )

        # STEP 3: CUSTOMER IDENTITY RESOLUTION
        logger.info("Starting customer identity resolution")

        (
            resolved_customers,
            customer_mapping,
            manual_review
        ) = resolve_customer_identities(valid_customers)

        # Calculate merged customer count
        merged_customer_count = (
            len(valid_customers) - len(resolved_customers)
        )

        # Replace original customer ID with canonical customer ID
        resolved_customers["customer_id"] = (
            resolved_customers["canonical_customer_id"]
        )

        resolved_customers = resolved_customers.drop(
            columns=["canonical_customer_id"]
        )

        logger.info(
            "Identity resolution completed | "
            "Original valid customers: %s | "
            "Resolved customers: %s | "
            "Merged customers: %s | "
            "Manual review pairs: %s",
            len(valid_customers),
            len(resolved_customers),
            merged_customer_count,
            len(manual_review)
        )

        # STEP 4: CREATE CUSTOMER ID LOOKUP
        customer_id_mapping = dict(
            zip(
                customer_mapping["original_customer_id"],
                customer_mapping["canonical_customer_id"]
            )
        )

        # STEP 5: UPDATE CHILD DATASET CUSTOMER IDs
        logger.info("Updating child dataset customer references")

        child_datasets = {}

        for dataset_name in [
            "accounts",
            "orders",
            "interactions"
        ]:

            child_df = datasets[dataset_name].copy()

            child_df["customer_id"] = child_df["customer_id"].map(
                lambda customer_id: customer_id_mapping.get(
                    str(customer_id),
                    customer_id
                ) if pd.notna(customer_id) else customer_id
            )

            child_datasets[dataset_name] = child_df

        # STEP 6: VALIDATE ALL CHILD DATASETS
        logger.info("Starting child dataset validation")

        validated_data = {
            "customers": resolved_customers
        }

        rejected_data = {
            "customers": rejected_customers
        }

        for dataset_name in [
            "accounts",
            "orders",
            "interactions"
        ]:

            valid_df, rejected_df = validate_dataset(
                dataset_name,
                child_datasets[dataset_name],
                customers=resolved_customers
            )

            validated_data[dataset_name] = valid_df

            rejected_data[dataset_name] = rejected_df

            logger.info(
                "%s | Valid: %s | Rejected: %s",
                dataset_name,
                len(valid_df),
                len(rejected_df)
            )

        # STEP 7: BUILD CUSTOMER 360
        logger.info("Building Customer 360 dataset")

        customer_360 = build_customer_360(
            validated_data
        )

        customer_360_path = (
            PROCESSED_DIR / "customer_360.csv"
        )

        customer_360.to_csv(
            customer_360_path,
            index=False
        )

        logger.info(
            "Customer 360 dataset created with %s customers",
            len(customer_360)
        )

        # STEP 8: PUBLISH CSV DATASETS
        logger.info("Starting data publishing")

        run_id, summary = publish_datasets(
            validated_data,
            rejected_data
        )

        metrics["run_id"] = run_id

        for name, counts in summary.items():

            metrics["processed_counts"][name] = counts["processed"]

            metrics["rejected_counts"][name] = counts["rejected"]

        # STEP 9: SAVE IDENTITY RESOLUTION REPORTS
        customer_mapping["run_id"] = run_id

        manual_review["run_id"] = run_id

        customer_mapping.to_csv(
            OUTPUT_DIR / "customer_identity_mapping.csv",
            index=False
        )

        manual_review.to_csv(
            OUTPUT_DIR / "identity_manual_review.csv",
            index=False
        )

        metrics["identity_resolution"] = {
            "original_valid_customers": len(valid_customers),
            "resolved_customers": len(resolved_customers),
            "merged_customers": merged_customer_count,
            "manual_review_pairs": len(manual_review)
        }

        logger.info("Identity resolution reports saved")

        logger.info("CSV publishing completed")

        # STEP 10: SAVE DATA INTO SQLITE
        logger.info("Starting SQLite database storage")

        database_path = save_to_database(
            validated_data,
            customer_360
        )

        logger.info(
            "SQLite database updated: %s",
            database_path
        )

        # STEP 11: RUN RECONCILIATION
        logger.info("Starting reconciliation checks")

        identity_summary = {
            "merged_customers": merged_customer_count
        }

        reconciliation_report = run_reconciliation(
            datasets,
            validated_data,
            rejected_data,
            customer_360,
            identity_summary=identity_summary
        )

        metrics["reconciliation_status"] = (
            reconciliation_report["overall_status"]
        )

        metrics["reconciliation_checks"] = (
            reconciliation_report["total_checks"]
        )

        if reconciliation_report["overall_status"] != "PASS":

            raise RuntimeError(
                "Reconciliation failed. Check reconciliation_report.json"
            )

        logger.info(
            "Reconciliation completed: %s checks passed",
            reconciliation_report["passed_checks"]
        )

        # Mark pipeline successful
        metrics["status"] = "SUCCESS"

        logger.info(
            "CUSTOMER 360 PIPELINE COMPLETED SUCCESSFULLY"
        )

    except Exception as error:

        metrics["status"] = "FAILED"

        metrics["failure_reason"] = str(error)

        logger.exception("CUSTOMER 360 PIPELINE FAILED")

        raise

    finally:

        # Calculate execution duration
        end_time = datetime.now(timezone.utc)

        metrics["end_time"] = end_time.isoformat()

        metrics["duration_seconds"] = round(
            perf_counter() - start_counter,
            4
        )

        # Save execution summary
        summary_file = OUTPUT_DIR / "run_summary.json"

        with open(summary_file, "w", encoding="utf-8") as file:

            json.dump(
                metrics,
                file,
                indent=4
            )

        logger.info(
            "Pipeline execution duration: %s seconds",
            metrics["duration_seconds"]
        )

        logger.info(
            "Execution summary saved to %s",
            summary_file
        )


# Execute the pipeline
if __name__ == "__main__":

    main()