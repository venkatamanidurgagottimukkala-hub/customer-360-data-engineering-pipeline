import sqlite3

import pandas as pd
import pytest

from src import storage


# Create sample interaction records
def create_interactions(records):

    return pd.DataFrame(
        records,
        columns=[
            "interaction_id",
            "customer_id",
            "interaction_type",
            "description",
            "interaction_date"
        ]
    )


# Create all required datasets
def create_validated_data(interactions):

    return {
        "customers": pd.DataFrame(
            columns=[
                "customer_id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "created_at"
            ]
        ),
        "accounts": pd.DataFrame(
            columns=[
                "account_id",
                "customer_id",
                "account_type",
                "status",
                "created_at"
            ]
        ),
        "orders": pd.DataFrame(
            columns=[
                "order_id",
                "customer_id",
                "product_name",
                "amount",
                "order_status",
                "order_date"
            ]
        ),
        "interactions": interactions
    }


# Read the number of records in a database table
def get_record_count(database_path, table_name):

    with sqlite3.connect(database_path) as connection:

        return connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]


# Test 1: Identical events must not be duplicated
def test_duplicate_event_is_not_inserted(tmp_path, monkeypatch):

    database_path = tmp_path / "test.db"

    monkeypatch.setattr(storage, "DB_PATH", database_path)

    interactions = create_interactions([
        (
            "INT001",
            "CUST001",
            "Call",
            "Customer requested assistance",
            "2026-11-07T10:00:00"
        )
    ])

    validated_data = create_validated_data(interactions)

    customer_360 = pd.DataFrame(
    columns=[
        "customer_id",
        "account_count",
        "active_account_count",
        "order_count",
        "total_order_amount",
        "interaction_count"
    ]
)

    # First save
    storage.save_to_database(
        validated_data,
        customer_360,
        "RUN001"
    )

    # Save the identical event again
    storage.save_to_database(
        validated_data,
        customer_360,
        "RUN001"
    )

    assert get_record_count(
        database_path,
        "interaction_event_history"
    ) == 1

    assert get_record_count(
        database_path,
        "pipeline_run_history"
    ) == 1


# Test 2: A new run should be recorded without duplicating events
def test_new_run_preserves_existing_events(tmp_path, monkeypatch):

    database_path = tmp_path / "test.db"

    monkeypatch.setattr(storage, "DB_PATH", database_path)

    interactions = create_interactions([
        (
            "INT001",
            "CUST001",
            "Call",
            "Customer requested assistance",
            "2026-11-07T10:00:00"
        )
    ])

    validated_data = create_validated_data(interactions)

    customer_360 = pd.DataFrame(
    columns=[
        "customer_id",
        "account_count",
        "active_account_count",
        "order_count",
        "total_order_amount",
        "interaction_count"
    ]
)

    # First pipeline run
    storage.save_to_database(
        validated_data,
        customer_360,
        "RUN001"
    )

    # Second pipeline run with the same event
    storage.save_to_database(
        validated_data,
        customer_360,
        "RUN002"
    )

    assert get_record_count(
        database_path,
        "pipeline_run_history"
    ) == 2

    assert get_record_count(
        database_path,
        "interaction_event_history"
    ) == 1


# Test 3: Changed event details must raise an error
def test_changed_event_details_raise_conflict(tmp_path, monkeypatch):

    database_path = tmp_path / "test.db"

    monkeypatch.setattr(storage, "DB_PATH", database_path)

    original_interactions = create_interactions([
        (
            "INT001",
            "CUST001",
            "Call",
            "Original interaction",
            "2026-11-07T10:00:00"
        )
    ])

    original_data = create_validated_data(
        original_interactions
    )

    customer_360 = pd.DataFrame(
    columns=[
        "customer_id",
        "account_count",
        "active_account_count",
        "order_count",
        "total_order_amount",
        "interaction_count"
    ]
)

    storage.save_to_database(
        original_data,
        customer_360,
        "RUN001"
    )

    changed_interactions = create_interactions([
        (
            "INT001",
            "CUST001",
            "Email",
            "Changed interaction",
            "2026-11-07T11:00:00"
        )
    ])

    changed_data = create_validated_data(
        changed_interactions
    )

    with pytest.raises(
        ValueError,
        match="Interaction history conflict"
    ):

        storage.save_to_database(
            changed_data,
            customer_360,
            "RUN002"
        )

    # Original event must remain unchanged
    with sqlite3.connect(database_path) as connection:

        event = connection.execute(
            """
            SELECT interaction_type, description
            FROM interaction_event_history
            WHERE interaction_id = ?
            """,
            ("INT001",)
        ).fetchone()

    assert event == (
        "Call",
        "Original interaction"
    )

    # Failed run must not be recorded
    assert get_record_count(
        database_path,
        "pipeline_run_history"
    ) == 1


# Test 4: A failed write must roll back earlier inserts
def test_failed_history_write_rolls_back_new_events(
    tmp_path,
    monkeypatch
):

    database_path = tmp_path / "test.db"

    monkeypatch.setattr(storage, "DB_PATH", database_path)

    original_interactions = create_interactions([
        (
            "INT001",
            "CUST001",
            "Call",
            "Original interaction",
            "2026-11-07T10:00:00"
        )
    ])

    original_data = create_validated_data(
        original_interactions
    )

    customer_360 = pd.DataFrame(
    columns=[
        "customer_id",
        "account_count",
        "active_account_count",
        "order_count",
        "total_order_amount",
        "interaction_count"
    ]
)

    storage.save_to_database(
        original_data,
        customer_360,
        "RUN001"
    )

    # First event is new.
    # Second event conflicts with the existing INT001.
    interactions_with_conflict = create_interactions([
        (
            "INT002",
            "CUST002",
            "Email",
            "New interaction",
            "2026-11-07T12:00:00"
        ),
        (
            "INT001",
            "CUST001",
            "Email",
            "Changed existing interaction",
            "2026-11-07T13:00:00"
        )
    ])

    conflicting_data = create_validated_data(
        interactions_with_conflict
    )

    with pytest.raises(
        ValueError,
        match="Interaction history conflict"
    ):

        storage.save_to_database(
            conflicting_data,
            customer_360,
            "RUN002"
        )

    # INT002 must have been rolled back
    assert get_record_count(
        database_path,
        "interaction_event_history"
    ) == 1

    # Only the original run should exist
    assert get_record_count(
        database_path,
        "pipeline_run_history"
    ) == 1