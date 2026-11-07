import sqlite3
import json

from pathlib import Path
from datetime import datetime, timezone


# Define the database location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "customer360.db"


# Save pipeline datasets and preserve historical records
def save_to_database(validated_data, customer_360, run_id):

    # Create the database directory if necessary
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Record the current UTC timestamp
    recorded_at = datetime.now(timezone.utc).isoformat()

    # Prepare record counts
    record_counts = {
        name: len(dataframe)
        for name, dataframe in validated_data.items()
    }

    record_counts["customer_360"] = len(customer_360)

    # Connect to SQLite
    with sqlite3.connect(DB_PATH) as connection:

        cursor = connection.cursor()

        # --------------------------------------------------
        # STEP 1: CREATE PIPELINE RUN HISTORY TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_run_history (
                run_id TEXT PRIMARY KEY,
                recorded_at TEXT NOT NULL,
                record_counts TEXT NOT NULL
            )
        """)

        # --------------------------------------------------
        # STEP 2: CREATE INTERACTION EVENT HISTORY TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_event_history (
                interaction_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                interaction_type TEXT,
                description TEXT,
                interaction_date TEXT,
                first_seen_run_id TEXT NOT NULL,
                source_file TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
        """)

        # --------------------------------------------------
        # STEP 3: PRESERVE INTERACTION EVENTS
        # --------------------------------------------------

        interactions = validated_data["interactions"]

        for _, row in interactions.iterrows():

            interaction_id = str(row["interaction_id"])

            event_values = (
                str(row["customer_id"]),
                str(row["interaction_type"]),
                str(row["description"]),
                str(row["interaction_date"])
            )

            # Check whether this event already exists
            existing_event = cursor.execute(
                """
                SELECT
                    customer_id,
                    interaction_type,
                    description,
                    interaction_date
                FROM interaction_event_history
                WHERE interaction_id = ?
                """,
                (interaction_id,)
            ).fetchone()

            if existing_event is not None:

                # Do not silently accept changed event details
                if existing_event != event_values:

                    raise ValueError(
                        "Interaction history conflict: "
                        f"{interaction_id} already exists "
                        "with different event details."
                    )

                # Identical event: safely skip it
                continue

            # Insert a new historical event
            cursor.execute(
                """
                INSERT INTO interaction_event_history (
                    interaction_id,
                    customer_id,
                    interaction_type,
                    description,
                    interaction_date,
                    first_seen_run_id,
                    source_file,
                    recorded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interaction_id,
                    event_values[0],
                    event_values[1],
                    event_values[2],
                    event_values[3],
                    run_id,
                    "interactions.csv",
                    recorded_at
                )
            )

        # --------------------------------------------------
        # STEP 4: RECORD THE PIPELINE RUN
        # --------------------------------------------------

        cursor.execute(
            """
            INSERT OR IGNORE INTO pipeline_run_history (
                run_id,
                recorded_at,
                record_counts
            )
            VALUES (?, ?, ?)
            """,
            (
                run_id,
                recorded_at,
                json.dumps(record_counts, sort_keys=True)
            )
        )

        # --------------------------------------------------
        # STEP 5: SAVE CURRENT-STATE DATASETS
        # --------------------------------------------------

        datasets = {
            "customers": validated_data["customers"],
            "accounts": validated_data["accounts"],
            "orders": validated_data["orders"],
            "interactions": validated_data["interactions"],
            "customer_360": customer_360
        }

        for table_name, dataframe in datasets.items():

            dataframe.to_sql(
                name=table_name,
                con=connection,
                if_exists="replace",
                index=False
            )

            print(
                f"Saved table: {table_name} "
                f"| Records: {len(dataframe)}"
            )

        print("Historical pipeline run and interaction events saved.")

    return DB_PATH