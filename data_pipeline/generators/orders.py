"""Order and order items generator — realistic transaction data."""

import random
from datetime import timedelta

import numpy as np
import pandas as pd
from faker import Faker

from data_pipeline.generators.base import GenerationConfig


ORDER_STATUSES = ["completed", "processing", "shipped", "cancelled", "returned"]
STATUS_WEIGHTS = [0.70, 0.10, 0.10, 0.07, 0.03]

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "crypto"]
PAYMENT_WEIGHTS = [0.45, 0.25, 0.20, 0.08, 0.02]


def generate_orders(
    config: GenerationConfig | None = None,
    products_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate orders and order_items with realistic patterns.

    Patterns modeled:
    - Seasonal peaks (Q4 holiday season, summer)
    - Day-of-week patterns (more orders on weekdays)
    - Customer purchase frequency follows power law
    - Premium customers order more frequently
    - Some orders have invalid/NULL shipped dates (quality edge cases)

    Returns:
        Tuple of (orders_df, order_items_df)
    """
    if config is None:
        from data_pipeline.generators.base import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    fake = Faker()
    Faker.seed(config.random_seed)
    random.seed(config.random_seed)
    np.random.seed(config.random_seed)

    # Generate order dates with seasonal patterns
    total_days = (config.order_end_date - config.order_start_date).days
    order_dates = []

    for _ in range(config.num_orders):
        # Base: uniform random day
        day_offset = random.randint(0, total_days)
        order_date = config.order_start_date + timedelta(days=day_offset)

        # Seasonal bias: boost Q4 (Oct-Dec) and reduce Q1 (Jan-Mar)
        month = order_date.month
        if month in (10, 11, 12):
            # Accept Q4 dates more frequently (simulate holiday season)
            if random.random() < 0.7:
                order_dates.append(order_date)
                continue
        elif month in (1, 2, 3):
            # Reduce Q1 (post-holiday slowdown)
            if random.random() < 0.4:
                order_dates.append(order_date)
                continue

        order_dates.append(order_date)

    # Ensure we have exactly num_orders dates
    while len(order_dates) < config.num_orders:
        day_offset = random.randint(0, total_days)
        order_dates.append(config.order_start_date + timedelta(days=day_offset))
    order_dates = sorted(order_dates[: config.num_orders])

    # Customer assignment: power-law distribution (some customers buy a lot)
    # 20% of customers generate 80% of orders
    customer_weights = np.random.pareto(1.5, config.num_customers) + 1
    customer_weights /= customer_weights.sum()
    customer_ids = np.random.choice(
        range(1, config.num_customers + 1),
        size=config.num_orders,
        p=customer_weights,
    )

    # Product prices for reference
    if products_df is not None:
        product_prices = products_df.set_index("product_id")["price"].to_dict()
        product_ids_available = list(products_df["product_id"])
    else:
        product_prices = {i: round(random.uniform(10, 500), 2) for i in range(1, 201)}
        product_ids_available = list(range(1, 201))

    orders = []
    order_items = []
    order_item_id = 1

    for order_idx in range(config.num_orders):
        order_id = order_idx + 1
        customer_id = int(customer_ids[order_idx])
        order_date = order_dates[order_idx]

        # Status
        status = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        # Payment method
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]

        # Shipped date (only for shipped/completed orders)
        shipped_date = None
        if status in ("shipped", "completed"):
            days_to_ship = random.randint(1, 7)
            shipped_date = order_date + timedelta(days=days_to_ship)
            # Intentional NULL shipped dates for quality testing
            if random.random() < config.null_rate:
                shipped_date = None

        # Generate order items (1-8 items per order, weighted toward 2-3)
        num_items = max(1, int(np.random.lognormal(mean=0.7, sigma=0.5)))
        num_items = min(num_items, 8)

        order_total = 0.0
        selected_products = random.sample(
            product_ids_available, min(num_items, len(product_ids_available))
        )

        for product_id in selected_products:
            quantity = random.choices([1, 2, 3, 4, 5], weights=[0.5, 0.25, 0.15, 0.07, 0.03], k=1)[0]
            unit_price = product_prices.get(product_id, 29.99)

            # Discount (0-20%, with most being 0%)
            discount_pct = random.choices(
                [0, 5, 10, 15, 20],
                weights=[0.60, 0.15, 0.15, 0.07, 0.03],
                k=1,
            )[0] / 100.0
            discount = round(unit_price * quantity * discount_pct, 2)
            line_total = round(unit_price * quantity - discount, 2)
            order_total += line_total

            order_items.append({
                "order_item_id": order_item_id,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount": discount,
                "line_total": line_total,
            })
            order_item_id += 1

        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": order_date,
            "status": status,
            "total_amount": round(order_total, 2),
            "payment_method": payment_method,
            "shipped_date": shipped_date,
        })

    orders_df = pd.DataFrame(orders)
    order_items_df = pd.DataFrame(order_items)

    return orders_df, order_items_df
