# Customer 360 Data Dictionary

This document describes the schemas, columns, logical data types and purposes of the Customer 360 Data Engineering Pipeline.

## 1. Customers Dataset

**Source:** `data/raw/customers.csv`

| Column | Data Type | Description |
|---|---|---|
| customer_id | String | Unique customer identifier. Primary key. |
| first_name | String | Customer's first name. |
| last_name | String | Customer's last name. |
| email | String | Customer's email address. |
| phone | String | Customer's contact number. |
| created_at | ISO-8601 Timestamp | Date and time the customer record was created. |

## 2. Accounts Dataset

**Source:** `data/raw/accounts.csv`

| Column | Data Type | Description |
|---|---|---|
| account_id | String | Unique account identifier. Primary key. |
| customer_id | String | References the customer who owns the account. Foreign key. |
| account_type | String | Account category: Savings, Checking or Credit. |
| status | String | Account status: Active, Inactive or Closed. |
| created_at | ISO-8601 Timestamp | Account creation date and time. |

## 3. Orders Dataset

**Source:** `data/raw/orders.csv`

| Column | Data Type | Description |
|---|---|---|
| order_id | String | Unique order identifier. Primary key. |
| customer_id | String | References the customer who placed the order. Foreign key. |
| product_name | String | Name of the purchased product. |
| amount | Decimal (2 places) | Monetary value of the order. |
| order_status | String | Order status: Completed, Pending or Cancelled. |
| order_date | ISO-8601 Timestamp | Date and time the order was placed. |

## 4. Interactions Dataset

**Source:** `data/raw/interactions.csv`

| Column | Data Type | Description |
|---|---|---|
| interaction_id | String | Unique interaction identifier. Primary key. |
| customer_id | String | References the customer involved in the interaction. Foreign key. |
| interaction_type | String | Type of interaction: Call, Email, Chat, Meeting or Support Ticket. |
| description | String | Description of the customer interaction. |
| interaction_date | ISO-8601 Timestamp | Date and time of the interaction. |

## 5. Customer 360 Dataset

**Output:** `data/processed/customer_360.csv`

| Column | Data Type | Description |
|---|---|---|
| customer_id | String | Unique customer identifier. |
| first_name | String | Customer's first name. |
| last_name | String | Customer's last name. |
| email | String | Customer's email address. |
| phone | String | Customer's contact number. |
| created_at | ISO-8601 Timestamp | Customer creation date. |
| account_count | Integer | Total number of accounts belonging to the customer. |
| active_account_count | Integer | Number of active customer accounts. |
| order_count | Integer | Total number of customer orders. |
| total_order_amount | Decimal (2 places) | Sum of the customer's order amounts. |
| last_order_date | ISO-8601 Timestamp / Null | Most recent order date. Null if no orders exist. |
| interaction_count | Integer | Total number of customer interactions. |
| last_interaction_date | ISO-8601 Timestamp / Null | Most recent interaction date. Null if no interactions exist. |

## 6. Pipeline Metadata

The published source datasets also contain:

| Column | Data Type | Description |
|---|---|---|
| run_id | String | Deterministic identifier generated from source file contents. |
| source_file | String | Name of the original source CSV file. |

Rejected datasets additionally contain:

| Column | Data Type | Description |
|---|---|---|
| rejection_reason | String | Explanation of why the record failed validation. |

## 7. Primary and Foreign Keys

| Dataset | Primary Key | Foreign Key |
|---|---|---|
| Customers | customer_id | None |
| Accounts | account_id | customer_id |
| Orders | order_id | customer_id |
| Interactions | interaction_id | customer_id |
| Customer 360 | customer_id | None |

## 8. Relationships

- One customer can have multiple accounts.
- One customer can place multiple orders.
- One customer can have multiple interactions.
- Customer 360 combines customer-level summaries from all three related datasets.

## 9. Data Handling Rules

- Primary keys must be unique and non-null.
- Foreign keys must reference valid customers.
- Order amounts must be positive.
- Dates must be valid and cannot precede customer creation dates for related records.
- Categorical fields must contain permitted values.
- Invalid records are separated into quarantine outputs with rejection reasons.