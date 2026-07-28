# Phase 5 — API Design

## 5.1 API Overview

| Base URL | Version | Auth | Content-Type |
|----------|---------|------|-------------|
| `/api/v1` | v1 (URL-based versioning) | Bearer JWT / API Key | application/json |

### Common Headers (all requests)

```text
Authorization: Bearer <token>  OR  X-API-Key: <api_key>
Content-Type: application/json
X-Request-ID: <uuid> (optional, server generates if absent)
```

### Common Response Envelope

All responses follow a consistent structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": {
    "request_id": "uuid",
    "timestamp": "ISO-8601",
    "latency_ms": 123
  }
}
```

Error envelope:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [ ... ]
  },
  "metadata": { ... }
}
```

---

## 5.2 Endpoints

### 5.2.1 Query Endpoints

#### `POST /api/v1/query` — Submit Natural Language Query

Full pipeline: intent → RAG → generate → validate → execute → explain.

**Request:**
```json
{
  "question": "Show me the top 5 products by revenue last quarter",
  "options": {
    "execute": true,
    "explain": true,
    "visualize": true,
    "max_rows": 1000,
    "timeout_seconds": 30
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "query_id": "550e8400-e29b-41d4-a716-446655440000",
    "original_question": "Show me the top 5 products by revenue last quarter",
    "intent": {
      "category": "aggregation",
      "entities": ["products", "revenue"],
      "time_range": "last_quarter"
    },
    "sql": {
      "generated": "SELECT p.product_name, SUM(oi.line_total) AS revenue\nFROM products p\nJOIN order_items oi ON oi.product_id = p.product_id\nJOIN orders o ON o.order_id = oi.order_id\nWHERE o.order_date >= date_trunc('quarter', CURRENT_DATE - INTERVAL '3 months')\n  AND o.order_date < date_trunc('quarter', CURRENT_DATE)\nGROUP BY p.product_name\nORDER BY revenue DESC\nLIMIT 5",
      "tables_used": ["products", "order_items", "orders"],
      "columns_used": ["product_name", "line_total", "product_id", "order_id", "order_date"],
      "confidence": 0.92
    },
    "validation": {
      "is_valid": true,
      "risk_level": "LOW",
      "warnings": []
    },
    "execution": {
      "status": "success",
      "rows_returned": 5,
      "execution_time_ms": 42.5,
      "columns": [
        {"name": "product_name", "type": "varchar"},
        {"name": "revenue", "type": "numeric"}
      ],
      "rows": [
        ["Wireless Headphones", 125400.50],
        ["Smart Watch Pro", 98200.00],
        ["Laptop Stand", 87600.75],
        ["USB-C Hub", 76500.25],
        ["Mechanical Keyboard", 65800.00]
      ]
    },
    "visualization": {
      "chart_type": "bar",
      "config": {
        "x_axis": "product_name",
        "y_axis": "revenue",
        "title": "Top 5 Products by Revenue (Last Quarter)",
        "sort": "descending"
      }
    },
    "explanation": "Wireless Headphones generated the highest revenue at $125,400.50 last quarter, followed by Smart Watch Pro at $98,200. The top 5 products account for a combined revenue of $453,501.50.",
    "metadata": {
      "retry_count": 0,
      "total_latency_ms": 2340,
      "llm_tokens_used": 850,
      "estimated_llm_cost_usd": 0.0034
    }
  },
  "metadata": {
    "request_id": "req-abc123",
    "timestamp": "2026-07-29T03:00:00Z",
    "latency_ms": 2340
  }
}
```

**Error Responses:**
| Status | Code | Scenario |
|--------|------|----------|
| 400 | INVALID_REQUEST | Missing/malformed question |
| 401 | UNAUTHORIZED | Invalid/expired token |
| 403 | ACCESS_DENIED | User lacks permission for requested tables |
| 422 | SQL_GENERATION_FAILED | LLM couldn't generate valid SQL after retries |
| 429 | RATE_LIMITED | Too many requests |
| 503 | LLM_UNAVAILABLE | LLM provider down |

---

#### `POST /api/v1/query/validate` — Validate Only (No Execution)

Runs intent → RAG → generate → validate pipeline without executing.

**Request:**
```json
{
  "question": "Delete all orders from last year"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "query_id": "550e8400-...",
    "original_question": "Delete all orders from last year",
    "sql": {
      "generated": "DELETE FROM orders WHERE ...",
      "tables_used": ["orders"],
      "confidence": 0.85
    },
    "validation": {
      "is_valid": false,
      "risk_level": "CRITICAL",
      "errors": [
        {
          "code": "WRITE_OPERATION_BLOCKED",
          "message": "DELETE operations are not allowed. Only SELECT queries are permitted."
        }
      ],
      "warnings": []
    },
    "execution": null,
    "visualization": null,
    "explanation": null
  }
}
```

---

#### `GET /api/v1/query/{query_id}` — Get Query Record

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "query_id": "550e8400-...",
    "original_question": "...",
    "sql": { ... },
    "validation": { ... },
    "execution": { ... },
    "visualization": { ... },
    "explanation": "...",
    "corrections": [
      {
        "attempt": 1,
        "original_sql": "...",
        "error": "column 'revenue' does not exist",
        "corrected_sql": "...",
        "status": "success"
      }
    ],
    "metadata": { ... },
    "created_at": "2026-07-29T03:00:00Z"
  }
}
```

**Error Responses:**
| Status | Code | Scenario |
|--------|------|----------|
| 404 | NOT_FOUND | Query ID doesn't exist |
| 403 | ACCESS_DENIED | User doesn't own this query (non-admin) |

---

#### `GET /api/v1/query/history` — Query History

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Results per page (max 100) |
| status | string | null | Filter by execution_status |
| from_date | ISO date | null | Start date filter |
| to_date | ISO date | null | End date filter |
| sort_by | string | created_at | Sort column |
| sort_order | string | desc | asc or desc |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "queries": [
      {
        "query_id": "...",
        "original_question": "...",
        "execution_status": "success",
        "rows_returned": 5,
        "total_latency_ms": 2340,
        "created_at": "2026-07-29T03:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 142,
      "total_pages": 8
    }
  }
}
```

---

### 5.2.2 Schema Endpoints

#### `GET /api/v1/schema` — List Available Schema

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| database | string | null | Filter by database |
| table | string | null | Filter by specific table |
| include_columns | bool | true | Include column details |
| include_relationships | bool | false | Include FK relationships |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tables": [
      {
        "table_name": "orders",
        "schema_name": "public",
        "description": "Customer order transactions",
        "row_count_estimate": 10000,
        "columns": [
          {
            "name": "order_id",
            "type": "integer",
            "is_primary_key": true,
            "is_nullable": false,
            "description": "Unique order identifier"
          },
          {
            "name": "customer_id",
            "type": "integer",
            "is_foreign_key": true,
            "references": "customers.customer_id",
            "description": "Customer who placed the order"
          }
        ],
        "relationships": [
          {
            "type": "belongs_to",
            "target_table": "customers",
            "join_column": "customer_id"
          }
        ]
      }
    ],
    "glossary_terms": ["revenue", "active customer", "churn"],
    "available_metrics": ["total_revenue", "avg_order_value", "customer_lifetime_value"]
  }
}
```

---

#### `GET /api/v1/schema/glossary` — Business Glossary

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "terms": [
      {
        "term": "revenue",
        "definition": "Sum of line_total from order_items for completed orders",
        "sql_formula": "SUM(oi.line_total) WHERE o.status = 'completed'",
        "related_tables": ["order_items", "orders"],
        "synonyms": ["sales", "income", "earnings"]
      }
    ]
  }
}
```

---

#### `GET /api/v1/schema/metrics` — Available Metrics

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "name": "total_revenue",
        "description": "Total revenue from completed orders",
        "formula": "SUM(order_items.line_total)",
        "aggregation": "sum",
        "required_tables": ["order_items", "orders"],
        "filters": "orders.status = 'completed'"
      }
    ]
  }
}
```

---

### 5.2.3 Authentication Endpoints

#### `POST /api/v1/auth/login` — User Login

**Request:**
```json
{
  "email": "analyst@company.com",
  "password": "secure_password"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "user-uuid",
      "email": "analyst@company.com",
      "display_name": "Jane Analyst",
      "roles": ["analyst"]
    }
  }
}
```

**Error Responses:**
| Status | Code | Scenario |
|--------|------|----------|
| 401 | INVALID_CREDENTIALS | Wrong email/password |
| 423 | ACCOUNT_LOCKED | Too many failed attempts |

---

#### `POST /api/v1/auth/refresh` — Refresh Token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "new_token...",
    "expires_in": 3600
  }
}
```

---

#### `POST /api/v1/auth/api-keys` — Create API Key

**Request:**
```json
{
  "name": "My Integration Key",
  "expires_in_days": 90
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "key_id": "key-uuid",
    "api_key": "ntq_abc123...xyz789",
    "prefix": "ntq_abc1",
    "name": "My Integration Key",
    "expires_at": "2026-10-27T03:00:00Z",
    "warning": "Store this key securely. It will not be shown again."
  }
}
```

---

### 5.2.4 Admin Endpoints

#### `GET /api/v1/admin/metrics` — System Metrics

**Requires role: admin**

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "queries": {
      "total_today": 342,
      "success_rate": 0.94,
      "avg_latency_ms": 2100,
      "correction_rate": 0.15
    },
    "llm": {
      "total_tokens_today": 125000,
      "estimated_cost_today_usd": 0.52,
      "avg_tokens_per_query": 365
    },
    "system": {
      "active_users_today": 12,
      "error_rate": 0.03,
      "p95_latency_ms": 4500,
      "p99_latency_ms": 8200
    }
  }
}
```

---

#### `GET /api/v1/admin/users` — List Users (Admin)

**Query Parameters:** page, page_size, role, is_active

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "user-uuid",
        "email": "analyst@company.com",
        "display_name": "Jane Analyst",
        "roles": ["analyst"],
        "is_active": true,
        "query_count": 142,
        "last_login_at": "2026-07-29T02:00:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

---

### 5.2.5 Health & System Endpoints

#### `GET /api/v1/health` — Health Check (No Auth)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 86400
  }
}
```

---

#### `GET /api/v1/health/readiness` — Readiness Probe

Checks all dependencies are reachable.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "ready",
    "checks": {
      "database": {"status": "up", "latency_ms": 2},
      "vector_store": {"status": "up", "latency_ms": 5},
      "llm_provider": {"status": "up", "latency_ms": 150}
    }
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "success": false,
  "data": {
    "status": "not_ready",
    "checks": {
      "database": {"status": "up", "latency_ms": 2},
      "vector_store": {"status": "down", "error": "connection refused"},
      "llm_provider": {"status": "up", "latency_ms": 150}
    }
  }
}
```

---

## 5.3 Error Code Reference

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | INVALID_REQUEST | Malformed request body |
| 400 | INVALID_PARAMETER | Invalid query parameter |
| 401 | UNAUTHORIZED | Missing or invalid auth |
| 401 | TOKEN_EXPIRED | JWT expired |
| 403 | ACCESS_DENIED | Insufficient permissions |
| 403 | TABLE_ACCESS_DENIED | No access to specific table |
| 403 | COLUMN_ACCESS_DENIED | No access to specific column |
| 404 | NOT_FOUND | Resource not found |
| 409 | DUPLICATE_RESOURCE | Resource already exists |
| 422 | SQL_GENERATION_FAILED | Could not generate valid SQL |
| 422 | VALIDATION_FAILED | SQL failed validation |
| 422 | COST_LIMIT_EXCEEDED | Query too expensive |
| 429 | RATE_LIMITED | Rate limit exceeded |
| 500 | INTERNAL_ERROR | Unexpected server error |
| 503 | SERVICE_UNAVAILABLE | Dependency down |
| 503 | LLM_UNAVAILABLE | LLM provider unreachable |

---

## 5.4 Rate Limiting

| Role | Requests/minute | Queries/hour |
|------|----------------|-------------|
| admin | 120 | unlimited |
| analyst | 60 | 100 |
| business_user | 30 | 50 |
| restricted | 10 | 20 |

Rate limit headers included in every response:
```text
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1722222000
```

---

## 5.5 WebSocket (Optional — Streaming Results)

For long-running queries, an optional WebSocket endpoint enables streaming:

```text
WS /api/v1/query/stream
```

Message flow:
```json
→ {"type": "query", "question": "...", "options": {...}}
← {"type": "status", "state": "intent_detection", "message": "Analyzing question..."}
← {"type": "status", "state": "context_retrieval", "message": "Retrieving schema context..."}
← {"type": "status", "state": "sql_generation", "message": "Generating SQL..."}
← {"type": "sql_preview", "sql": "SELECT ..."}
← {"type": "status", "state": "execution", "message": "Executing query..."}
← {"type": "result", "data": {...}}
```

This is a P2 (Nice to Have) feature.
