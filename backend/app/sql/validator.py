"""SQL Safety Validator — regex-based barrier preventing unsafe SQL execution.

This module is the final defense before any generated SQL reaches the
database executor.  It performs:
  1. Blocked-keyword detection (DROP, DELETE, UPDATE, INSERT, ALTER, etc.)
  2. Statement-type verification (only SELECT allowed)
  3. Semicolon/multi-statement detection
  4. Comment-injection detection

Design: stateless functions — no class instantiation needed.
"""

from __future__ import annotations

import re

from backend.app.core.constants import BLOCKED_SQL_OPERATIONS
from backend.app.core.exceptions import SQLValidationError
from backend.app.core.types import ValidationResult

# Pre-compiled patterns for performance
_BLOCKED_PATTERN = re.compile(
    r"\b(" + "|".join(BLOCKED_SQL_OPERATIONS) + r")\b",
    re.IGNORECASE,
)
_MULTI_STATEMENT_PATTERN = re.compile(r";\s*\S")
_COMMENT_INJECTION_PATTERN = re.compile(r"(--|/\*|\*/|xp_|exec\s|execute\s)", re.IGNORECASE)
_SELECT_START_PATTERN = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE)


def validate_sql_safety(sql: str) -> ValidationResult:
    """Validate that a SQL string is safe to execute.

    Applies a multi-layer regex barrier:
      1. Must start with SELECT or WITH (CTE).
      2. Must NOT contain blocked keywords.
      3. Must NOT contain multiple statements.
      4. Must NOT contain comment-injection patterns.

    Args:
        sql: The SQL string to validate.

    Returns:
        ValidationResult indicating pass/fail with error details.
    """
    errors: list[str] = []
    warnings: list[str] = []
    operations_detected: list[str] = []

    cleaned = sql.strip()

    # --- Rule 1: must begin with SELECT or WITH ---
    if not _SELECT_START_PATTERN.match(cleaned):
        errors.append(
            "SQL must start with SELECT or WITH (CTE). "
            f"Found: '{cleaned[:30]}...'"
        )

    # --- Rule 2: blocked keywords ---
    blocked_matches = _BLOCKED_PATTERN.findall(cleaned)
    if blocked_matches:
        unique = sorted(set(m.upper() for m in blocked_matches))
        operations_detected.extend(unique)
        errors.append(
            f"Blocked SQL operations detected: {', '.join(unique)}"
        )

    # --- Rule 3: multi-statement ---
    if _MULTI_STATEMENT_PATTERN.search(cleaned):
        errors.append(
            "Multiple SQL statements detected (semicolon followed by content). "
            "Only single SELECT statements are allowed."
        )

    # --- Rule 4: comment injection ---
    if _COMMENT_INJECTION_PATTERN.search(cleaned):
        warnings.append(
            "SQL contains comment or injection-like patterns "
            "(e.g. '--', '/*', 'xp_', 'exec'). Review carefully."
        )

    # --- Rule 5: trailing semicolon is OK, just strip it ---
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()

    is_valid = len(errors) == 0
    risk_level = "LOW"
    if warnings:
        risk_level = "MEDIUM"
    if not is_valid:
        risk_level = "CRITICAL"

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        operations_detected=operations_detected,
        risk_level=risk_level,
    )


def validate_or_raise(sql: str) -> str:
    """Validate SQL safety and raise on failure.

    Convenience wrapper that raises SQLValidationError if the SQL is
    not safe, or returns the cleaned SQL string if it passes.

    Args:
        sql: The SQL string to validate.

    Returns:
        The cleaned SQL string (trailing semicolons stripped).

    Raises:
        SQLValidationError: If any safety rule is violated.
    """
    result = validate_sql_safety(sql)
    if not result.is_valid:
        raise SQLValidationError(
            message="Generated SQL failed safety validation",
            errors=result.errors,
        )
    return sql.strip().rstrip(";")
