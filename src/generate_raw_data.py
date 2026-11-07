from pathlib import Path

from src.data_generator import (
    generate_customers,
    generate_accounts,
    generate_orders,
    generate_interactions
)


# Define the raw data directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


# Create the raw directory if it does not exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# Generate all four datasets
customers = generate_customers(1000)
accounts = generate_accounts(customers)
orders = generate_orders(customers)
interactions = generate_interactions(customers)


# Save datasets as CSV files
customers.to_csv(RAW_DATA_DIR / "customers.csv", index=False)

accounts.to_csv(RAW_DATA_DIR / "accounts.csv", index=False)

orders.to_csv(RAW_DATA_DIR / "orders.csv", index=False)

interactions.to_csv(RAW_DATA_DIR / "interactions.csv", index=False)


# Display generation summary
print("RAW DATA GENERATION COMPLETED")

print("--------------------------------")

print("Customers:", len(customers))
print("Accounts:", len(accounts))
print("Orders:", len(orders))
print("Interactions:", len(interactions))

print("--------------------------------")

print("Files saved successfully in:", RAW_DATA_DIR)