import pandas as pd

from src.validation import validate_dataset


# Create sample customer data
customers = pd.DataFrame([
    {
        "customer_id": "CUST000001",
        "first_name": "Mani",
        "last_name": "Test",
        "email": "mani@example.com",
        "phone": "9876543210",
        "created_at": "2026-01-01T10:00:00"
    }
])


# Test 1: Duplicate customer ID
duplicate_customers = pd.concat(
    [customers, customers],
    ignore_index=True
)

valid, rejected = validate_dataset(
    "customers",
    duplicate_customers
)

print("TEST 1 - DUPLICATE CUSTOMER")
print("Valid:", len(valid))
print("Rejected:", len(rejected))
print(rejected["rejection_reason"].tolist())


# Test 2: Missing customer email
missing_email = customers.copy()

missing_email.loc[0, "email"] = None

valid, rejected = validate_dataset(
    "customers",
    missing_email
)

print("\nTEST 2 - MISSING EMAIL")
print("Valid:", len(valid))
print("Rejected:", len(rejected))
print(rejected["rejection_reason"].tolist())


# Test 3: Invalid customer reference
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
    customers=customers
)

print("\nTEST 3 - INVALID CUSTOMER REFERENCE")
print("Valid:", len(valid))
print("Rejected:", len(rejected))
print(rejected["rejection_reason"].tolist())


# Test 4 and 5: Invalid date and negative amount
orders = pd.DataFrame([
    {
        "order_id": "ORD000001",
        "customer_id": "CUST000001",
        "product_name": "Laptop",
        "amount": -5000,
        "order_status": "Completed",
        "order_date": "INVALID_DATE"
    }
])

valid, rejected = validate_dataset(
    "orders",
    orders,
    customers=customers
)

print("\nTEST 4 AND 5 - INVALID DATE AND NEGATIVE AMOUNT")
print("Valid:", len(valid))
print("Rejected:", len(rejected))
print(rejected["rejection_reason"].tolist())


# Test 6: Invalid interaction type
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
    customers=customers
)

print("\nTEST 6 - INVALID INTERACTION TYPE")
print("Valid:", len(valid))
print("Rejected:", len(rejected))
print(rejected["rejection_reason"].tolist())