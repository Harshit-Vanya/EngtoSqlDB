"""Base configuration for data generators.

Defines generation parameters and shared utilities.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class GenerationConfig:
    """Configuration for data generation volumes."""

    num_regions: int = 10
    num_categories: int = 20
    num_products: int = 200
    num_customers: int = 1000
    num_orders: int = 10000
    avg_items_per_order: float = 3.0
    # Date range for orders
    order_start_date: date = date(2023, 1, 1)
    order_end_date: date = date(2025, 6, 30)
    # Seed for reproducibility
    random_seed: int = 42
    # Quality edge cases
    null_rate: float = 0.02  # 2% NULLs in optional fields
    duplicate_rate: float = 0.005  # 0.5% duplicate records
    invalid_date_rate: float = 0.001  # 0.1% invalid date entries


# Default config
DEFAULT_CONFIG = GenerationConfig()
