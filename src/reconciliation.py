import json
import sqlite3

from pathlib import Path
from datetime import datetime, timezone

from src.storage import DB_PATH


# Define the report location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORT_PATH = PROJECT_ROOT / "outputs" / "reconciliation_report.json"


# Run reconciliation checks
def run_reconciliation(
    source_data,
    validated_data,
    rejected_data,
    customer_360
):

    # Store all reconciliation results
    checks = []

    # Connect to the SQLite database
    with sqlite3.connect(DB_PATH) as connection:

        # STEP 1: Verify source record counts
        for dataset_name in source_data:

            source_count = len(source_data[dataset_name])

            valid_count = len(validated_data[dataset_name])

            rejected_count = len(rejected_data[dataset_name])

            is_valid = (
                source_count == valid_count + rejected_count
            )

            checks.append({
                "check": f"{dataset_name}_record_reconciliation",
                "status": "PASS" if is_valid else "FAIL",
                "source_records": source_count,
                "valid_records": valid_count,
                "rejected_records": rejected_count
            })

        # STEP 2: Verify database record counts
        for dataset_name in validated_data:

            database_count = connection.execute(
                f"SELECT COUNT(*) FROM {dataset_name}"
            ).fetchone()[0]

            expected_count = len(validated_data[dataset_name])

            is_valid = database_count == expected_count

            checks.append({
                "check": f"{dataset_name}_database_count",
                "status": "PASS" if is_valid else "FAIL",
                "expected_records": expected_count,
                "database_records": database_count
            })

        # STEP 3: Verify Customer 360 record count
        database_customer_count = connection.execute(
            "SELECT COUNT(*) FROM customer_360"
        ).fetchone()[0]

        is_valid = database_customer_count == len(customer_360)

        checks.append({
            "check": "customer_360_record_count",
            "status": "PASS" if is_valid else "FAIL",
            "expected_records": len(customer_360),
            "database_records": database_customer_count
        })

        # STEP 4: Verify total order amount
        source_total = connection.execute(
            "SELECT ROUND(SUM(amount), 2) FROM orders"
        ).fetchone()[0] or 0

        customer_360_total = connection.execute(
            "SELECT ROUND(SUM(total_order_amount), 2) FROM customer_360"
        ).fetchone()[0] or 0

        is_valid = round(source_total, 2) == round(
            customer_360_total, 2
        )

        checks.append({
            "check": "order_amount_reconciliation",
            "status": "PASS" if is_valid else "FAIL",
            "source_total": source_total,
            "customer_360_total": customer_360_total
        })

        # STEP 5: Check invalid customer references
        foreign_key_queries = {
            "accounts": """
                SELECT COUNT(*)
                FROM accounts a
                LEFT JOIN customers c
                ON a.customer_id = c.customer_id
                WHERE c.customer_id IS NULL
            """,

            "orders": """
                SELECT COUNT(*)
                FROM orders o
                LEFT JOIN customers c
                ON o.customer_id = c.customer_id
                WHERE c.customer_id IS NULL
            """,

            "interactions": """
                SELECT COUNT(*)
                FROM interactions i
                LEFT JOIN customers c
                ON i.customer_id = c.customer_id
                WHERE c.customer_id IS NULL
            """
        }

        for dataset_name, query in foreign_key_queries.items():

            orphan_count = connection.execute(query).fetchone()[0]

            checks.append({
                "check": f"{dataset_name}_foreign_key_integrity",
                "status": "PASS" if orphan_count == 0 else "FAIL",
                "orphan_records": orphan_count
            })

        # STEP 6: Verify customer-level aggregation counts
        aggregation_queries = {
            "account_count": """
                SELECT COUNT(*)
                FROM customer_360 c
                WHERE c.account_count != (
                    SELECT COUNT(*)
                    FROM accounts a
                    WHERE a.customer_id = c.customer_id
                )
            """,

            "order_count": """
                SELECT COUNT(*)
                FROM customer_360 c
                WHERE c.order_count != (
                    SELECT COUNT(*)
                    FROM orders o
                    WHERE o.customer_id = c.customer_id
                )
            """,

            "interaction_count": """
                SELECT COUNT(*)
                FROM customer_360 c
                WHERE c.interaction_count != (
                    SELECT COUNT(*)
                    FROM interactions i
                    WHERE i.customer_id = c.customer_id
                )
            """
        }

        for column_name, query in aggregation_queries.items():

            mismatch_count = connection.execute(
                query
            ).fetchone()[0]

            checks.append({
                "check": f"{column_name}_reconciliation",
                "status": "PASS" if mismatch_count == 0 else "FAIL",
                "mismatches": mismatch_count
            })

    # STEP 7: Calculate overall reconciliation status
    overall_status = (
        "PASS"
        if all(check["status"] == "PASS" for check in checks)
        else "FAIL"
    )

    # Prepare the final report
    report = {
        "report_generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "overall_status": overall_status,

        "total_checks": len(checks),

        "passed_checks": sum(
            check["status"] == "PASS" for check in checks
        ),

        "failed_checks": sum(
            check["status"] == "FAIL" for check in checks
        ),

        "checks": checks
    }

    # Create the output directory
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save the report as JSON
    with open(REPORT_PATH, "w", encoding="utf-8") as file:

        json.dump(
            report,
            file,
            indent=4
        )

    print("\nRECONCILIATION REPORT")

    print("Overall status:", overall_status)

    print("Total checks:", len(checks))

    print("Passed:", report["passed_checks"])

    print("Failed:", report["failed_checks"])

    print("Report saved to:", REPORT_PATH)

    return report