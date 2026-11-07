import pandas as pd
import pytest

from src.validation import validate_dataset


@pytest.fixture
def sample_customers():

    return pd.DataFrame([
        {
            "customer_id": "CUST000001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2026-01-01T10:00:00"
        }
    ])


def test_duplicate_customer_rejected(sample_customers):

    customers = pd.concat(
        [sample_customers, sample_customers],
        ignore_index=True
    )

    valid, rejected = validate_dataset(
        "customers",
        customers
    )

    assert len(valid) == 1
    assert len(rejected) == 1
    assert "Duplicate primary key" in rejected.iloc[0]["rejection_reason"]


def test_missing_email_rejected(sample_customers):

    customers = sample_customers.copy()
    customers.loc[0, "email"] = None

    valid, rejected = validate_dataset(
        "customers",
        customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1


def test_invalid_customer_reference_rejected(sample_customers):

    accounts = pd.DataFrame([
        {
            "account_id": "ACC000001",
            "customer_id": "CUST999999",
            "account_type": "Savings",
            "status": "Active",
            "created_at": "2026-02-01T10:00:00"
        }
    ])

    valid, rejected = validate_dataset(
        "accounts",
        accounts,
        customers=sample_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1


def test_invalid_order_date_rejected(sample_customers):

    orders = pd.DataFrame([
        {
            "order_id": "ORD000001",
            "customer_id": "CUST000001",
            "product_name": "Laptop",
            "amount": 5000,
            "order_status": "Completed",
            "order_date": "INVALID_DATE"
        }
    ])

    valid, rejected = validate_dataset(
        "orders",
        orders,
        customers=sample_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1


def test_negative_order_amount_rejected(sample_customers):

    orders = pd.DataFrame([
        {
            "order_id": "ORD000001",
            "customer_id": "CUST000001",
            "product_name": "Laptop",
            "amount": -5000,
            "order_status": "Completed",
            "order_date": "2026-02-01T10:00:00"
        }
    ])

    valid, rejected = validate_dataset(
        "orders",
        orders,
        customers=sample_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1


def test_invalid_interaction_type_rejected(sample_customers):

    interactions = pd.DataFrame([
        {
            "interaction_id": "INT000001",
            "customer_id": "CUST000001",
            "interaction_type": "Smoke Signal",
            "description": "Test interaction",
            "interaction_date": "2026-02-01T10:00:00"
        }
    ])

    valid, rejected = validate_dataset(
        "interactions",
        interactions,
        customers=sample_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1


def test_valid_customer_accepted(sample_customers):

    valid, rejected = validate_dataset(
        "customers",
        sample_customers
    )

    assert len(valid) == 1
    assert len(rejected) == 0
def test_empty_customer_dataset(sample_customers):

    empty_customers = sample_customers.iloc[0:0].copy()

    valid, rejected = validate_dataset(
        "customers",
        empty_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 0


def test_malformed_order_amount_rejected(sample_customers):

    orders = pd.DataFrame([
        {
            "order_id": "ORD000001",
            "customer_id": "CUST000001",
            "product_name": "Laptop",
            "amount": "invalid_amount",
            "order_status": "Completed",
            "order_date": "2026-02-01T10:00:00"
        }
    ])

    valid, rejected = validate_dataset(
        "orders",
        orders,
        customers=sample_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1
    assert "positive number" in rejected.iloc[0]["rejection_reason"]


def test_order_before_customer_creation_rejected(sample_customers):

    orders = pd.DataFrame([
        {
            "order_id": "ORD000001",
            "customer_id": "CUST000001",
            "product_name": "Laptop",
            "amount": 5000,
            "order_status": "Completed",
            "order_date": "2025-12-01T10:00:00"
        }
    ])

    valid, rejected = validate_dataset(
        "orders",
        orders,
        customers=sample_customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1
    assert "earlier than customer creation date" in rejected.iloc[0]["rejection_reason"]


def test_missing_customer_id_rejected(sample_customers):

    customers = sample_customers.copy()

    customers.loc[0, "customer_id"] = None

    valid, rejected = validate_dataset(
        "customers",
        customers
    )

    assert len(valid) == 0
    assert len(rejected) == 1
    assert "Missing value in customer_id" in rejected.iloc[0]["rejection_reason"]