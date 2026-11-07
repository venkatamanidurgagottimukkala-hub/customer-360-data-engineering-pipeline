from decimal import Decimal
import pandas as pd
from faker import Faker
from datetime import datetime
import random


# Generate customer records
def generate_customers(num_customers=1000, seed=42):

    fake = Faker()
    fake.seed_instance(seed)

    customers = []

    for i in range(1, num_customers + 1):

        customer = {
            "customer_id": f"CUST{i:06d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "phone": fake.phone_number(),
            "created_at": fake.date_time_between(
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2026, 11, 7)
            ).isoformat()
        }

        customers.append(customer)

    return pd.DataFrame(customers)


# Generate account records
def generate_accounts(customers, seed=42):

    fake = Faker()
    fake.seed_instance(seed)

    rng = random.Random(seed)

    customer_ids = customers["customer_id"].tolist()

    # Store customer creation dates for reference
    customer_dates = customers.set_index(
        "customer_id"
    )["created_at"].to_dict()

    accounts = []

    account_number = 1

    for customer_id in customer_ids:

        number_of_accounts = rng.randint(1, 3)

        # Get the creation date of the current customer
        customer_created_at = pd.to_datetime(
            customer_dates[customer_id]
        ).to_pydatetime()

        for _ in range(number_of_accounts):

            account = {
                "account_id": f"ACC{account_number:06d}",
                "customer_id": customer_id,
                "account_type": rng.choice(
                    ["Savings", "Checking", "Credit"]
                ),
                "status": rng.choice(
                    ["Active", "Inactive", "Closed"]
                ),
                "created_at": fake.date_time_between(
                    start_date=customer_created_at,
                    end_date=datetime(2026, 11, 7)
                ).isoformat()
            }

            accounts.append(account)

            account_number += 1

    return pd.DataFrame(accounts)
# Generate order records
def generate_orders(customers, seed=42):

    fake = Faker()
    fake.seed_instance(seed)

    rng = random.Random(seed + 2)

    customer_ids = customers["customer_id"].tolist()

    customer_dates = customers.set_index(
        "customer_id"
    )["created_at"].to_dict()

    products = [
        "Laptop",
        "Mobile Phone",
        "Headphones",
        "Keyboard",
        "Mouse",
        "Monitor",
        "Tablet"
    ]

    orders = []

    order_number = 1

    for customer_id in customer_ids:

        number_of_orders = rng.randint(0, 5)

        customer_created_at = pd.to_datetime(
            customer_dates[customer_id]
        ).to_pydatetime()

        for _ in range(number_of_orders):

            order = {
                "order_id": f"ORD{order_number:06d}",
                "customer_id": customer_id,
                "product_name": rng.choice(products),
                "amount": Decimal(
                    str(round(rng.uniform(500, 100000), 2))
                ).quantize(Decimal("0.01")),
                "order_status": rng.choice(
                    ["Completed", "Pending", "Cancelled"]
                ),
                "order_date": fake.date_time_between(
                    start_date=customer_created_at,
                    end_date=datetime(2026, 11, 7)
                ).isoformat()
            }

            orders.append(order)

            order_number += 1

    return pd.DataFrame(orders)
# Generate customer interaction records
def generate_interactions(customers, seed=42):

    fake = Faker()
    fake.seed_instance(seed)

    rng = random.Random(seed + 3)

    customer_ids = customers["customer_id"].tolist()

    customer_dates = customers.set_index(
        "customer_id"
    )["created_at"].to_dict()

    interaction_types = [
        "Call",
        "Email",
        "Chat",
        "Meeting",
        "Support Ticket"
    ]

    interactions = []

    interaction_number = 1

    for customer_id in customer_ids:

        number_of_interactions = rng.randint(0, 5)

        customer_created_at = pd.to_datetime(
            customer_dates[customer_id]
        ).to_pydatetime()

        for _ in range(number_of_interactions):

            interaction = {
                "interaction_id": f"INT{interaction_number:06d}",
                "customer_id": customer_id,
                "interaction_type": rng.choice(
                    interaction_types
                ),
                "description": fake.sentence(),
                "interaction_date": fake.date_time_between(
                    start_date=customer_created_at,
                    end_date=datetime(2026, 11, 7)
                ).isoformat()
            }

            interactions.append(interaction)

            interaction_number += 1

    return pd.DataFrame(interactions)