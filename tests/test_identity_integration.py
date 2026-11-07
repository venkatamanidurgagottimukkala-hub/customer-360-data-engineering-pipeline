import pandas as pd

from src.validation import validate_dataset
from src.identity_resolution import resolve_customer_identities
from src.customer_360 import build_customer_360


def test_identity_resolution_preserves_child_records():

    # STEP 1: Create duplicate customer records
    customers = pd.DataFrame([
        {
            "customer_id": "CUST000001",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "mani@example.com",
            "phone": "9876543210",
            "created_at": "2026-01-01T10:00:00"
        },
        {
            "customer_id": "CUST000002",
            "first_name": "Mani",
            "last_name": "Test",
            "email": "MANI@example.com",
            "phone": "+91 9876543210",
            "created_at": "2026-01-01T10:00:00"
        }
    ])

    # STEP 2: Create accounts
    accounts = pd.DataFrame([
        {
            "account_id": "ACC000001",
            "customer_id": "CUST000001",
            "account_type": "Savings",
            "status": "Active",
            "created_at": "2026-02-01T10:00:00"
        },
        {
            "account_id": "ACC000002",
            "customer_id": "CUST000002",
            "account_type": "Checking",
            "status": "Inactive",
            "created_at": "2026-02-02T10:00:00"
        }
    ])

    # STEP 3: Create orders
    orders = pd.DataFrame([
        {
            "order_id": "ORD000001",
            "customer_id": "CUST000001",
            "product_name": "Laptop",
            "amount": 100,
            "order_status": "Completed",
            "order_date": "2026-03-01T10:00:00"
        },
        {
            "order_id": "ORD000002",
            "customer_id": "CUST000002",
            "product_name": "Mobile",
            "amount": 200,
            "order_status": "Completed",
            "order_date": "2026-03-02T10:00:00"
        },
        {
            "order_id": "ORD000003",
            "customer_id": "CUST000002",
            "product_name": "Tablet",
            "amount": 300,
            "order_status": "Pending",
            "order_date": "2026-03-03T10:00:00"
        }
    ])

    # STEP 4: Create interactions
    interactions = pd.DataFrame([
        {
            "interaction_id": "INT000001",
            "customer_id": "CUST000001",
            "interaction_type": "Call",
            "description": "Customer enquiry",
            "interaction_date": "2026-04-01T10:00:00"
        },
        {
            "interaction_id": "INT000002",
            "customer_id": "CUST000002",
            "interaction_type": "Email",
            "description": "Product enquiry",
            "interaction_date": "2026-04-02T10:00:00"
        }
    ])

    # STEP 5: Validate customers
    valid_customers, rejected_customers = validate_dataset(
        "customers", customers
    )

    assert len(rejected_customers) == 0

    # STEP 6: Resolve duplicate customer identities
    (
        resolved_customers,
        customer_mapping,
        manual_review
    ) = resolve_customer_identities(valid_customers)

    merged_customer_count = (
        len(valid_customers) - len(resolved_customers)
    )

    assert merged_customer_count == 1
    assert len(resolved_customers) == 1

    # STEP 7: Use canonical customer IDs
    resolved_customers["customer_id"] = (
        resolved_customers["canonical_customer_id"]
    )

    resolved_customers = resolved_customers.drop(
        columns=["canonical_customer_id"]
    )

    customer_id_mapping = dict(zip(
        customer_mapping["original_customer_id"],
        customer_mapping["canonical_customer_id"]
    ))

    # STEP 8: Map child records to canonical customer IDs
    child_datasets = {
        "accounts": accounts,
        "orders": orders,
        "interactions": interactions
    }

    validated_data = {
        "customers": resolved_customers
    }

    for dataset_name, child_df in child_datasets.items():

        child_df = child_df.copy()

        child_df["customer_id"] = child_df["customer_id"].map(
            lambda customer_id: customer_id_mapping.get(
                str(customer_id), customer_id
            ) if pd.notna(customer_id) else customer_id
        )

        valid_df, rejected_df = validate_dataset(
            dataset_name,
            child_df,
            customers=resolved_customers
        )

        validated_data[dataset_name] = valid_df

        assert len(rejected_df) == 0

    # STEP 9: Verify child records are preserved
    assert len(validated_data["accounts"]) == 2
    assert len(validated_data["orders"]) == 3
    assert len(validated_data["interactions"]) == 2

    for dataset_name in ["accounts", "orders", "interactions"]:
        assert (
            validated_data[dataset_name]["customer_id"]
            == "CUST000001"
        ).all()

    # STEP 10: Build Customer 360
    customer_360 = build_customer_360(validated_data)

    # STEP 11: Verify final customer summary
    assert len(customer_360) == 1

    customer = customer_360.iloc[0]

    assert customer["customer_id"] == "CUST000001"
    assert customer["account_count"] == 2
    assert customer["active_account_count"] == 1
    assert customer["order_count"] == 3
    assert customer["total_order_amount"] == 600.00
    assert customer["interaction_count"] == 2

    print("\nIDENTITY RESOLUTION INTEGRATION TEST")
    print("-----------------------------------")
    print("Original customers:", len(valid_customers))
    print("Resolved customers:", len(resolved_customers))
    print("Merged customers:", merged_customer_count)
    print("Accounts preserved:", len(validated_data["accounts"]))
    print("Orders preserved:", len(validated_data["orders"]))
    print("Interactions preserved:", len(validated_data["interactions"]))
    print("Manual review pairs:", len(manual_review))
    print("Customer 360 integration: SUCCESS")