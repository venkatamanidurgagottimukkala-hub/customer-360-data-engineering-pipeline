import pandas as pd

from src.identity_resolution import resolve_customer_identities


def create_customers(records):
    return pd.DataFrame(records)


def test_exact_duplicate_identity_is_merged():

    customers = create_customers([
        {
            "customer_id": "CUST002",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2026-01-01"
        },
        {
            "customer_id": "CUST001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        }
    ])

    resolved, mapping, review = resolve_customer_identities(customers)

    assert len(resolved) == 1
    assert mapping["canonical_customer_id"].nunique() == 1
    assert review.empty


def test_email_case_is_normalized():

    customers = create_customers([
        {
            "customer_id": "CUST001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "MANI@EXAMPLE.COM",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        },
        {
            "customer_id": "CUST002",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        }
    ])

    resolved, mapping, review = resolve_customer_identities(customers)

    assert len(resolved) == 1


def test_phone_formatting_is_normalized():

    customers = create_customers([
        {
            "customer_id": "CUST001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "+91 98765-43210",
            "created_at": "2025-01-01"
        },
        {
            "customer_id": "CUST002",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        }
    ])

    resolved, mapping, review = resolve_customer_identities(customers)

    assert len(resolved) == 1


def test_same_email_different_phone_requires_review():

    customers = create_customers([
        {
            "customer_id": "CUST001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        },
        {
            "customer_id": "CUST002",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9123456780",
            "created_at": "2025-01-01"
        }
    ])

    resolved, mapping, review = resolve_customer_identities(customers)

    assert len(resolved) == 2
    assert not review.empty
    assert "Same email but different phone" in review["match_reason"].values


def test_same_phone_different_email_requires_review():

    customers = create_customers([
        {
            "customer_id": "CUST001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        },
        {
            "customer_id": "CUST002",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "other@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        }
    ])

    resolved, mapping, review = resolve_customer_identities(customers)

    assert len(resolved) == 2
    assert not review.empty
    assert "Same phone but different email" in review["match_reason"].values


def test_canonical_id_is_deterministic():

    customers = create_customers([
        {
            "customer_id": "CUST003",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        },
        {
            "customer_id": "CUST001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2025-01-01"
        }
    ])

    resolved, mapping, review = resolve_customer_identities(customers)

    assert set(mapping["canonical_customer_id"]) == {"CUST001"}