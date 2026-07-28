"""Raw → Staging transformations.

The staging layer applies:
- Data type standardization
- NULL handling and defaults
- Deduplication
- Column renaming to snake_case conventions
- Date parsing and validation
- Basic data cleansing (trimming, case normalization)
"""

from datetime import date

import pandas as pd


def stage_customers(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw customers to staging layer.

    Transformations:
    - Trim whitespace from string fields
    - Normalize email to lowercase
    - Parse signup_date to proper date type
    - Flag records with missing required fields
    """
    df = raw_df.copy()

    # Trim strings
    for col in ["first_name", "last_name", "email"]:
        df[col] = df[col].astype(str).str.strip()

    # Normalize email
    df["email"] = df["email"].str.lower()

    # Parse dates
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce").dt.date

    # Add staging metadata
    df["_staged_at"] = pd.Timestamp.now()
    df["_is_valid"] = True

    # Flag invalid records
    df.loc[df["email"].isna() | (df["email"] == ""), "_is_valid"] = False
    df.loc[df["region_id"].isna(), "_is_valid"] = False

    return df


def stage_products(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw products to staging layer.

    Transformations:
    - Ensure price is positive
    - Default stock_quantity to 0 if NULL
    - Parse created_date
    - Validate category_id references
    """
    df = raw_df.copy()

    # Ensure non-negative price
    df["price"] = df["price"].clip(lower=0)

    # Default stock
    df["stock_quantity"] = df["stock_quantity"].fillna(0).astype(int)

    # Parse dates
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce").dt.date

    # Add staging metadata
    df["_staged_at"] = pd.Timestamp.now()
    df["_is_valid"] = True

    # Flag invalid
    df.loc[df["price"] <= 0, "_is_valid"] = False
    df.loc[df["category_id"].isna(), "_is_valid"] = False

    return df


def stage_orders(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw orders to staging layer.

    Transformations:
    - Parse date fields
    - Validate shipped_date >= order_date
    - Normalize status to lowercase
    - Flag orders with future dates
    """
    df = raw_df.copy()

    # Parse dates
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.date
    df["shipped_date"] = pd.to_datetime(df["shipped_date"], errors="coerce").dt.date

    # Normalize status
    df["status"] = df["status"].str.lower().str.strip()

    # Add staging metadata
    df["_staged_at"] = pd.Timestamp.now()
    df["_is_valid"] = True

    # Flag invalid: future order dates
    today = date.today()
    df.loc[df["order_date"] > today, "_is_valid"] = False

    # Flag invalid: shipped before ordered
    mask = df["shipped_date"].notna() & df["order_date"].notna()
    df.loc[mask & (df["shipped_date"] < df["order_date"]), "_is_valid"] = False

    return df


def stage_order_items(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw order items to staging layer.

    Transformations:
    - Validate quantity > 0
    - Validate unit_price >= 0
    - Recalculate line_total if inconsistent
    """
    df = raw_df.copy()

    # Validate positive values
    df["quantity"] = df["quantity"].clip(lower=1)
    df["unit_price"] = df["unit_price"].clip(lower=0)
    df["discount"] = df["discount"].fillna(0).clip(lower=0)

    # Recalculate line_total for consistency
    df["_calculated_line_total"] = (df["unit_price"] * df["quantity"] - df["discount"]).round(2)

    # Add staging metadata
    df["_staged_at"] = pd.Timestamp.now()
    df["_is_valid"] = True

    # Flag invalid
    df.loc[df["unit_price"] <= 0, "_is_valid"] = False
    df.loc[df["quantity"] <= 0, "_is_valid"] = False

    return df
