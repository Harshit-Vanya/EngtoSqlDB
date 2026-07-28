"""Seed the analytics database with generated sample data.

This script:
1. Creates the analytics tables (regions, categories, products, customers, orders, order_items)
2. Generates realistic sample data using the generators
3. Loads data into the database via SQLAlchemy
4. Optionally exports to CSV for local dev without a running DB

Usage:
    python -m data_pipeline.seeds.seed_database [--csv-only] [--db-url URL]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from data_pipeline.generators.base import DEFAULT_CONFIG, GenerationConfig
from data_pipeline.generators.customers import generate_customers
from data_pipeline.generators.orders import generate_orders
from data_pipeline.generators.products import generate_products
from data_pipeline.generators.regions import generate_categories, generate_regions

# SQL DDL for analytics tables
ANALYTICS_SCHEMA_DDL = """
-- Drop tables if they exist (for re-seeding)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- Regions
CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    continent VARCHAR(50) NOT NULL
);

-- Categories
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(category_id)
);

-- Products
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    supplier VARCHAR(200),
    created_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Customers
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    region_id INTEGER NOT NULL REFERENCES regions(region_id),
    signup_date DATE,
    segment VARCHAR(50)
);

-- Orders
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    payment_method VARCHAR(50),
    shipped_date DATE
);

-- Order Items
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0,
    line_total DECIMAL(12, 2) NOT NULL
);

-- Indexes
CREATE INDEX idx_customers_region ON customers(region_id);
CREATE INDEX idx_customers_segment ON customers(segment);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category_id);
"""


def generate_all_data(config: GenerationConfig | None = None) -> dict[str, pd.DataFrame]:
    """Generate all datasets and return as a dictionary of DataFrames."""
    if config is None:
        config = DEFAULT_CONFIG

    print(f"Generating data with config: {config.num_customers} customers, "
          f"{config.num_orders} orders, {config.num_products} products...")

    regions_df = generate_regions()
    print(f"  ✓ Regions: {len(regions_df)} records")

    categories_df = generate_categories()
    print(f"  ✓ Categories: {len(categories_df)} records")

    products_df = generate_products(config)
    print(f"  ✓ Products: {len(products_df)} records")

    customers_df = generate_customers(config)
    print(f"  ✓ Customers: {len(customers_df)} records")

    orders_df, order_items_df = generate_orders(config, products_df)
    print(f"  ✓ Orders: {len(orders_df)} records")
    print(f"  ✓ Order Items: {len(order_items_df)} records")

    total_records = sum(len(df) for df in [
        regions_df, categories_df, products_df, customers_df, orders_df, order_items_df
    ])
    print(f"\n  Total records generated: {total_records:,}")

    return {
        "regions": regions_df,
        "categories": categories_df,
        "products": products_df,
        "customers": customers_df,
        "orders": orders_df,
        "order_items": order_items_df,
    }


def export_to_csv(data: dict[str, pd.DataFrame], output_dir: str = "data/sample") -> None:
    """Export all DataFrames to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for name, df in data.items():
        filepath = output_path / f"{name}.csv"
        df.to_csv(filepath, index=False)
        print(f"  Exported: {filepath} ({len(df)} rows)")

    print(f"\n  All CSVs exported to: {output_path}/")


def load_to_database(data: dict[str, pd.DataFrame], db_url: str) -> None:
    """Load data into the database.

    Creates schema, then bulk inserts all data.
    """
    # Convert async URL to sync if needed
    sync_url = db_url.replace("+asyncpg", "").replace("+aiosqlite", "")
    engine = create_engine(sync_url)

    print(f"\n  Connecting to: {sync_url.split('@')[-1] if '@' in sync_url else sync_url}")

    with engine.connect() as conn:
        # Create schema
        print("  Creating analytics schema...")
        for statement in ANALYTICS_SCHEMA_DDL.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
        print("  ✓ Schema created")

        # Load data in order (respecting foreign keys)
        load_order = ["regions", "categories", "products", "customers", "orders", "order_items"]
        for table_name in load_order:
            df = data[table_name]
            df.to_sql(table_name, conn, if_exists="append", index=False, method="multi")
            print(f"  ✓ Loaded {table_name}: {len(df)} rows")

        conn.commit()

    engine.dispose()
    print("\n  ✓ Database seeded successfully!")


def main() -> None:
    """Main entry point for the seed script."""
    parser = argparse.ArgumentParser(description="Seed the analytics database")
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Only export to CSV, don't load to database",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (overrides settings)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/sample",
        help="CSV output directory",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  AI-Text-to-SQL — Data Seed Script")
    print("=" * 60)

    # Generate data
    data = generate_all_data()

    # Always export to CSV
    print("\nExporting to CSV...")
    export_to_csv(data, args.output_dir)

    # Load to database unless --csv-only
    if not args.csv_only:
        if args.db_url:
            db_url = args.db_url
        else:
            try:
                from backend.app.core.config import get_settings
                db_url = get_settings().analytics_database_url
            except Exception:
                print("\n  ⚠ No database URL configured. Use --db-url or set ANALYTICS_DATABASE_URL")
                print("  Data exported to CSV only. Load to DB with:")
                print(f"    python -m data_pipeline.seeds.seed_database --db-url <URL>")
                return

        print(f"\nLoading to database...")
        try:
            load_to_database(data, db_url)
        except Exception as e:
            print(f"\n  ✗ Database load failed: {e}")
            print("  CSVs are still available. You can load them manually.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  Seed complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
