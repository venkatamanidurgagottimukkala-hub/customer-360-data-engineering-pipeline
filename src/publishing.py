from pathlib import Path
import hashlib

import pandas as pd


# Define project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"


# Source file names
SOURCE_FILES = {
    "customers": "customers.csv",
    "accounts": "accounts.csv",
    "orders": "orders.csv",
    "interactions": "interactions.csv"
}


# Generate a deterministic pipeline run ID
def generate_run_id():

    hasher = hashlib.sha256()

    for dataset_name in sorted(SOURCE_FILES):

        file_path = RAW_DATA_DIR / SOURCE_FILES[dataset_name]

        if not file_path.exists():
            raise FileNotFoundError(
                f"Source file not found: {file_path}"
            )

        with open(file_path, "rb") as file:

            hasher.update(file.read())

    return hasher.hexdigest()[:16]


# Publish valid and rejected datasets
def publish_datasets(validated_data, rejected_data):

    # Create output directories
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a run ID
    run_id = generate_run_id()

    print("PIPELINE RUN ID:", run_id)

    # Store publishing statistics
    summary = {}

    # Process all four datasets
    for dataset_name in SOURCE_FILES:

        source_file = SOURCE_FILES[dataset_name]

        # Prepare valid records
        valid_df = validated_data[dataset_name].copy()

        valid_df["run_id"] = run_id

        valid_df["source_file"] = source_file

        # Prepare rejected records
        rejected_df = rejected_data[dataset_name].copy()

        rejected_df["run_id"] = run_id

        rejected_df["source_file"] = source_file

        # Save processed records
        processed_path = (
            PROCESSED_DIR / f"{dataset_name}.csv"
        )

        valid_df.to_csv(
            processed_path,
            index=False
        )

        # Save rejected records
        quarantine_path = (
            QUARANTINE_DIR / f"{dataset_name}_rejected.csv"
        )

        rejected_df.to_csv(
            quarantine_path,
            index=False
        )

        # Store record counts
        summary[dataset_name] = {
            "processed": len(valid_df),
            "rejected": len(rejected_df)
        }

        print(
            f"{dataset_name}: "
            f"Processed={len(valid_df)}, "
            f"Rejected={len(rejected_df)}"
        )

    return run_id, summary