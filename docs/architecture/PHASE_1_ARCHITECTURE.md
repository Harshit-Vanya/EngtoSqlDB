# Phase 1 — Architecture

## 1.1 High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Frontend / UI]
    end

    subgraph "API Layer"
        GW[API Gateway]
        AUTH[Auth Middleware]
        RL[Rate Limiter]
        API[FastAPI Application]
    end

    subgraph "Orchestration Layer"
        QO[Query Orchestrator]
        SM[State Machine / Workflow Engine]
    end

    subgraph "Intelligence Layer"
        ID[Intent Detector]
        SIL[Schema Intelligence Layer]
        RAG[RAG Context Retriever]
        SQLGEN[SQL Generation Agent]
        CORR[Self-Correction Agent]
        EXPLAIN[Explanation Agent]
        VIZ[Visualization Recommender]
    end

    subgraph "Validation & Security Layer"
        SQLVAL[SQL Validator]
        SECVAL[Security & RBAC Validator]
        COSTVAL[Cost & Performance Validator]
    end

    subgraph "Execution Layer"
        EXEC[Query Executor]
        RP[Result Processor]
    end

    subgraph "Data & Storage Layer"
        PDB[("<PRIMARY_DATABASE>")]
        VDB[("<VECTOR_DATABASE>")]
        QHS[("<QUERY_HISTORY_STORE>")]
        OBJ[("<OBJECT_STORAGE>")]
    end

    subgraph "Observability Layer"
        LOG[Structured Logger]
        MET[Metrics Collector]
        TRACE[Distributed Tracer]
        OBS[("<OBSERVABILITY_PLATFORM>")]
    end

    subgraph "Data Engineering Layer"
        ING[Data Ingestion]
        ETL[ETL / ELT Pipeline]
        DQ[Data Quality Checks]
        ORCH[("<DATA_ORCHESTRATOR>")]
    end

    UI --> GW
    GW --> AUTH
    AUTH --> RL
    RL --> API
    API --> QO

    QO --> ID
    QO --> SIL
    QO --> RAG
    QO --> SQLGEN
    QO --> SQLVAL
    QO --> SECVAL
    QO --> COSTVAL
    QO --> EXEC
    QO --> RP
    QO --> VIZ
    QO --> EXPLAIN
    QO --> CORR

    SIL --> VDB
    SIL --> PDB
    RAG --> VDB
    SQLGEN --> LLM[("<LLM_PROVIDER>")]
    CORR --> LLM
    EXPLAIN --> LLM
    VIZ --> LLM

    EXEC --> PDB
    QO --> QHS

    LOG --> OBS
    MET --> OBS
    TRACE --> OBS

    ING --> OBJ
    OBJ --> ETL
    ETL --> PDB
    ORCH --> ETL
    DQ --> ETL
```

---

## 1.2 Component Architecture (Layered View)

```mermaid
graph LR
    subgraph "Layer 1: Presentation"
        A1[REST API Controllers]
        A2[WebSocket Handler]
        A3[Request/Response Schemas]
    end

    subgraph "Layer 2: Application Services"
        B1[Query Orchestrator Service]
        B2[Auth Service]
        B3[History Service]
        B4[Schema Service]
        B5[Evaluation Service]
    end

    subgraph "Layer 3: Domain / Core"
        C1[Intent Detection]
        C2[SQL Generation]
        C3[SQL Validation]
        C4[Security Engine]
        C5[Cost Analyzer]
        C6[Self-Correction]
        C7[Result Processing]
        C8[Visualization Engine]
        C9[Explanation Engine]
        C10[RAG Pipeline]
    end

    subgraph "Layer 4: Infrastructure / Adapters"
        D1[LLM Adapter]
        D2[Embedding Adapter]
        D3[Database Adapter]
        D4[Vector Store Adapter]
        D5[Object Storage Adapter]
        D6[Auth Provider Adapter]
        D7[Observability Adapter]
    end

    A1 --> B1
    A1 --> B2
    A1 --> B3
    A1 --> B4

    B1 --> C1
    B1 --> C2
    B1 --> C3
    B1 --> C4
    B1 --> C5
    B1 --> C6
    B1 --> C7
    B1 --> C8
    B1 --> C9
    B1 --> C10

    C1 --> D1
    C2 --> D1
    C6 --> D1
    C9 --> D1
    C10 --> D2
    C10 --> D4
    C3 --> D3
    C5 --> D3
    C7 --> D3
    B2 --> D6
    B1 --> D7
```

---

## 1.3 Component Descriptions

| Component | Responsibility | Key Interfaces |
|-----------|---------------|----------------|
| **API Gateway** | Request routing, CORS, request ID generation, API versioning | `handle_request()` |
| **Auth Middleware** | JWT/token validation, user extraction, session management | `authenticate()`, `get_current_user()` |
| **Rate Limiter** | Per-user and global rate limiting | `check_rate_limit()` |
| **Query Orchestrator** | Central coordinator — drives the entire query lifecycle as a state machine | `process_query()`, `get_state()` |
| **Intent Detector** | Classifies user question into categories (analytics, definition, comparison, aggregation) | `detect_intent()` |
| **Schema Intelligence Layer** | Manages metadata catalog — tables, columns, relationships, business definitions | `get_schema()`, `search_schema()` |
| **RAG Context Retriever** | Retrieves relevant schema, examples, glossary via vector similarity | `retrieve_context()` |
| **SQL Generation Agent** | Produces SQL from natural language + context | `generate_sql()` |
| **SQL Validator** | Parses and validates SQL syntax, checks for dangerous operations | `validate()` |
| **Security & RBAC Validator** | Enforces table/column/row-level access based on user role | `check_permissions()` |
| **Cost & Performance Validator** | Runs EXPLAIN, estimates cost, enforces limits | `estimate_cost()` |
| **Self-Correction Agent** | Receives errors, regenerates SQL with error context | `correct_sql()` |
| **Query Executor** | Executes validated SQL against the target database with timeouts | `execute()` |
| **Result Processor** | Formats raw DB results, handles pagination, NULL handling | `process_results()` |
| **Visualization Recommender** | Determines chart type from result shape and query intent | `recommend_visualization()` |
| **Explanation Agent** | Generates natural-language summary of results | `explain_results()` |
| **Observability** | Structured logging, metrics emission, distributed tracing | `log()`, `emit_metric()`, `trace()` |
| **Data Pipeline** | Ingests raw data, transforms to analytics-ready tables | `run_pipeline()` |

---

## 1.4 End-to-End Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant AUTH as Auth Service
    participant QO as Query Orchestrator
    participant ID as Intent Detector
    participant RAG as RAG Retriever
    participant SIL as Schema Intelligence
    participant GEN as SQL Generator
    participant VAL as SQL Validator
    participant SEC as Security Validator
    participant COST as Cost Validator
    participant EXEC as Query Executor
    participant CORR as Self-Correction
    participant RP as Result Processor
    participant VIZ as Visualization Engine
    participant EXP as Explanation Engine
    participant DB as <PRIMARY_DATABASE>
    participant VDB as <VECTOR_DATABASE>
    participant LLM as <LLM_PROVIDER>

    U->>FE: "Top 5 products by revenue last quarter"
    FE->>API: POST /api/v1/query {question, session_id}
    API->>AUTH: Validate token, extract user + role
    AUTH-->>API: {user_id, role, permissions}
    API->>QO: process_query(question, user_context)

    Note over QO: State: INTENT_DETECTION
    QO->>ID: detect_intent(question)
    ID->>LLM: Classify intent
    LLM-->>ID: {intent: "aggregation", entities: [...]}
    ID-->>QO: IntentResult

    Note over QO: State: CONTEXT_RETRIEVAL
    QO->>RAG: retrieve_context(question, intent)
    RAG->>VDB: similarity_search(embedding)
    VDB-->>RAG: relevant_chunks
    RAG->>SIL: get_schema_for_tables(tables)
    SIL-->>RAG: schema_details
    RAG-->>QO: RetrievedContext

    Note over QO: State: SQL_GENERATION
    QO->>GEN: generate_sql(question, context, permissions, dialect)
    GEN->>LLM: prompt with schema + question
    LLM-->>GEN: generated SQL
    GEN-->>QO: SQLGenerationResult

    Note over QO: State: VALIDATION
    QO->>VAL: validate(sql, schema_context)
    VAL-->>QO: ValidationResult {is_valid, errors, warnings}

    QO->>SEC: check_permissions(sql, user_permissions)
    SEC-->>QO: SecurityResult {allowed, violations}

    QO->>COST: estimate_cost(sql)
    COST->>DB: EXPLAIN sql
    DB-->>COST: query_plan
    COST-->>QO: CostResult {estimated_cost, within_limits}

    alt Validation/Security/Cost Failed
        Note over QO: State: SELF_CORRECTION
        QO->>CORR: correct_sql(sql, errors, context)
        CORR->>LLM: correction prompt
        LLM-->>CORR: corrected SQL
        CORR-->>QO: Loop back to VALIDATION (max N retries)
    end

    Note over QO: State: EXECUTION
    QO->>EXEC: execute(sql, timeout, max_rows)
    EXEC->>DB: Execute query
    DB-->>EXEC: raw results
    EXEC-->>QO: ExecutionResult

    Note over QO: State: POST_PROCESSING
    QO->>RP: process_results(raw_results)
    RP-->>QO: ProcessedResult {columns, rows, metadata}

    par Visualization & Explanation
        QO->>VIZ: recommend(processed_result, intent)
        VIZ-->>QO: VisualizationConfig {chart_type, axes, config}
        QO->>EXP: explain(question, sql, results)
        EXP->>LLM: explanation prompt
        LLM-->>EXP: natural language summary
        EXP-->>QO: Explanation
    end

    Note over QO: State: COMPLETE
    QO-->>API: QueryResponse
    API-->>FE: {query_id, sql, results, visualization, explanation, metadata}
    FE-->>U: Rendered results + chart + explanation
```

---

## 1.5 Data Flow Diagram

```mermaid
flowchart TD
    subgraph "Input"
        Q[User Question]
        UC[User Context: role, permissions]
    end

    subgraph "Context Assembly"
        EMB[Embed Question]
        VS[Vector Similarity Search]
        SR[Schema Retrieval]
        BR[Business Rules Retrieval]
        EQ[Example Query Retrieval]
        CTX[Assembled Context Package]
    end

    subgraph "SQL Pipeline"
        PROMPT[Prompt Construction]
        GEN[LLM SQL Generation]
        SQL[Generated SQL]
    end

    subgraph "Validation Pipeline"
        PARSE[SQL Parsing / AST]
        SYN[Syntax Validation]
        SEM[Semantic Validation: tables/columns exist]
        SECV[Security Validation: RBAC check]
        COSTV[Cost Validation: EXPLAIN analysis]
        VRES[Validation Result]
    end

    subgraph "Execution Pipeline"
        EXEC[Execute SQL]
        RAW[Raw Result Set]
        PROC[Process & Format]
        FINAL[Structured Result]
    end

    subgraph "Output Assembly"
        VIZR[Visualization Config]
        EXPR[AI Explanation]
        META[Query Metadata]
        RESP[Final Response]
    end

    Q --> EMB --> VS --> CTX
    Q --> SR --> CTX
    VS --> BR --> CTX
    VS --> EQ --> CTX

    UC --> PROMPT
    CTX --> PROMPT
    Q --> PROMPT
    PROMPT --> GEN --> SQL

    SQL --> PARSE --> SYN --> SEM --> SECV --> COSTV --> VRES

    VRES -->|Valid| EXEC
    VRES -->|Invalid| GEN

    EXEC --> RAW --> PROC --> FINAL

    FINAL --> VIZR --> RESP
    FINAL --> EXPR --> RESP
    FINAL --> META --> RESP
```

---

## 1.6 Agent / Workflow Architecture

```mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Authenticating
    Authenticating --> IntentDetection : auth_success
    Authenticating --> Rejected : auth_failed

    IntentDetection --> ContextRetrieval : intent_classified
    IntentDetection --> Failed : intent_error

    ContextRetrieval --> SQLGeneration : context_assembled
    ContextRetrieval --> Failed : retrieval_error

    SQLGeneration --> Validation : sql_generated
    SQLGeneration --> Failed : generation_error

    Validation --> SecurityCheck : syntax_valid
    Validation --> SelfCorrection : syntax_invalid

    SecurityCheck --> CostCheck : access_allowed
    SecurityCheck --> Rejected : access_denied

    CostCheck --> Execution : cost_acceptable
    CostCheck --> CostWarning : cost_high

    CostWarning --> Rejected : user_declined
    CostWarning --> Execution : user_approved

    Execution --> ResultProcessing : execution_success
    Execution --> SelfCorrection : execution_error

    SelfCorrection --> Validation : retry_count < max
    SelfCorrection --> Failed : retry_count >= max

    ResultProcessing --> PostProcessing
    
    PostProcessing --> Completed : all_done

    Completed --> [*]
    Rejected --> [*]
    Failed --> [*]
```

### Agent Node Descriptions

| Node | Agent Type | LLM Required | Description |
|------|-----------|:---:|-------------|
| Intent Detection | LLM Agent | ✓ | Classifies question type, extracts entities, determines DB dialect needs |
| Context Retrieval | Deterministic + Embedding | ✓ (embedding) | Vector search + schema lookup — assembles full context package |
| SQL Generation | LLM Agent | ✓ | Core generation — takes context and produces SQL |
| Validation | Deterministic | ✗ | SQL parsing, AST analysis, syntax/semantic checks |
| Security Check | Deterministic | ✗ | RBAC table/column/row matching against user permissions |
| Cost Check | Deterministic | ✗ | EXPLAIN plan analysis, threshold comparison |
| Self-Correction | LLM Agent | ✓ | Receives error + original context, produces corrected SQL |
| Result Processing | Deterministic | ✗ | Formatting, pagination, NULL handling |
| Visualization | Hybrid (rules + LLM fallback) | Optional | Rule-based chart selection with LLM fallback for ambiguous cases |
| Explanation | LLM Agent | ✓ | Summarizes results in natural language |

### Workflow Orchestration Design

The Query Orchestrator implements a **finite state machine** pattern:

```python
class QueryState(Enum):
    RECEIVED = "received"
    AUTHENTICATING = "authenticating"
    INTENT_DETECTION = "intent_detection"
    CONTEXT_RETRIEVAL = "context_retrieval"
    SQL_GENERATION = "sql_generation"
    VALIDATION = "validation"
    SECURITY_CHECK = "security_check"
    COST_CHECK = "cost_check"
    EXECUTION = "execution"
    SELF_CORRECTION = "self_correction"
    RESULT_PROCESSING = "result_processing"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
```

The orchestrator is framework-agnostic. It exposes a `process_query()` interface. Internally it can be wired to `<AGENT_FRAMEWORK>` (LangGraph, CrewAI, custom DAG, etc.) without changing the external contract.

---

## 1.7 RAG Workflow (Detailed)

```mermaid
flowchart TD
    subgraph "Indexing Pipeline (Offline)"
        S1[Schema Catalog] --> E1[Chunk & Embed]
        S2[Business Glossary] --> E2[Chunk & Embed]
        S3[Metric Definitions] --> E3[Chunk & Embed]
        S4[Example Queries] --> E4[Chunk & Embed]
        S5[Documentation] --> E5[Chunk & Embed]

        E1 --> VDB[(< VECTOR_DATABASE >)]
        E2 --> VDB
        E3 --> VDB
        E4 --> VDB
        E5 --> VDB
    end

    subgraph "Retrieval Pipeline (Online)"
        UQ[User Question] --> QE[Query Embedding]
        QE --> SIM[Similarity Search]
        SIM --> VDB
        VDB --> RC[Retrieved Chunks]
        RC --> RANK[Re-Ranking / Filtering]
        RANK --> DEDUP[Deduplication]
        DEDUP --> CTX[Final Context Package]
    end

    subgraph "Context Package Structure"
        CTX --> T1[Relevant Tables & Columns]
        CTX --> T2[Relationships / JOINs]
        CTX --> T3[Business Definitions]
        CTX --> T4[Similar Example Queries]
        CTX --> T5[Metric Formulas]
    end

    subgraph "Prompt Assembly"
        T1 --> PA[Prompt Builder]
        T2 --> PA
        T3 --> PA
        T4 --> PA
        T5 --> PA
        UQ --> PA
        PA --> LLM[< LLM_PROVIDER >]
    end
```

### RAG Indexing Strategy

| Source | Chunk Strategy | Metadata |
|--------|---------------|----------|
| Table schemas | One chunk per table (name + columns + descriptions) | `{source: "schema", table: "...", database: "..."}` |
| Column details | One chunk per column (with parent table context) | `{source: "column", table: "...", column: "..."}` |
| Business glossary | One chunk per term | `{source: "glossary", term: "..."}` |
| Metrics | One chunk per metric (formula + description) | `{source: "metric", metric_name: "..."}` |
| Example queries | One chunk per example (question + SQL + explanation) | `{source: "example", category: "..."}` |
| Relationships | One chunk per FK/relationship | `{source: "relationship", tables: [...]}` |

### Retrieval Configuration

```python
class RAGConfig:
    top_k: int = 10                  # Initial retrieval count
    rerank_top_k: int = 5            # After re-ranking
    similarity_threshold: float = 0.7 # Minimum relevance score
    include_examples: bool = True
    include_glossary: bool = True
    max_context_tokens: int = 4000   # Token budget for context
```

### Context Assembly Rules

1. **Always include**: Tables and columns detected as relevant
2. **Always include**: Foreign key relationships between relevant tables
3. **Include if available**: Business definitions for ambiguous terms
4. **Include if available**: Similar example queries (max 3)
5. **Include if available**: Metric formulas referenced in the question
6. **Never include**: Entire database schema
7. **Budget-aware**: Total context must fit within `max_context_tokens`

---

## 1.8 Cross-Cutting Concerns

### Observability Flow

```mermaid
flowchart LR
    subgraph "Every Request"
        REQ[Request] --> RID[Assign Request ID]
        RID --> SPAN[Create Trace Span]
        SPAN --> LOG[Structured Log: start]
    end

    subgraph "Every Agent Call"
        AC[Agent Invocation] --> AT[Timer Start]
        AT --> CALL[Execute]
        CALL --> MET[Emit Metrics: latency, tokens, cost]
        MET --> ALOG[Structured Log: result]
    end

    subgraph "Aggregation"
        MET --> DASH[Dashboards]
        ALOG --> SEARCH[Log Search]
        SPAN --> TRACES[Trace Visualization]
    end
```

### Error Propagation

```text
Agent Error
    ↓
Captured by Orchestrator
    ↓
Logged with full context (request_id, state, input, error)
    ↓
Decision:
  - Retryable? → Route to Self-Correction (up to MAX_RETRIES)
  - Non-retryable? → Transition to FAILED state
  - Security violation? → Transition to REJECTED state
    ↓
User receives structured error response with:
  - Error category
  - User-friendly message
  - Suggestion (if applicable)
  - query_id for support reference
```

---

## 1.9 Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration pattern | State Machine | Explicit states, easy to debug, resume, and observe |
| RAG strategy | Selective retrieval | Avoids sending entire schema; reduces token cost and hallucination |
| SQL validation | Multi-layer (syntax → semantic → security → cost) | Defense in depth; each layer catches different issues |
| LLM usage | Separate prompts per task | Smaller, focused prompts = higher accuracy + easier testing |
| Self-correction | Bounded retry with error context | Prevents infinite loops; error feedback improves correction |
| Visualization | Rule-based with LLM fallback | Deterministic for common cases; LLM for ambiguous edge cases |
| Architecture style | Clean Architecture (ports & adapters) | Infrastructure-independent; every external service is replaceable |
| Async | Async I/O for all external calls | LLM, DB, vector store are all I/O-bound; async maximizes throughput |

---

## 1.10 Interface Contracts (Key Abstractions)

```python
# All external dependencies are behind interfaces

class LLMProvider(Protocol):
    async def generate(self, prompt: str, **kwargs) -> LLMResponse: ...
    async def generate_structured(self, prompt: str, schema: type) -> Any: ...

class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

class VectorStore(Protocol):
    async def search(self, embedding: list[float], top_k: int) -> list[SearchResult]: ...
    async def upsert(self, documents: list[Document]) -> None: ...

class DatabaseExecutor(Protocol):
    async def execute(self, sql: str, params: dict | None = None) -> QueryResult: ...
    async def explain(self, sql: str) -> QueryPlan: ...

class AuthProvider(Protocol):
    async def validate_token(self, token: str) -> UserContext: ...
    async def get_permissions(self, user_id: str) -> Permissions: ...

class ObservabilityProvider(Protocol):
    def log(self, level: str, message: str, **context) -> None: ...
    def emit_metric(self, name: str, value: float, tags: dict) -> None: ...
    def start_span(self, name: str) -> Span: ...
```

These abstractions ensure the entire system can switch providers (e.g., from one `<LLM_PROVIDER>` to another) by implementing a new adapter — zero changes to business logic.
