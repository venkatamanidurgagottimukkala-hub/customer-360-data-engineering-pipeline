import sqlite3

from pathlib import Path


# Define the database location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "customer360.db"


# Save pipeline datasets into SQLite
def save_to_database(validated_data, customer_360):

    # Create the database directory if necessary
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to the SQLite database
    with sqlite3.connect(DB_PATH) as connection:

        # Prepare all five datasets
        datasets = {
            "customers": validated_data["customers"],
            "accounts": validated_data["accounts"],
            "orders": validated_data["orders"],
            "interactions": validated_data["interactions"],
            "customer_360": customer_360
        }

        # Save each dataset as a database table
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

    return DB_PATH