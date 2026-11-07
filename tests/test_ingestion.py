import pandas as pd
import pytest

from src.ingestion import load_csv


EXPECTED_COLUMNS = [
    "customer_id",
    "first_name",
    "last_name",
    "email",
    "phone",
    "created_at"
]


def test_valid_schema_accepted(tmp_path):

    file_path = tmp_path / "customers.csv"

    df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    df.to_csv(file_path, index=False)

    result = load_csv(file_path, EXPECTED_COLUMNS)

    assert list(result.columns) == EXPECTED_COLUMNS


def test_unexpected_column_rejected(tmp_path):

    file_path = tmp_path / "customers.csv"

    columns = EXPECTED_COLUMNS + ["city"]

    df = pd.DataFrame(columns=columns)

    df.to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Schema mismatch"):

        load_csv(file_path, EXPECTED_COLUMNS)


def test_missing_column_rejected(tmp_path):

    file_path = tmp_path / "customers.csv"

    columns = EXPECTED_COLUMNS[:-1]

    df = pd.DataFrame(columns=columns)

    df.to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Schema mismatch"):

        load_csv(file_path, EXPECTED_COLUMNS)


def test_missing_source_file_rejected(tmp_path):

    file_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):

        load_csv(file_path, EXPECTED_COLUMNS)