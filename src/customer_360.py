import pandas as pd


# Build the unified Customer 360 dataset
def build_customer_360(validated_data):

    # Get the four validated datasets
    customers = validated_data["customers"].copy()
    accounts = validated_data["accounts"].copy()
    orders = validated_data["orders"].copy()
    interactions = validated_data["interactions"].copy()

    # STEP 1: Aggregate account information
    account_summary = accounts.groupby("customer_id").agg(
        account_count=("account_id", "count"),
        active_account_count=(
            "status",
            lambda status: (status == "Active").sum()
        )
    ).reset_index()

    # STEP 2: Aggregate order information
    orders["amount"] = pd.to_numeric(
        orders["amount"],
        errors="coerce"
    )

    order_summary = orders.groupby("customer_id").agg(
        order_count=("order_id", "count"),
        total_order_amount=("amount", "sum"),
        last_order_date=("order_date", "max")
    ).reset_index()

    # STEP 3: Aggregate interaction information
    interaction_summary = interactions.groupby("customer_id").agg(
        interaction_count=("interaction_id", "count"),
        last_interaction_date=("interaction_date", "max")
    ).reset_index()

    # STEP 4: Combine account information with customers
    customer_360 = customers.merge(
        account_summary,
        on="customer_id",
        how="left"
    )

    # STEP 5: Combine order information
    customer_360 = customer_360.merge(
        order_summary,
        on="customer_id",
        how="left"
    )

    # STEP 6: Combine interaction information
    customer_360 = customer_360.merge(
        interaction_summary,
        on="customer_id",
        how="left"
    )

    # STEP 7: Replace missing counts and amounts with zero
    count_columns = [
        "account_count",
        "active_account_count",
        "order_count",
        "interaction_count"
    ]

    customer_360[count_columns] = (
        customer_360[count_columns]
        .fillna(0)
        .astype(int)
    )

    customer_360["total_order_amount"] = (
        customer_360["total_order_amount"]
        .fillna(0)
        .round(2)
    )

    return customer_360