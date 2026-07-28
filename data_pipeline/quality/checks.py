"""Data quality checks for the pipeline.

Provides reusable check functions that validate DataFrame integrity
at each pipeline stage. Returns structured results with pass/fail/warning.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class CheckResult:
    """Result of a single data quality check."""

    check_name: str
    status: CheckStatus
    table_name: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Aggregated quality report for a pipeline run."""

    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.FAIL)

    @property
    def warnings(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.WARN)

    @property
    def is_healthy(self) -> bool:
        return self.failed == 0

    def summary(self) -> str:
        return (
            f"Quality Report: {self.passed} passed, {self.warnings} warnings, "
            f"{self.failed} failed — {'HEALTHY' if self.is_healthy else 'UNHEALTHY'}"
        )


# --- Check Functions ---


def check_not_empty(df: pd.DataFrame, table_name: str) -> CheckResult:
    """Check that the DataFrame is not empty."""
    if len(df) == 0:
        return CheckResult(
            check_name="not_empty",
            status=CheckStatus.FAIL,
            table_name=table_name,
            message=f"Table '{table_name}' is empty",
        )
    return CheckResult(
        check_name="not_empty",
        status=CheckStatus.PASS,
        table_name=table_name,
        message=f"Table '{table_name}' has {len(df)} rows",
        details={"row_count": len(df)},
    )


def check_no_duplicates(df: pd.DataFrame, table_name: str, key_columns: list[str]) -> CheckResult:
    """Check for duplicate rows based on key columns."""
    duplicates = df.duplicated(subset=key_columns, keep=False).sum()
    if duplicates > 0:
        dup_rate = duplicates / len(df)
        status = CheckStatus.FAIL if dup_rate > 0.01 else CheckStatus.WARN
        return CheckResult(
            check_name="no_duplicates",
            status=status,
            table_name=table_name,
            message=f"Found {duplicates} duplicate rows in '{table_name}' on columns {key_columns}",
            details={"duplicate_count": duplicates, "duplicate_rate": round(dup_rate, 4)},
        )
    return CheckResult(
        check_name="no_duplicates",
        status=CheckStatus.PASS,
        table_name=table_name,
        message=f"No duplicates in '{table_name}' on {key_columns}",
    )


def check_null_rate(
    df: pd.DataFrame, table_name: str, column: str, max_null_rate: float = 0.05
) -> CheckResult:
    """Check that NULL rate for a column is within acceptable limits."""
    null_count = df[column].isna().sum()
    null_rate = null_count / len(df) if len(df) > 0 else 0

    if null_rate > max_null_rate:
        return CheckResult(
            check_name="null_rate",
            status=CheckStatus.WARN,
            table_name=table_name,
            message=f"Column '{table_name}.{column}' has {null_rate:.1%} NULLs (threshold: {max_null_rate:.1%})",
            details={"null_count": null_count, "null_rate": round(null_rate, 4)},
        )
    return CheckResult(
        check_name="null_rate",
        status=CheckStatus.PASS,
        table_name=table_name,
        message=f"Column '{table_name}.{column}' NULL rate: {null_rate:.1%} (OK)",
        details={"null_count": null_count, "null_rate": round(null_rate, 4)},
    )


def check_referential_integrity(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    child_table: str,
    parent_table: str,
    child_column: str,
    parent_column: str,
) -> CheckResult:
    """Check that all foreign key values exist in the parent table."""
    child_values = set(child_df[child_column].dropna().unique())
    parent_values = set(parent_df[parent_column].unique())
    orphans = child_values - parent_values

    if orphans:
        return CheckResult(
            check_name="referential_integrity",
            status=CheckStatus.FAIL,
            table_name=child_table,
            message=(
                f"Referential integrity violation: {len(orphans)} values in "
                f"'{child_table}.{child_column}' not found in '{parent_table}.{parent_column}'"
            ),
            details={"orphan_count": len(orphans), "sample_orphans": list(orphans)[:5]},
        )
    return CheckResult(
        check_name="referential_integrity",
        status=CheckStatus.PASS,
        table_name=child_table,
        message=f"FK '{child_table}.{child_column}' → '{parent_table}.{parent_column}' OK",
    )


def check_value_range(
    df: pd.DataFrame, table_name: str, column: str, min_val: float | None = None, max_val: float | None = None
) -> CheckResult:
    """Check that numeric values are within expected range."""
    values = df[column].dropna()
    if len(values) == 0:
        return CheckResult(
            check_name="value_range",
            status=CheckStatus.WARN,
            table_name=table_name,
            message=f"Column '{table_name}.{column}' has no non-null values to check",
        )

    violations = 0
    if min_val is not None:
        violations += (values < min_val).sum()
    if max_val is not None:
        violations += (values > max_val).sum()

    if violations > 0:
        return CheckResult(
            check_name="value_range",
            status=CheckStatus.WARN,
            table_name=table_name,
            message=f"Column '{table_name}.{column}' has {violations} values outside range [{min_val}, {max_val}]",
            details={"violations": violations, "min_actual": float(values.min()), "max_actual": float(values.max())},
        )
    return CheckResult(
        check_name="value_range",
        status=CheckStatus.PASS,
        table_name=table_name,
        message=f"Column '{table_name}.{column}' values in range [{min_val}, {max_val}]",
    )


def run_all_checks(data: dict[str, pd.DataFrame]) -> QualityReport:
    """Run all data quality checks against the provided datasets.

    Args:
        data: Dictionary of table_name → DataFrame

    Returns:
        QualityReport with all check results.
    """
    report = QualityReport()

    # Non-empty checks
    for table_name, df in data.items():
        report.results.append(check_not_empty(df, table_name))

    # Duplicate checks
    report.results.append(check_no_duplicates(data["customers"], "customers", ["customer_id"]))
    report.results.append(check_no_duplicates(data["products"], "products", ["product_id"]))
    report.results.append(check_no_duplicates(data["orders"], "orders", ["order_id"]))

    # NULL rate checks
    report.results.append(check_null_rate(data["customers"], "customers", "email", max_null_rate=0.0))
    report.results.append(check_null_rate(data["customers"], "customers", "phone", max_null_rate=0.05))
    report.results.append(check_null_rate(data["orders"], "orders", "shipped_date", max_null_rate=0.30))
    report.results.append(check_null_rate(data["products"], "products", "supplier", max_null_rate=0.05))

    # Referential integrity
    report.results.append(check_referential_integrity(
        data["customers"], data["regions"], "customers", "regions", "region_id", "region_id"
    ))
    report.results.append(check_referential_integrity(
        data["orders"], data["customers"], "orders", "customers", "customer_id", "customer_id"
    ))
    report.results.append(check_referential_integrity(
        data["order_items"], data["orders"], "order_items", "orders", "order_id", "order_id"
    ))
    report.results.append(check_referential_integrity(
        data["order_items"], data["products"], "order_items", "products", "product_id", "product_id"
    ))
    report.results.append(check_referential_integrity(
        data["products"], data["categories"], "products", "categories", "category_id", "category_id"
    ))

    # Value range checks
    report.results.append(check_value_range(data["products"], "products", "price", min_val=0))
    report.results.append(check_value_range(data["order_items"], "order_items", "quantity", min_val=1))
    report.results.append(check_value_range(data["order_items"], "order_items", "unit_price", min_val=0))

    return report
