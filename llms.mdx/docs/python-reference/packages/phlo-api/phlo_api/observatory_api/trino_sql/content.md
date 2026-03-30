# trino_sql (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/trino_sql)



SQL helper utilities for Trino API query construction and validation.

Provides SQL parsing, validation, and identifier quoting utilities
to ensure safe query construction for the Trino query endpoint.

Key Functions:
quote\_identifier: Safely quote SQL identifiers.
qualify\_table\_name: Build fully qualified table names.
is\_probably\_qualified\_table: Check if table name is qualified.
sql\_literal: Convert Python values to SQL literals.
validate\_read\_only\_query: Validate queries for read-only mode.

Example:
Building a safe query:

.. code-block:: python

from phlo\_api.observatory\_api.trino\_sql import (
quote\_identifier, qualify\_table\_name, sql\_literal
)

table = qualify\_table\_name("warehouse", "main", "events")
query = f"SELECT \* FROM \{table} WHERE id = \{sql\_literal(123)}"

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;quote_identifier&#x22;" type="&#x22;(identifier) -> str&#x22;">
      Quote an SQL identifier safely for Trino.

      <PySourceCode>
        ```python
        def quote_identifier(identifier: str) -> str:
            """Quote an SQL identifier safely for Trino.

            Args:
                identifier: The SQL identifier to quote.

            Returns:
                Quoted identifier string with double quotes.

            Raises:
                ValueError: If identifier is empty or contains NUL bytes.

            """
            if not identifier:
                raise ValueError("Identifier cannot be empty")
            if "\x00" in identifier:
                raise ValueError("Identifier cannot contain NUL bytes")
            escaped = identifier.replace('"', '""')
            return f'"{escaped}"'
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;identifier&#x22;" type="&#x22;str&#x22;" value="undefined">
          The SQL identifier to quote.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Quoted identifier string with double quotes.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;qualify_table_name&#x22;" type="&#x22;(catalog, schema, table) -> str&#x22;">
      Build a fully qualified table name with proper quoting.

      <PySourceCode>
        ```python
        def qualify_table_name(catalog: str, schema: str, table: str) -> str:
            """Build a fully qualified table name with proper quoting.

            Args:
                catalog: Catalog name.
                schema: Schema name.
                table: Table name.

            Returns:
                Fully qualified and quoted table name string.

            Raises:
                ValueError: If any identifier is invalid.

            """
            return f"{quote_identifier(catalog)}.{quote_identifier(schema)}.{quote_identifier(table)}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="undefined">
          Catalog name.
        </PyParameter>

        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name.
        </PyParameter>

        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Fully qualified and quoted table name string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;is_probably_qualified_table&#x22;" type="&#x22;(table) -> bool&#x22;">
      Check if a table name appears to be fully qualified.

      <PySourceCode>
        ```python
        def is_probably_qualified_table(table: str) -> bool:
            """Check if a table name appears to be fully qualified.

            Args:
                table: Table name string to check.

            Returns:
                True if table name contains at least 2 dots or starts with a quote.

            Raises:
                None: No exceptions raised directly.

            """
            return table.count(".") >= 2 or table.startswith('"')
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name string to check.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if table name contains at least 2 dots or starts with a quote.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;sql_literal&#x22;" type="&#x22;(value) -> str&#x22;">
      Convert a Python value to a safe SQL literal.

      <PySourceCode>
        ```python
        def sql_literal(value: object) -> str:
            """Convert a Python value to a safe SQL literal.

            Args:
                value: Python value to convert (bool, int, float, str, or None).

            Returns:
                SQL literal string representation.

            Raises:
                ValueError: If value is None, non-finite float, or unsupported type.

            """
            if value is None:
                raise ValueError("Use IS NULL for null filters")
            if isinstance(value, bool):
                return "TRUE" if value else "FALSE"
            if isinstance(value, int):
                return str(value)
            if isinstance(value, float):
                if not isfinite(value):
                    raise ValueError("Non-finite float values are not supported")
                return str(value)
            if isinstance(value, str):
                escaped = value.replace("'", "''")
                return f"'{escaped}'"
            raise ValueError(f"Unsupported filter value type: {type(value).__name__}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;object&#x22;" value="undefined">
          Python value to convert (bool, int, float, str, or None).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        SQL literal string representation.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;strip_sql_literals_and_comments&#x22;" type="&#x22;(query) -> str&#x22;">
      Return query with string literals, identifiers, and comments removed.

      This is used to prepare a query for keyword analysis by removing
      variable content that might contain forbidden keywords.

      <PySourceCode>
        ```python
        def strip_sql_literals_and_comments(query: str) -> str:
            """Return query with string literals, identifiers, and comments removed.

            This is used to prepare a query for keyword analysis by removing
            variable content that might contain forbidden keywords.

            Args:
                query: SQL query string to process.

            Returns:
                Query string with literals and comments replaced by spaces.

            Raises:
                None: No exceptions raised directly.

            """
            out: list[str] = []
            i = 0
            in_single = False
            in_double = False
            in_line_comment = False
            in_block_comment = False
            length = len(query)

            while i < length:
                ch = query[i]
                nxt = query[i + 1] if i + 1 < length else ""

                if in_line_comment:
                    if ch in "\r\n":
                        in_line_comment = False
                        out.append(ch)
                    else:
                        out.append(" ")
                    i += 1
                    continue

                if in_block_comment:
                    if ch == "*" and nxt == "/":
                        out.extend([" ", " "])
                        i += 2
                        in_block_comment = False
                        continue
                    out.append(" ")
                    i += 1
                    continue

                if in_single:
                    if ch == "'":
                        if nxt == "'":
                            out.extend([" ", " "])
                            i += 2
                            continue
                        in_single = False
                    out.append(" ")
                    i += 1
                    continue

                if in_double:
                    if ch == '"':
                        if nxt == '"':
                            out.extend([" ", " "])
                            i += 2
                            continue
                        in_double = False
                    out.append(" ")
                    i += 1
                    continue

                if ch == "-" and nxt == "-":
                    in_line_comment = True
                    out.extend([" ", " "])
                    i += 2
                    continue

                if ch == "/" and nxt == "*":
                    in_block_comment = True
                    out.extend([" ", " "])
                    i += 2
                    continue

                if ch == "'":
                    in_single = True
                    out.append(" ")
                    i += 1
                    continue

                if ch == '"':
                    in_double = True
                    out.append(" ")
                    i += 1
                    continue

                out.append(ch)
                i += 1

            return "".join(out)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          SQL query string to process.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Query string with literals and comments replaced by spaces.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;validate_read_only_query&#x22;" type="&#x22;(query) -> str | None&#x22;">
      Validate a query is read-only and a single statement.

      Checks for forbidden keywords (INSERT, UPDATE, DELETE, etc.) and
      ensures only a single statement is present.

      <PySourceCode>
        ```python
        def validate_read_only_query(query: str) -> str | None:
            """Validate a query is read-only and a single statement.

            Checks for forbidden keywords (INSERT, UPDATE, DELETE, etc.) and
            ensures only a single statement is present.

            Args:
                query: SQL query string to validate.

            Returns:
                Error message string if validation fails, None if query is valid.

            Raises:
                None: No exceptions raised directly.

            """
            cleaned = strip_sql_literals_and_comments(query)
            trimmed = cleaned.strip()
            if not trimmed:
                return "Query cannot be empty"

            while trimmed.endswith(";"):
                trimmed = trimmed[:-1].rstrip()
            if ";" in trimmed:
                return "Multiple statements are not allowed in read-only mode"

            match = _FORBIDDEN_READ_ONLY_PATTERN.search(trimmed.upper())
            if match:
                return f"{match.group(1)} statements are not allowed in read-only mode"

            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          SQL query string to validate.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Error message string if validation fails, None if query is valid.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
