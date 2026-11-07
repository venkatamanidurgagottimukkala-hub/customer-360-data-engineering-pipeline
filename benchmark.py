import json

from time import perf_counter
from pathlib import Path

from src.data_generator import (
    generate_customers,
    generate_accounts,
    generate_orders,
    generate_interactions
)

from src.validation import validate_all_datasets
from src.customer_360 import build_customer_360


# Benchmark configuration
NUMBER_OF_CUSTOMERS = 15000

PROJECT_ROOT = Path(__file__).resolve().parent

OUTPUT_FILE = PROJECT_ROOT / "outputs" / "performance_benchmark.json"


# Start total execution timer
total_start = perf_counter()


# STEP 1: Generate sample datasets
print("\nSTEP 1: DATA GENERATION")

start = perf_counter()

customers = generate_customers(NUMBER_OF_CUSTOMERS)
accounts = generate_accounts(customers)
orders = generate_orders(customers)
interactions = generate_interactions(customers)

generation_time = perf_counter() - start

datasets = {
    "customers": customers,
    "accounts": accounts,
    "orders": orders,
    "interactions": interactions
}

input_counts = {
    name: len(df)
    for name, df in datasets.items()
}

total_records = sum(input_counts.values())

print("Customers:", len(customers))
print("Accounts:", len(accounts))
print("Orders:", len(orders))
print("Interactions:", len(interactions))
print("Total records:", total_records)
print("Generation time:", round(generation_time, 2), "seconds")


# STEP 2: Validate datasets
print("\nSTEP 2: DATA VALIDATION")

start = perf_counter()

validated_data, rejected_data = validate_all_datasets(datasets)

validation_time = perf_counter() - start

valid_count = sum(
    len(df) for df in validated_data.values()
)

rejected_count = sum(
    len(df) for df in rejected_data.values()
)

print("Valid records:", valid_count)
print("Rejected records:", rejected_count)
print("Validation time:", round(validation_time, 2), "seconds")


# STEP 3: Build Customer 360
print("\nSTEP 3: CUSTOMER 360 TRANSFORMATION")

start = perf_counter()

customer_360 = build_customer_360(validated_data)

transformation_time = perf_counter() - start

print("Customer 360 records:", len(customer_360))
print("Transformation time:", round(transformation_time, 2), "seconds")


# STEP 4: Calculate total execution time
total_time = perf_counter() - total_start

print("\nPERFORMANCE BENCHMARK RESULTS")

print("Total input records:", total_records)
print("Total valid records:", valid_count)
print("Total rejected records:", rejected_count)

print("Generation time:", round(generation_time, 2))
print("Validation time:", round(validation_time, 2))
print("Transformation time:", round(transformation_time, 2))
print("Total execution time:", round(total_time, 2))


# STEP 5: Save benchmark results
report = {
    "customer_count": NUMBER_OF_CUSTOMERS,
    "input_counts": input_counts,
    "total_input_records": total_records,
    "valid_records": valid_count,
    "rejected_records": rejected_count,
    "customer_360_records": len(customer_360),
    "generation_time_seconds": round(generation_time, 2),
    "validation_time_seconds": round(validation_time, 2),
    "transformation_time_seconds": round(transformation_time, 2),
    "total_execution_time_seconds": round(total_time, 2)
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(report, file, indent=4)

print("\nBenchmark report saved to:", OUTPUT_FILE)