import pandas as pd

from src.schemas import (
    PRIMARY_KEYS,
    FOREIGN_KEYS
)


ALLOWED_VALUES = {
    "account_type": ["Savings", "Checking", "Credit"],
    "status": ["Active", "Inactive", "Closed"],
    "order_status": ["Completed", "Pending", "Cancelled"],
    "interaction_type": [
        "Call",
        "Email",
        "Chat",
        "Meeting",
        "Support Ticket"
    ]
}


DATE_COLUMNS = {
    "customers": "created_at",
    "accounts": "created_at",
    "orders": "order_date",
    "interactions": "interaction_date"
}


def validate_dataset(dataset_name, df, customers=None):

    df = df.copy()

    rejection_reasons = [[] for _ in range(len(df))]

    def add_reason(mask, message):

        positions = mask.to_numpy(dtype=bool)

        for position in range(len(positions)):

            if positions[position]:

                rejection_reasons[position].append(message)

    # STEP 1: Check missing values

    for column in df.columns:

        missing_mask = df[column].isna()

        add_reason(
            missing_mask,
            f"Missing value in {column}"
        )

    # STEP 2: Check duplicate primary keys

    primary_key = PRIMARY_KEYS[dataset_name]

    duplicate_mask = df[primary_key].duplicated(
        keep="first"
    )

    add_reason(
        duplicate_mask,
        f"Duplicate primary key: {primary_key}"
    )

    # STEP 3: Prepare customer reference information

    foreign_key = FOREIGN_KEYS.get(dataset_name)

    valid_customer_ids = set()
    customer_dates = {}

    if customers is not None:

        valid_customer_ids = set(
            customers["customer_id"].dropna()
        )

        customer_dates = (
            customers.set_index("customer_id")["created_at"].to_dict()
        )

    # STEP 4: Validate foreign keys

    if foreign_key is not None:

        invalid_customer_mask = (
            df[foreign_key].notna()
            & ~df[foreign_key].isin(valid_customer_ids)
        )

        add_reason(
            invalid_customer_mask,
            "Invalid customer reference"
        )

    # STEP 5: Validate dates

    date_column = DATE_COLUMNS[dataset_name]

    record_dates = pd.to_datetime(
        df[date_column],
        errors="coerce",
        utc=True
    )

    invalid_date_mask = (
        df[date_column].notna()
        & record_dates.isna()
    )

    add_reason(
        invalid_date_mask,
        f"Invalid date in {date_column}"
    )

    # STEP 6: Compare child record dates with customer creation dates

    if foreign_key is not None:

        mapped_customer_dates = df[foreign_key].map(
            customer_dates
        )

        parsed_customer_dates = pd.to_datetime(
            mapped_customer_dates,
            errors="coerce",
            utc=True
        )

        invalid_customer_date_mask = (
            df[foreign_key].isin(valid_customer_ids)
            & mapped_customer_dates.notna()
            & parsed_customer_dates.isna()
        )

        add_reason(
            invalid_customer_date_mask,
            "Invalid customer creation date"
        )

        earlier_record_mask = (
            record_dates.notna()
            & parsed_customer_dates.notna()
            & (record_dates < parsed_customer_dates)
        )

        add_reason(
            earlier_record_mask,
            "Record date is earlier than customer creation date"
        )

    # STEP 7: Validate order amounts

    if dataset_name == "orders":

        amounts = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        invalid_amount_mask = (
            amounts.isna()
            | (amounts <= 0)
        )

        add_reason(
            invalid_amount_mask,
            "Order amount must be a positive number"
        )

    # STEP 8: Validate allowed categorical values

    for column, allowed_values in ALLOWED_VALUES.items():

        if column in df.columns:

            invalid_value_mask = (
                df[column].notna()
                & ~df[column].isin(allowed_values)
            )

            positions = invalid_value_mask.to_numpy(dtype=bool)

            for position in range(len(positions)):

                if positions[position]:

                    value = df.iloc[position][column]

                    rejection_reasons[position].append(
                        f"Invalid value in {column}: {value}"
                    )

    # STEP 9: Separate valid and rejected records

    rejected_mask = [
        len(reasons) > 0
        for reasons in rejection_reasons
    ]

    valid_positions = [
        position
        for position, rejected in enumerate(rejected_mask)
        if not rejected
    ]

    rejected_positions = [
        position
        for position, rejected in enumerate(rejected_mask)
        if rejected
    ]

    valid_df = df.iloc[valid_positions].copy()

    rejected_df = df.iloc[rejected_positions].copy()

    rejected_df["rejection_reason"] = [
        "; ".join(rejection_reasons[position])
        for position in rejected_positions
    ]

    return valid_df, rejected_df


def validate_all_datasets(datasets):

    validated_data = {}
    rejected_data = {}

    valid_customers, rejected_customers = validate_dataset(
        "customers",
        datasets["customers"]
    )

    validated_data["customers"] = valid_customers
    rejected_data["customers"] = rejected_customers

    for dataset_name in ["accounts", "orders", "interactions"]:

        valid_df, rejected_df = validate_dataset(
            dataset_name,
            datasets[dataset_name],
            customers=valid_customers
        )

        validated_data[dataset_name] = valid_df
        rejected_data[dataset_name] = rejected_df

    return validated_data, rejected_data