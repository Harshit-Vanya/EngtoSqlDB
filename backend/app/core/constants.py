"""Application-wide constants."""

# SQL operations that are always blocked
BLOCKED_SQL_OPERATIONS: set[str] = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "MERGE",
    "UPSERT",
    "REPLACE",
}

# Allowed SQL operations
ALLOWED_SQL_OPERATIONS: set[str] = {"SELECT"}

# Risk levels
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"

# Query execution statuses
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_REJECTED = "rejected"
STATUS_TIMEOUT = "timeout"

# Validation statuses
VALIDATION_PENDING = "pending"
VALIDATION_VALID = "valid"
VALIDATION_INVALID = "invalid"

# Security statuses
SECURITY_PENDING = "pending"
SECURITY_ALLOWED = "allowed"
SECURITY_DENIED = "denied"

# Intent categories
INTENT_AGGREGATION = "aggregation"
INTENT_COMPARISON = "comparison"
INTENT_TREND = "trend"
INTENT_DETAIL = "detail"
INTENT_DEFINITION = "definition"
INTENT_COUNT = "count"
INTENT_RANKING = "ranking"
INTENT_GENERAL = "general"

INTENT_CATEGORIES: list[str] = [
    INTENT_AGGREGATION,
    INTENT_COMPARISON,
    INTENT_TREND,
    INTENT_DETAIL,
    INTENT_DEFINITION,
    INTENT_COUNT,
    INTENT_RANKING,
    INTENT_GENERAL,
]

# Visualization chart types
CHART_BAR = "bar"
CHART_LINE = "line"
CHART_PIE = "pie"
CHART_KPI = "kpi_card"
CHART_TABLE = "table"
CHART_HORIZONTAL_BAR = "horizontal_bar"
CHART_SCATTER = "scatter"
CHART_MULTI_LINE = "multi_line"

# User roles
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_BUSINESS_USER = "business_user"
ROLE_RESTRICTED = "restricted"

ALL_ROLES: list[str] = [ROLE_ADMIN, ROLE_ANALYST, ROLE_BUSINESS_USER, ROLE_RESTRICTED]

# Database dialect
DB_DIALECT_POSTGRESQL = "postgresql"
DB_DIALECT_MYSQL = "mysql"
DB_DIALECT_SQLITE = "sqlite"
