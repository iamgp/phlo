"""PostgREST API view generation from dbt models.

This module automates the generation of PostgREST-compatible API views from
dbt models. It parses dbt's manifest.json, generates CREATE VIEW statements,
manages database permissions based on dbt tags, and provides tools for
applying or diffing view changes.

Classes:
    PostgrestViewsSettings: Configuration settings for view generation.
    DbtModel: Data class representing a parsed dbt model.
    DbtManifestParser: Parser for dbt manifest.json files.
    ViewGenerator: Generator for CREATE VIEW SQL statements.
    PostgreSTViewManager: Database operations for view management.

Functions:
    generate_views: Main entry point for view generation workflow.

Example:
    >>> from phlo_postgrest.views import generate_views
    >>> generate_views(apply=True, models="mrt_*")
    Views applied successfully

"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from phlo.config.base import BaseConfig
from phlo.logging import get_logger
from pydantic import Field

logger = get_logger(__name__)


class PostgrestViewsSettings(BaseConfig):
    """Configuration settings for PostgREST view generation.

    Pydantic-based configuration class that loads settings from environment
    variables and configuration files. Controls paths, database connections,
    and schema selection for view generation.

    Attributes:
        dbt_manifest_path: Path to dbt's manifest.json output.
        dbt_api_source_schema: Source schema to expose via PostgREST.
        postgres_host: PostgreSQL server hostname.
        postgres_port: PostgreSQL server port.
        postgres_user: Database username.
        postgres_password: Database password (required; set via env var).
        postgres_db: Database name.

    Example:
        >>> settings = PostgrestViewsSettings()
        >>> settings.postgres_host
        'postgres'

    """

    dbt_manifest_path: str = Field(
        default="workflows/transforms/dbt/target/manifest.json",
        description="Path to dbt manifest.json",
    )
    dbt_api_source_schema: str | None = Field(
        default=None,
        description="dbt schema to expose through generated PostgREST views",
    )
    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="phlo", description="PostgreSQL username")
    postgres_password: str | None = Field(
        default=None,
        description="PostgreSQL password (required; set PHLO_POSTGRES_PASSWORD or POSTGRES_PASSWORD env var)",
    )
    postgres_db: str = Field(default="phlo", description="PostgreSQL database name")


@dataclass
class DbtModel:
    """Represents a dbt model extracted from manifest.json.

    Data class containing metadata about a dbt model including its
    name, schema, columns, tags, and description for view generation.

    Attributes:
        name: Model identifier (table/view name).
        schema: Database schema where model resides.
        description: Documentation string from dbt model YAML.
        columns: Dictionary of column metadata from manifest.
        tags: List of dbt tags applied to the model.
        unique_id: Full unique identifier from manifest (e.g., 'model.project.name').

    Example:
        >>> model = DbtModel(
        ...     name="mrt_orders",
        ...     schema="marts",
        ...     description="Order metrics",
        ...     columns={"order_id": {...}},
        ...     tags=["analyst"],
        ...     unique_id="model.phlo.mrt_orders"
        ... )

    """

    name: str
    schema: str
    description: str
    columns: dict
    tags: list[str]
    unique_id: str


class DbtManifestParser:
    """Parser for dbt manifest.json files.

    Extracts model metadata from dbt's compilation output, supporting
    schema filtering and dependency graph construction for view
    generation and ordering.

    Attributes:
        manifest_path: Path to manifest.json file.
        source_schema: Schema to filter models (e.g., 'marts').

    Example:
        >>> parser = DbtManifestParser(
        ...     manifest_path="target/manifest.json",
        ...     source_schema="marts"
        ... )
        >>> models = parser.parse()

    """

    def __init__(self, manifest_path: Optional[str] = None, source_schema: Optional[str] = None):
        """Initialize manifest parser with configuration.

        Args:
            manifest_path: Path to manifest.json. Uses settings if None.
            source_schema: Schema to filter models. Uses settings if None.

        Raises:
            FileNotFoundError: If manifest.json doesn't exist at specified path.

        Example:
            >>> parser = DbtManifestParser(
            ...     "workflows/transforms/dbt/target/manifest.json",
            ...     "marts"
            ... )

        """
        settings = PostgrestViewsSettings()
        if manifest_path is None:
            manifest_path = settings.dbt_manifest_path
        if source_schema is None:
            source_schema = settings.dbt_api_source_schema

        self.manifest_path = Path(manifest_path)
        self.source_schema = source_schema

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"dbt manifest not found at {manifest_path}")

    def parse(self) -> dict[str, DbtModel]:
        """Parse manifest and extract filtered models.

        Reads manifest.json and extracts all model nodes matching the
        configured source_schema, constructing DbtModel instances.

        Returns:
            dict[str, DbtModel]: Mapping of model names to DbtModel objects.

        Raises:
            FileNotFoundError: If manifest file is missing.
            json.JSONDecodeError: If manifest contains invalid JSON.

        Example:
            >>> parser = DbtManifestParser(source_schema="marts")
            >>> models = parser.parse()
            >>> list(models.keys())
            ['mrt_orders', 'mrt_customers']

        """
        with open(self.manifest_path) as f:
            manifest = json.load(f)

        source_schema = self.source_schema or self._infer_source_schema(manifest)

        models = {}
        for unique_id, node in manifest.get("nodes", {}).items():
            if not unique_id.startswith("model."):
                continue

            if node.get("schema") != source_schema:
                continue

            model = DbtModel(
                name=node.get("name"),
                schema=node.get("schema"),
                description=node.get("description", ""),
                columns=node.get("columns", {}),
                tags=node.get("tags", []),
                unique_id=unique_id,
            )

            models[model.name] = model

        return models

    def _infer_source_schema(self, manifest: dict) -> str:
        """Infer source schema when not explicitly configured.

        Analyzes all models in manifest and determines schema when only
        one unique schema is present. Raises error if multiple schemas
        exist and none is specified.

        Args:
            manifest: Parsed manifest.json dictionary.

        Returns:
            str: The inferred schema name.

        Raises:
            ValueError: If multiple schemas exist without explicit configuration.

        Example:
            >>> schema = parser._infer_source_schema(manifest)
            >>> print(schema)
            'marts'

        """
        schemas = {
            node.get("schema")
            for unique_id, node in manifest.get("nodes", {}).items()
            if unique_id.startswith("model.") and isinstance(node.get("schema"), str)
        }
        if len(schemas) == 1:
            return next(iter(schemas))
        raise ValueError(
            "dbt_api_source_schema is not configured and manifest contains multiple model "
            f"schemas: {sorted(schemas)}"
        )

    def build_dependency_graph(self) -> dict[str, list[str]]:
        """Build model dependency graph from manifest.

        Constructs a directed graph of model dependencies for topological
        sorting during view generation, ensuring views are created in
        correct order.

        Returns:
            dict[str, list[str]]: Mapping of model names to their dependencies.

        Example:
            >>> graph = parser.build_dependency_graph()
            >>> graph.get("mrt_orders")
            ['stg_orders', 'stg_customers']

        """
        with open(self.manifest_path) as f:
            manifest = json.load(f)

        graph = {}
        for unique_id, node in manifest.get("nodes", {}).items():
            if not unique_id.startswith("model."):
                continue

            model_name = node.get("name")
            depends_on = []

            for dep_id in node.get("depends_on", {}).get("nodes", []):
                if dep_id.startswith("model."):
                    dep_name = dep_id.split(".")[-1]
                    depends_on.append(dep_name)

            graph[model_name] = depends_on

        return graph


class ViewGenerator:
    """Generator for PostgREST-compatible database views.

    Generates CREATE VIEW statements from dbt models, including proper
    column ordering, SQL comments, permissions based on tags, and
    Row-Level Security policies.

    Attributes:
        parser: DbtManifestParser instance for reading model metadata.
        api_schema: Target schema for generated views (default: 'api').

    Example:
        >>> generator = ViewGenerator(api_schema="api")
        >>> sql = generator.generate_all_views(models="mrt_*")

    """

    def __init__(
        self,
        manifest_path: Optional[str] = None,
        api_schema: str = "api",
        source_schema: Optional[str] = None,
    ):
        """Initialize view generator with configuration.

        Args:
            manifest_path: Path to dbt manifest.json file.
            api_schema: Target schema for API views (default: 'api').
            source_schema: Source dbt schema to expose.

        Example:
            >>> generator = ViewGenerator(
            ...     manifest_path="target/manifest.json",
            ...     api_schema="api",
            ...     source_schema="marts"
            ... )

        """
        self.parser = DbtManifestParser(manifest_path, source_schema=source_schema)
        self.api_schema = api_schema

    def generate_view_sql(self, model: DbtModel) -> str:
        """Generate CREATE VIEW SQL for a single model.

        Creates a complete CREATE OR REPLACE VIEW statement with column
        selection, table references, and SQL COMMENT documentation.

        Args:
            model: DbtModel instance to generate view for.

        Returns:
            str: Complete SQL statement for view creation.

        Example:
            >>> sql = generator.generate_view_sql(model)
            >>> print(sql)
            CREATE OR REPLACE VIEW api.mrt_orders AS
            SELECT order_id, customer_id, total
            FROM marts.mrt_orders;

        """
        # Extract column names in order
        columns = list(model.columns.keys())
        column_list = ",\n    ".join(columns) if columns else "*"

        sql = f"""-- Auto-generated by phlo api generate-views
-- Model: {model.name}
-- Description: {model.description}

CREATE OR REPLACE VIEW {self.api_schema}.{model.name} AS
SELECT
    {column_list}
FROM {model.schema}.{model.name};

COMMENT ON VIEW {self.api_schema}.{model.name} IS '{self._escape_string(model.description)}';
"""
        return sql

    def generate_permissions_sql(self, model: DbtModel) -> str:
        """Generate GRANT SQL for a model.

        Maps dbt tags to database roles and generates appropriate
        GRANT statements for generated API views.

        Tag-to-Role Mapping:
            - 'public' -> anon role
            - 'analyst' -> analyst and admin roles
            - 'admin' -> admin role only

        Args:
            model: DbtModel instance with tags to process.

        Returns:
            str: SQL statements for grants.

        Example:
            >>> sql = generator.generate_permissions_sql(model)
            >>> print(sql)
            GRANT SELECT ON api.mrt_orders TO analyst;
            GRANT SELECT ON api.mrt_orders TO admin;

        """
        sql_parts = ["\n-- Permissions"]

        # Map tags to roles
        role_mapping = {
            "public": ["anon"],
            "analyst": ["analyst", "admin"],
            "admin": ["admin"],
        }

        granted_roles = set()
        for tag in model.tags:
            for role in role_mapping.get(tag, []):
                if role not in granted_roles:
                    sql_parts.append(f"GRANT SELECT ON {self.api_schema}.{model.name} TO {role};")
                    granted_roles.add(role)

        if granted_roles:
            sql_parts.append("\n-- Note: PostgreSQL views do not support RLS policies directly.")
            sql_parts.append(
                "-- Apply row-level controls to underlying tables or security-definer functions."
            )

        return "\n".join(sql_parts)

    def generate_all_views(self, model_filter: Optional[str] = None) -> str:
        """Generate SQL for all views matching filter.

        Processes all models from manifest, optionally filtered by glob
        pattern, and generates complete SQL including views and permissions
        in dependency order.

        Args:
            model_filter: Glob pattern to filter models (e.g., 'mrt_*', 'stg_*').

        Returns:
            str: Complete SQL script for all views and permissions.
            Returns empty string if no models match.

        Example:
            >>> sql = generator.generate_all_views(model_filter="mrt_*")
            >>> len(sql) > 0
            True

        """
        models = self.parser.parse()

        # Filter models
        if model_filter:
            from fnmatch import fnmatch

            models = {name: model for name, model in models.items() if fnmatch(name, model_filter)}

        if not models:
            return ""

        # Sort by dependencies (simple topological sort)
        dependency_graph = self.parser.build_dependency_graph()
        sorted_models = self._topological_sort(models, dependency_graph)

        sql_parts = [
            "-- PostgREST API Views",
            f"-- Generated from dbt manifest at {self.parser.manifest_path}",
            f"-- Schema: {self.api_schema}",
            "--\n",
        ]

        for model_name in sorted_models:
            model = models[model_name]
            sql_parts.append(self.generate_view_sql(model))
            sql_parts.append(self.generate_permissions_sql(model))
            sql_parts.append("\n")

        return "\n".join(sql_parts)

    def _topological_sort(
        self, models: dict[str, DbtModel], graph: dict[str, list[str]]
    ) -> list[str]:
        """Sort models by dependencies using topological sort.

        Ensures views are created in correct order so that dependent
        views reference already-created views.

        Args:
            models: Dictionary of models to sort.
            graph: Dependency graph from build_dependency_graph().

        Returns:
            list[str]: Model names in dependency-respecting order.

        Example:
            >>> sorted_names = generator._topological_sort(models, graph)
            >>> sorted_names[0]  # Least dependent model first
            'stg_orders'

        """
        visited = set()
        order = []

        def visit(name: str) -> None:
            """Visit model and its dependencies recursively.

            Depth-first traversal helper that visits dependencies before
            the model itself to establish correct creation order.

            Args:
                name: Model name to visit.

            """
            if name in visited:
                return
            visited.add(name)

            for dep in graph.get(name, []):
                if dep in models:
                    visit(dep)

            if name in models:
                order.append(name)

        for name in models:
            visit(name)

        return order

    @staticmethod
    def _escape_string(s: str) -> str:
        """Escape single quotes in strings for SQL safety.

        Doubles single quotes to prevent SQL injection in COMMENT statements.

        Args:
            s: Input string potentially containing single quotes.

        Returns:
            str: Escaped string safe for SQL COMMENT.

        Example:
            >>> ViewGenerator._escape_string("It's a test")
            "It''s a test"

        """
        return s.replace("'", "''")


class PostgreSTViewManager:
    """Manager for PostgreSQL view operations and database connectivity.

        Handles database connections, SQL execution, view discovery, and
    diff generation for PostgREST view management.

    Attributes:
            host: PostgreSQL server hostname.
            port: PostgreSQL server port.
            database: Database name.
            user: Database username.
            password: Database password.

    Example:
            >>> manager = PostgreSTViewManager(host="postgres", port=5432)
            >>> manager.execute_sql("CREATE VIEW test AS SELECT 1")

    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize PostgreSQL connection manager with settings.

        Loads configuration from PostgrestViewsSettings for any
        parameters not explicitly provided.

        Args:
            host: Database server hostname.
            port: Database server port.
            database: Database name.
            user: Database username.
            password: Database password.

        Example:
            >>> manager = PostgreSTViewManager(
            ...     host="db.example.com",
            ...     port=5432,
            ...     database="phlo"
            ... )

        """
        settings = PostgrestViewsSettings()
        self.host = host or settings.postgres_host
        self.port = int(port or settings.postgres_port)
        self.database = database or settings.postgres_db
        self.user = user or settings.postgres_user
        self.password = password or settings.postgres_password
        if not self.password:
            raise ValueError(
                "PostgreSQL password must be set via the PHLO_POSTGRES_PASSWORD "
                "or POSTGRES_PASSWORD environment variable, or passed as the 'password' argument."
            )

    def get_connection(self):
        """Establish and return a PostgreSQL database connection.

        Creates a new psycopg2 connection with autocommit enabled
        for executing DDL statements.

        Returns:
            psycopg2 connection object with autocommit enabled.

        Raises:
            psycopg2.Error: If connection fails due to network or auth issues.

        Example:
            >>> conn = manager.get_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT 1")

        """
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn

    def execute_sql(self, sql: str, verbose: bool = True) -> None:
        """Execute SQL statements against the database.

        Runs the provided SQL with optional progress logging.
        Automatically manages connection lifecycle.

        Args:
            sql: SQL statement(s) to execute.
            verbose: Log execution progress if True.

        Raises:
            Exception: If SQL execution fails (re-raised after logging).

        Example:
            >>> manager.execute_sql("CREATE VIEW test AS SELECT 1")
            ✓ SQL executed successfully

        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if verbose:
                logger.info("Executing %s characters of SQL...", len(sql))
            cursor.execute(sql)
            if verbose:
                logger.info("✓ SQL executed successfully")
        except Exception as e:
            logger.error("✗ SQL execution failed: %s", e)
            raise
        finally:
            cursor.close()
            conn.close()

    def get_existing_views(self, schema: str = "api") -> set[str]:
        """Query database for existing views in a schema.

        Retrieves all view names from information_schema.tables for
        the specified schema.

        Args:
            schema: Schema name to query (default: 'api').

        Returns:
            set[str]: Set of existing view names in the schema.

        Example:
            >>> views = manager.get_existing_views("api")
            >>> print(views)
            {'mrt_orders', 'mrt_customers'}

        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'VIEW'
            """,
                (schema,),
            )
            return {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()

    def generate_diff(self, new_sql: str, schema: str = "api") -> str:
        """Generate human-readable diff between existing and new views.

        Compares currently deployed views against newly generated SQL
        to identify created, updated, and removed views.

        Args:
            new_sql: Generated SQL containing CREATE VIEW statements.
            schema: Schema name to compare (default: 'api').

        Returns:
            str: Formatted diff summary showing view changes.

        Example:
            >>> diff = manager.generate_diff(sql, "api")
            >>> print(diff)
            Views to be created/updated:
              mrt_orders (updated)
              mrt_customers (new)

        """
        existing_views = self.get_existing_views(schema)

        # Parse generated SQL to find new views
        import re

        new_views = set(re.findall(rf"CREATE OR REPLACE VIEW {schema}\.(\w+)", new_sql))

        lines = ["Views to be created/updated:"]
        for view in sorted(new_views):
            status = "(updated)" if view in existing_views else "(new)"
            lines.append(f"  {view} {status}")

        removed = existing_views - new_views
        if removed:
            lines.append("Views to be removed:")
            for view in sorted(removed):
                lines.append(f"  {view} (orphaned)")

        return "\n".join(lines)


def generate_views(
    output: Optional[str] = None,
    apply: bool = False,
    diff: bool = False,
    models: Optional[str] = None,
    manifest_path: Optional[str] = None,
    api_schema: str = "api",
    source_schema: Optional[str] = None,
    verbose: bool = True,
) -> str:
    """Generate PostgREST API views from dbt models.

        Main entry point for view generation workflow. Orchestrates parsing
    the dbt manifest, generating SQL, and optionally applying to database or
    showing diffs.

        Supports three output modes:
            - Default: Return SQL string
            - output: Write SQL to file
            - apply: Execute SQL directly against database
            - diff: Show comparison with existing views

    Args:
            output: File path to write SQL (default: return string).
            apply: Execute SQL against database if True.
            diff: Show diff summary instead of SQL.
            models: Glob pattern to filter models (e.g., 'mrt_*').
            manifest_path: Path to dbt manifest.json.
            api_schema: Target schema for views (default: 'api').
            source_schema: Source dbt schema to expose.
            verbose: Enable progress logging.

    Returns:
            str: Generated SQL, diff summary, or status message depending on mode.
            Returns empty string if no models match filter.

    Raises:
            Exception: If database operations fail when apply=True.

    Example:
            >>> # Generate SQL to stdout
            >>> sql = generate_views()

            >>> # Apply directly to database
            >>> result = generate_views(apply=True, models="mrt_*")
            >>> print(result)
            Views applied successfully

            >>> # Show what's changing
            >>> diff = generate_views(diff=True)
            >>> print(diff)

    """
    if verbose:
        logger.info("=" * 60)
        logger.info("PostgREST API View Generation")
        logger.info("=" * 60)

    # Generate SQL
    generator = ViewGenerator(manifest_path, api_schema, source_schema=source_schema)
    sql = generator.generate_all_views(models)

    if not sql:
        if verbose:
            logger.info("No models found matching filter")
        return ""

    if verbose:
        logger.info("Generated SQL for %s characters", len(sql))

    # Handle diff
    if diff:
        manager = PostgreSTViewManager()
        diff_output = manager.generate_diff(sql, api_schema)
        if verbose:
            logger.info("\n%s", diff_output)
        return diff_output

    # Handle apply
    if apply:
        if verbose:
            logger.info("Applying to database...")
        view_names = sorted(
            set(re.findall(rf"CREATE OR REPLACE VIEW {re.escape(api_schema)}\.(\w+)", sql))
        )
        logger.info(
            "postgrest_view_apply_started",
            schema=api_schema,
            view_count=len(view_names),
            view_names=view_names,
        )
        manager = PostgreSTViewManager()
        try:
            manager.execute_sql(sql, verbose=verbose)
        except Exception:
            logger.exception(
                "postgrest_view_apply_failed",
                schema=api_schema,
                view_count=len(view_names),
                view_names=view_names,
            )
            raise
        logger.info(
            "postgrest_view_apply_succeeded",
            schema=api_schema,
            view_count=len(view_names),
            view_names=view_names,
        )
        return "Views applied successfully"

    # Handle output file
    if output:
        output_path = Path(output)
        output_path.write_text(sql)
        if verbose:
            logger.info("✓ SQL written to %s", output)
        return f"SQL written to {output}"

    # Default: print to stdout
    return sql
