"""Staging → Analytics transformations.

The analytics layer creates business-ready aggregated tables:
- fct_daily_revenue: Daily revenue metrics
- fct_product_performance: Product-level revenue and order metrics
- fct_customer_summary: Customer lifetime metrics
- dim_date: Date dimension for time-series analysis
"""

import pandas as pd


def build_fct_daily_revenue(
    orders_df: pd.DataFrame, order_items_df: pd.DataFrame
) -> pd.DataFrame:
    """Build daily revenue fact table.

    Columns:
    - date: order date
    - total_orders: count of orders
    - total_revenue: sum of line_total
    - avg_order_value: avg revenue per order
    - total_items_sold: sum of quantity
    - completed_orders: count where status = 'completed'
    """
    # Only valid orders
    valid_orders = orders_df[orders_df.get("_is_valid", True) != False].copy()

    # Merge with items for revenue
    merged = valid_orders.merge(
        order_items_df[["order_id", "line_total", "quantity"]],
        on="order_id",
        how="left",
    )

    # Group by date
    daily = merged.groupby("order_date").agg(
        total_orders=("order_id", "nunique"),
        total_revenue=("line_total", "sum"),
        total_items_sold=("quantity", "sum"),
    ).reset_index()

    daily["avg_order_value"] = (daily["total_revenue"] / daily["total_orders"]).round(2)

    # Completed orders per day
    completed = valid_orders[valid_orders["status"] == "completed"].groupby("order_date").agg(
        completed_orders=("order_id", "nunique")
    ).reset_index()

    daily = daily.merge(completed, on="order_date", how="left")
    daily["completed_orders"] = daily["completed_orders"].fillna(0).astype(int)
    daily = daily.rename(columns={"order_date": "date"})

    return daily.sort_values("date").reset_index(drop=True)


def build_fct_product_performance(
    products_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    orders_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build product performance fact table.

    Columns:
    - product_id, product_name, category_id
    - total_revenue: sum of line_total for this product
    - total_quantity_sold: sum of quantity
    - total_orders: distinct orders containing this product
    - avg_unit_price: average selling price
    - first_order_date, last_order_date
    """
    # Join items with orders to get dates
    items_with_dates = order_items_df.merge(
        orders_df[["order_id", "order_date", "status"]],
        on="order_id",
        how="left",
    )

    # Only completed/shipped orders
    items_valid = items_with_dates[
        items_with_dates["status"].isin(["completed", "shipped", "processing"])
    ]

    perf = items_valid.groupby("product_id").agg(
        total_revenue=("line_total", "sum"),
        total_quantity_sold=("quantity", "sum"),
        total_orders=("order_id", "nunique"),
        avg_unit_price=("unit_price", "mean"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
    ).reset_index()

    # Merge product info
    perf = perf.merge(
        products_df[["product_id", "product_name", "category_id"]],
        on="product_id",
        how="left",
    )

    perf["avg_unit_price"] = perf["avg_unit_price"].round(2)
    perf["total_revenue"] = perf["total_revenue"].round(2)

    return perf.sort_values("total_revenue", ascending=False).reset_index(drop=True)


def build_fct_customer_summary(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build customer summary fact table.

    Columns:
    - customer_id, first_name, last_name, segment, region_id
    - total_orders: number of orders placed
    - total_revenue: total spending
    - avg_order_value: average order amount
    - first_order_date, last_order_date
    - days_since_last_order
    """
    valid_orders = orders_df[orders_df.get("_is_valid", True) != False].copy()

    # Revenue per order
    order_revenue = order_items_df.groupby("order_id").agg(
        order_revenue=("line_total", "sum")
    ).reset_index()

    orders_with_rev = valid_orders.merge(order_revenue, on="order_id", how="left")

    # Group by customer
    customer_metrics = orders_with_rev.groupby("customer_id").agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_revenue", "sum"),
        avg_order_value=("order_revenue", "mean"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
    ).reset_index()

    # Merge customer info
    summary = customers_df[["customer_id", "first_name", "last_name", "segment", "region_id"]].merge(
        customer_metrics, on="customer_id", how="left"
    )

    # Fill customers with no orders
    summary["total_orders"] = summary["total_orders"].fillna(0).astype(int)
    summary["total_revenue"] = summary["total_revenue"].fillna(0).round(2)
    summary["avg_order_value"] = summary["avg_order_value"].fillna(0).round(2)

    return summary.sort_values("total_revenue", ascending=False).reset_index(drop=True)
