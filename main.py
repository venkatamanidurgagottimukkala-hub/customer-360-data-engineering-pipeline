import json
import logging

from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter

from src.ingestion import load_all_sources
from src.validation import validate_all_datasets
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

        # STEP 2: VALIDATION
        logger.info("Starting data validation")

        valid, rejected = validate_all_datasets(datasets)

        logger.info("Data validation completed")

        # STEP 3: BUILD CUSTOMER 360
        logger.info("Building Customer 360 dataset")

        customer_360 = build_customer_360(valid)

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

        # STEP 4: PUBLISH CSV DATASETS
        logger.info("Starting data publishing")

        run_id, summary = publish_datasets(
            valid,
            rejected
        )

        metrics["run_id"] = run_id

        for name, counts in summary.items():

            metrics["processed_counts"][name] = counts["processed"]

            metrics["rejected_counts"][name] = counts["rejected"]

        logger.info("CSV publishing completed")

        # STEP 5: SAVE DATA INTO SQLITE
        logger.info("Starting SQLite database storage")

        database_path = save_to_database(
            valid,
            customer_360
        )

        logger.info(
            "SQLite database updated: %s",
            database_path
        )

        # STEP 6: RUN RECONCILIATION
        logger.info("Starting reconciliation checks")

        reconciliation_report = run_reconciliation(
            datasets,
            valid,
            rejected,
            customer_360
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

        logger.info("CUSTOMER 360 PIPELINE COMPLETED SUCCESSFULLY")

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