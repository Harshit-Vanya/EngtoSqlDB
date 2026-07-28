"""Schema Catalog — loads and serves schema metadata from YAML definitions.

This module is the single source of truth for database schema knowledge.
It provides:
- Table and column definitions with descriptions
- Business glossary terms
- Metric formulas
- Example NL→SQL pairs
- Relationship information

The data is loaded from YAML files at startup and made available
to the RAG system for indexing and to the SQL generator for context.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFINITIONS_DIR = Path(__file__).parent / "definitions"


@dataclass
class ColumnDef:
    """A column definition from the schema catalog."""

    name: str
    data_type: str
    description: str = ""
    primary_key: bool = False
    foreign_key: str | None = None
    nullable: bool = False
    sensitive: bool = False
    pii: bool = False


@dataclass
class TableDef:
    """A table definition from the schema catalog."""

    name: str
    description: str = ""
    columns: list[ColumnDef] = field(default_factory=list)


@dataclass
class RelationshipDef:
    """A foreign key relationship between two tables."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    rel_type: str = "many_to_one"
    description: str = ""


@dataclass
class GlossaryTerm:
    """A business glossary term."""

    term: str
    definition: str
    related_tables: list[str] = field(default_factory=list)
    related_columns: list[str] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    category: str = ""


@dataclass
class MetricDef:
    """A metric definition with SQL formula."""

    name: str
    description: str
    formula: str
    required_tables: list[str] = field(default_factory=list)
    required_joins: list[str] = field(default_factory=list)
    filters: str = ""
    group_by: str = ""
    aggregation: str = "sum"
    category: str = ""


@dataclass
class ExampleQueryDef:
    """An example NL-to-SQL pair."""

    question: str
    sql: str
    explanation: str = ""
    tables: list[str] = field(default_factory=list)
    category: str = ""
    difficulty: str = "medium"


class SchemaCatalog:
    """Loads and provides access to schema metadata from YAML definitions.

    Usage:
        catalog = SchemaCatalog()
        catalog.load()
        tables = catalog.get_tables()
        glossary = catalog.get_glossary()
    """

    def __init__(self, definitions_dir: Path | None = None):
        self._dir = definitions_dir or DEFINITIONS_DIR
        self._tables: list[TableDef] = []
        self._relationships: list[RelationshipDef] = []
        self._glossary: list[GlossaryTerm] = []
        self._metrics: list[MetricDef] = []
        self._examples: list[ExampleQueryDef] = []
        self._loaded = False

    def load(self) -> None:
        """Load all YAML definitions into memory."""
        self._load_tables()
        self._load_glossary()
        self._load_metrics()
        self._load_examples()
        self._loaded = True

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML file from the definitions directory."""
        filepath = self._dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, "r") as f:
            return yaml.safe_load(f) or {}

    def _load_tables(self) -> None:
        """Load table definitions and relationships from tables.yaml."""
        data = self._load_yaml("tables.yaml")

        for table_data in data.get("tables", []):
            columns = []
            for col in table_data.get("columns", []):
                columns.append(ColumnDef(
                    name=col["name"],
                    data_type=col.get("type", "varchar"),
                    description=col.get("description", ""),
                    primary_key=col.get("primary_key", False),
                    foreign_key=col.get("foreign_key"),
                    nullable=col.get("nullable", False),
                    sensitive=col.get("sensitive", False),
                    pii=col.get("pii", False),
                ))
            self._tables.append(TableDef(
                name=table_data["name"],
                description=table_data.get("description", ""),
                columns=columns,
            ))

        for rel_data in data.get("relationships", []):
            self._relationships.append(RelationshipDef(
                from_table=rel_data["from_table"],
                from_column=rel_data["from_column"],
                to_table=rel_data["to_table"],
                to_column=rel_data["to_column"],
                rel_type=rel_data.get("type", "many_to_one"),
                description=rel_data.get("description", ""),
            ))

    def _load_glossary(self) -> None:
        """Load business glossary from business_glossary.yaml."""
        data = self._load_yaml("business_glossary.yaml")
        for term_data in data.get("terms", []):
            self._glossary.append(GlossaryTerm(
                term=term_data["term"],
                definition=term_data["definition"],
                related_tables=term_data.get("related_tables", []),
                related_columns=term_data.get("related_columns", []),
                synonyms=term_data.get("synonyms", []),
                category=term_data.get("category", ""),
            ))

    def _load_metrics(self) -> None:
        """Load metric definitions from metrics.yaml."""
        data = self._load_yaml("metrics.yaml")
        for metric_data in data.get("metrics", []):
            self._metrics.append(MetricDef(
                name=metric_data["name"],
                description=metric_data["description"],
                formula=metric_data["formula"],
                required_tables=metric_data.get("required_tables", []),
                required_joins=metric_data.get("required_joins", []),
                filters=metric_data.get("filters", ""),
                group_by=metric_data.get("group_by", ""),
                aggregation=metric_data.get("aggregation", "sum"),
                category=metric_data.get("category", ""),
            ))

    def _load_examples(self) -> None:
        """Load example queries from examples.yaml."""
        data = self._load_yaml("examples.yaml")
        for ex_data in data.get("examples", []):
            self._examples.append(ExampleQueryDef(
                question=ex_data["question"],
                sql=ex_data["sql"].strip(),
                explanation=ex_data.get("explanation", ""),
                tables=ex_data.get("tables", []),
                category=ex_data.get("category", ""),
                difficulty=ex_data.get("difficulty", "medium"),
            ))

    # --- Public API ---

    def get_tables(self) -> list[TableDef]:
        """Get all table definitions."""
        self._ensure_loaded()
        return self._tables

    def get_table(self, name: str) -> TableDef | None:
        """Get a specific table definition by name."""
        self._ensure_loaded()
        for table in self._tables:
            if table.name == name:
                return table
        return None

    def get_relationships(self) -> list[RelationshipDef]:
        """Get all relationship definitions."""
        self._ensure_loaded()
        return self._relationships

    def get_relationships_for_tables(self, table_names: list[str]) -> list[RelationshipDef]:
        """Get relationships involving any of the given tables."""
        self._ensure_loaded()
        return [
            r for r in self._relationships
            if r.from_table in table_names or r.to_table in table_names
        ]

    def get_glossary(self) -> list[GlossaryTerm]:
        """Get all glossary terms."""
        self._ensure_loaded()
        return self._glossary

    def get_metrics(self) -> list[MetricDef]:
        """Get all metric definitions."""
        self._ensure_loaded()
        return self._metrics

    def get_examples(self) -> list[ExampleQueryDef]:
        """Get all example queries."""
        self._ensure_loaded()
        return self._examples

    def get_all_table_names(self) -> list[str]:
        """Get list of all table names."""
        self._ensure_loaded()
        return [t.name for t in self._tables]

    def get_all_column_names(self) -> dict[str, list[str]]:
        """Get mapping of table_name → list of column names."""
        self._ensure_loaded()
        return {
            table.name: [col.name for col in table.columns]
            for table in self._tables
        }

    def get_schema_text_for_table(self, table_name: str) -> str:
        """Get a formatted text description of a table for embedding/prompts.

        Returns a string like:
            Table: orders
            Description: Customer order transactions...
            Columns:
            - order_id (integer, PK): Unique identifier
            - customer_id (integer, FK→customers): Customer who placed this order
            ...
        """
        table = self.get_table(table_name)
        if table is None:
            return ""

        lines = [f"Table: {table.name}", f"Description: {table.description}", "Columns:"]
        for col in table.columns:
            flags = []
            if col.primary_key:
                flags.append("PK")
            if col.foreign_key:
                flags.append(f"FK→{col.foreign_key}")
            if col.nullable:
                flags.append("nullable")
            flag_str = f" ({col.data_type}, {', '.join(flags)})" if flags else f" ({col.data_type})"
            lines.append(f"  - {col.name}{flag_str}: {col.description}")

        return "\n".join(lines)

    def get_full_schema_text(self) -> str:
        """Get the complete schema as formatted text (for debugging/display)."""
        self._ensure_loaded()
        parts = []
        for table in self._tables:
            parts.append(self.get_schema_text_for_table(table.name))
            parts.append("")  # blank line between tables
        return "\n".join(parts)

    def _ensure_loaded(self) -> None:
        """Ensure YAML data has been loaded."""
        if not self._loaded:
            self.load()
