from pathlib import Path
import pandas as pd

from src.schemas import (
    CUSTOMER_COLUMNS,
    ACCOUNT_COLUMNS,
    ORDER_COLUMNS,
    INTERACTION_COLUMNS
)


# Define the raw data directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


# Expected columns for each dataset
EXPECTED_SCHEMAS = {
    "customers": CUSTOMER_COLUMNS,
    "accounts": ACCOUNT_COLUMNS,
    "orders": ORDER_COLUMNS,
    "interactions": INTERACTION_COLUMNS
}


# Read and validate one CSV file
def load_csv(file_path, expected_columns):

    # Check whether the file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    # Read the CSV file
    df = pd.read_csv(file_path)

    # Check for missing or unexpected columns
    actual_columns = list(df.columns)

    if actual_columns != expected_columns:

        missing_columns = [
            column for column in expected_columns
            if column not in actual_columns
        ]

        unexpected_columns = [
            column for column in actual_columns
            if column not in expected_columns
        ]

        raise ValueError(
            f"Schema mismatch in {file_path.name}. "
            f"Missing columns: {missing_columns}. "
            f"Unexpected columns: {unexpected_columns}."
        )

    return df


# Load all four source datasets
def load_all_sources():

    datasets = {}

    for dataset_name, expected_columns in EXPECTED_SCHEMAS.items():

        file_path = RAW_DATA_DIR / f"{dataset_name}.csv"

        datasets[dataset_name] = load_csv(
            file_path,
            expected_columns
        )

        print(
            f"Loaded {dataset_name}: "
            f"{len(datasets[dataset_name])} records"
        )

    return datasets