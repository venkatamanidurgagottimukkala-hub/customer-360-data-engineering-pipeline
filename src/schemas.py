# Required columns for each source dataset

CUSTOMER_COLUMNS = [
    "customer_id",
    "first_name",
    "last_name",
    "email",
    "phone",
    "created_at"
]

ACCOUNT_COLUMNS = [
    "account_id",
    "customer_id",
    "account_type",
    "status",
    "created_at"
]

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "product_name",
    "amount",
    "order_status",
    "order_date"
]

INTERACTION_COLUMNS = [
    "interaction_id",
    "customer_id",
    "interaction_type",
    "description",
    "interaction_date"
]


# Primary keys for each dataset

PRIMARY_KEYS = {
    "customers": "customer_id",
    "accounts": "account_id",
    "orders": "order_id",
    "interactions": "interaction_id"
}


# Foreign key relationships

FOREIGN_KEYS = {
    "accounts": "customer_id",
    "orders": "customer_id",
    "interactions": "customer_id"
}