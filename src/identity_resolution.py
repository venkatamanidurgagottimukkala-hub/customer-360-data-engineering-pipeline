import pandas as pd
from itertools import combinations


def normalize_email(email):
    """Normalize email for identity matching."""

    if pd.isna(email):
        return ""

    return str(email).strip().lower()


def normalize_phone(phone):
    """Normalize phone by removing formatting and explicit country code."""

    if pd.isna(phone):
        return ""

    phone = str(phone).strip()

    # Keep digits only
    digits = "".join(
        character
        for character in phone
        if character.isdigit()
    )

    # Remove India's country code when explicitly provided
    if phone.startswith("+91") and digits.startswith("91"):
        digits = digits[2:]

    elif phone.startswith("0091") and digits.startswith("0091"):
        digits = digits[4:]

    return digits


def resolve_customer_identities(customers):
    """
    Resolve customers using normalized email and phone.

    Matching rules:
    1. Same email AND phone: automatic match.
    2. Same email but different phone: manual review.
    3. Same phone but different email: manual review.
    4. Similar names alone: no automatic match.

    The lexicographically smallest customer ID becomes
    the canonical customer ID.
    """

    customers = customers.copy()

    # STEP 1: Normalize email and phone

    customers["normalized_email"] = (
        customers["email"].apply(normalize_email)
    )

    customers["normalized_phone"] = (
        customers["phone"].apply(normalize_phone)
    )

    # STEP 2: Create deterministic customer ID mapping

    customer_mapping = {}

    grouped = customers[
        (customers["normalized_email"] != "")
        & (customers["normalized_phone"] != "")
    ].groupby(
        ["normalized_email", "normalized_phone"],
        sort=True
    )

    for _, group in grouped:

        customer_ids = sorted(
            group["customer_id"].astype(str).unique()
        )

        canonical_id = customer_ids[0]

        for customer_id in customer_ids:

            customer_mapping[customer_id] = canonical_id

    # Customers without confident matches retain their IDs

    for customer_id in customers["customer_id"]:

        customer_mapping.setdefault(
            str(customer_id),
            str(customer_id)
        )

    # STEP 3: Build customer mapping report

    mapping_df = pd.DataFrame([
        {
            "original_customer_id": original_id,
            "canonical_customer_id": canonical_id
        }
        for original_id, canonical_id in sorted(
            customer_mapping.items()
        )
    ])

    # STEP 4: Identify uncertain matching groups

    review_groups = []

    for column, reason in [
        ("normalized_email", "Same email but different phone"),
        ("normalized_phone", "Same phone but different email")
    ]:

        eligible = customers[
            customers[column] != ""
        ]

        for value, group in eligible.groupby(column):

            if len(group) < 2:
                continue

            customer_ids = sorted(
                group["customer_id"].astype(str).unique()
            )

            if len(customer_ids) < 2:
                continue

            pairs = combinations(customer_ids, 2)

            for first_id, second_id in pairs:

                first = customers[
                    customers["customer_id"].astype(str)
                    == first_id
                ].iloc[0]

                second = customers[
                    customers["customer_id"].astype(str)
                    == second_id
                ].iloc[0]

                same_email = (
                    first["normalized_email"]
                    == second["normalized_email"]
                )

                same_phone = (
                    first["normalized_phone"]
                    == second["normalized_phone"]
                )

                if not (same_email and same_phone):

                    review_groups.append({
                        "customer_id_1": first_id,
                        "customer_id_2": second_id,
                        "match_reason": reason
                    })

    review_df = pd.DataFrame(
        review_groups,
        columns=[
            "customer_id_1",
            "customer_id_2",
            "match_reason"
        ]
    ).drop_duplicates().reset_index(drop=True)

    # STEP 5: Apply canonical customer IDs

    customers["canonical_customer_id"] = (
        customers["customer_id"]
        .astype(str)
        .map(customer_mapping)
    )

    # STEP 6: Keep one record per canonical customer

    resolved_customers = (
        customers.sort_values("customer_id")
        .drop_duplicates(
            subset=["canonical_customer_id"],
            keep="first"
        )
        .drop(
            columns=[
                "normalized_email",
                "normalized_phone"
            ]
        )
        .reset_index(drop=True)
    )

    return resolved_customers, mapping_df, review_df