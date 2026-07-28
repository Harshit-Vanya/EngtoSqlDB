"""Data Pipeline Orchestrator — local development mode.

This module demonstrates the complete data pipeline flow:
  Raw CSVs → Staging (cleaned) → Analytics (aggregated)

In production, this would be orchestrated by <DATA_ORCHESTRATOR> (e.g., Dagster, Airflow).
For local development, it runs as a simple sequential Python script.

Usage:
    python -m data_pipeline.pipeline [--input-dir data/sample] [--output-dir data/analytics]
"""

import argparse
from pathlib import Path

import pandas as pd

from data_pipeline.quality.checks import run_all_checks
from data_pipeline.transformations.raw_to_staging import (
    stage_customers,
    stage_order_items,
    stage_orders,
    stage_products,
)
from data_pipeline.transformations.staging_to_analytics import (
    build_fct_customer_summary,
    build_fct_daily_revenue,
    build_fct_product_performance,
)


def run_pipeline(input_dir: str = "data/sample", output_dir: str = "data/analytics") -> dict:
    """Execute the full data pipeline: raw → staging → analytics.

    Args:
        input_dir: Directory containing raw CSV files.
        output_dir: Directory to write analytics output.

    Returns:
        Dictionary with pipeline execution results.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Data Pipeline — Local Development Mode")
    print("=" * 60)

    # ─── Step 1: Load Raw Data ───
    print("\n[1/4] Loading raw data...")
    raw_data = {
        "regions": pd.read_csv(input_path / "regions.csv"),
        "categories": pd.read_csv(input_path / "categories.csv"),
        "products": pd.read_csv(input_path / "products.csv"),
        "customers": pd.read_csv(input_path / "customers.csv"),
        "orders": pd.read_csv(input_path / "orders.csv"),
        "order_items": pd.read_csv(input_path / "order_items.csv"),
    }
    for name, df in raw_data.items():
        print(f"  ✓ {name}: {len(df)} rows")

    # ─── Step 2: Data Quality Checks (Raw) ───
    print("\n[2/4] Running data quality checks on raw data...")
    quality_report = run_all_checks(raw_data)
    print(f"  {quality_report.summary()}")
    for result in quality_report.results:
        icon = "✓" if result.status.value == "pass" else "⚠" if result.status.value == "warn" else "✗"
        print(f"    {icon} [{result.status.value.upper()}] {result.message}")

    # ─── Step 3: Staging Transformations ───
    print("\n[3/4] Running staging transformations...")
    staged_data = {
        "regions": raw_data["regions"],  # Regions/categories pass through
        "categories": raw_data["categories"],
        "products": stage_products(raw_data["products"]),
        "customers": stage_customers(raw_data["customers"]),
        "orders": stage_orders(raw_data["orders"]),
        "order_items": stage_order_items(raw_data["order_items"]),
    }

    # Report staging validity
    for name in ["products", "customers", "orders", "order_items"]:
        df = staged_data[name]
        valid_count = df["_is_valid"].sum()
        invalid_count = len(df) - valid_count
        print(f"  ✓ {name}: {valid_count} valid, {invalid_count} flagged")

    # ─── Step 4: Analytics Transformations ───
    print("\n[4/4] Building analytics tables...")

    fct_daily_revenue = build_fct_daily_revenue(staged_data["orders"], staged_data["order_items"])
    print(f"  ✓ fct_daily_revenue: {len(fct_daily_revenue)} rows")

    fct_product_perf = build_fct_product_performance(
        staged_data["products"], staged_data["order_items"], staged_data["orders"]
    )
    print(f"  ✓ fct_product_performance: {len(fct_product_perf)} rows")

    fct_customer_summary = build_fct_customer_summary(
        staged_data["customers"], staged_data["orders"], staged_data["order_items"]
    )
    print(f"  ✓ fct_customer_summary: {len(fct_customer_summary)} rows")

    # ─── Export Analytics ───
    print(f"\n  Exporting analytics to: {output_path}/")
    fct_daily_revenue.to_csv(output_path / "fct_daily_revenue.csv", index=False)
    fct_product_perf.to_csv(output_path / "fct_product_performance.csv", index=False)
    fct_customer_summary.to_csv(output_path / "fct_customer_summary.csv", index=False)

    # Summary
    print("\n" + "=" * 60)
    print("  Pipeline complete!")
    print(f"  Quality: {quality_report.summary()}")
    print(f"  Analytics tables: 3 fact tables generated")
    print("=" * 60)

    return {
        "quality_report": quality_report,
        "raw_row_count": sum(len(df) for df in raw_data.values()),
        "analytics_tables": {
            "fct_daily_revenue": len(fct_daily_revenue),
            "fct_product_performance": len(fct_product_perf),
            "fct_customer_summary": len(fct_customer_summary),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the data pipeline")
    parser.add_argument("--input-dir", default="data/sample", help="Input CSV directory")
    parser.add_argument("--output-dir", default="data/analytics", help="Output directory")
    args = parser.parse_args()

    run_pipeline(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
