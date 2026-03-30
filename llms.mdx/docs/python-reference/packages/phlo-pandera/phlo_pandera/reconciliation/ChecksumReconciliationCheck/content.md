# ChecksumReconciliationCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/ChecksumReconciliationCheck)



Check that row-level hashes match between source and target tables.

This check computes hashes of specified columns and compares them between
source and target tables. It can detect data corruption, unexpected
transformations, or synchronization issues at the row level.

Attributes [#attributes]

<PyAttribute name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified source table name.
</PyAttribute>

<PyAttribute name="&#x22;target_table&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified target table name.
</PyAttribute>

<PyAttribute name="&#x22;key_columns&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Primary key or composite key columns for row alignment.
</PyAttribute>

<PyAttribute name="&#x22;columns&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
  Columns to hash. None = hash all non-key columns from target.
</PyAttribute>

<PyAttribute name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;">
  Column used for partition filtering.
</PyAttribute>

<PyAttribute name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Allowed fraction of mismatches (0.0 = exact match).
</PyAttribute>

<PyAttribute name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;">
  Allowed absolute count of mismatches.
</PyAttribute>

<PyAttribute name="&#x22;hash_algorithm&#x22;" type="&#x22;str&#x22;" value="&#x22;'xxhash64'&#x22;">
  Hash algorithm ('xxhash64' or 'md5').
</PyAttribute>

<PyAttribute name="&#x22;float_precision&#x22;" type="&#x22;int&#x22;" value="&#x22;6&#x22;">
  Precision used when normalizing floats for hashing.
</PyAttribute>

<PyAttribute name="&#x22;sample&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;">
  Optional deterministic sampling fraction (0 \< sample \<= 1).
</PyAttribute>

<PyAttribute name="&#x22;limit&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  Optional limit on number of keys compared (applies to source).
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute checksum reconciliation check.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute checksum reconciliation check.

        Args:
            df: Target DataFrame with data to validate.
            context: Runtime context with resources and partition info.

        Returns:
            QualityCheckResult with hash comparison results.

        """
        missing_columns = [column for column in self.key_columns if column not in df.columns]
        if missing_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                failure_message=f"Missing key columns in target data: {missing_columns}",
            )

        if self.columns is None:
            hash_columns = [column for column in df.columns if column not in self.key_columns]
        else:
            hash_columns = self.columns

        missing_hash_columns = [column for column in hash_columns if column not in df.columns]
        if missing_hash_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                failure_message=f"Missing hash columns in target data: {missing_hash_columns}",
            )

        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        source_query = self._build_hash_query(
            self.source_table, hash_columns, partition_key, apply_limit=True
        )
        target_query = self._build_hash_query(
            self.target_table, hash_columns, partition_key, apply_limit=False
        )

        source_rows = self._get_hash_rows(context, source_query)
        if source_rows is None:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                metadata={"source_table": self.source_table, "query": source_query},
                failure_message=f"Failed to query source hashes from {self.source_table}",
            )

        target_rows = self._get_hash_rows(context, target_query)
        if target_rows is None:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                metadata={"target_table": self.target_table, "query": target_query},
                failure_message=f"Failed to query target hashes from {self.target_table}",
            )

        source_hashes, source_duplicates = self._rows_to_hash_map(source_rows)
        target_hashes, target_duplicates = self._rows_to_hash_map(target_rows)

        if self.limit is not None:
            target_hashes = {
                key: value for key, value in target_hashes.items() if key in source_hashes
            }

        source_keys = set(source_hashes.keys())
        target_keys = set(target_hashes.keys())

        missing_in_target = source_keys - target_keys
        missing_in_source = target_keys - source_keys

        shared_keys = source_keys.intersection(target_keys)
        hash_mismatches = {
            key for key in shared_keys if source_hashes.get(key) != target_hashes.get(key)
        }

        total_keys = len(source_keys.union(target_keys))
        duplicate_count = source_duplicates + target_duplicates
        mismatch_count = (
            len(missing_in_target) + len(missing_in_source) + len(hash_mismatches) + duplicate_count
        )
        total_comparable = total_keys + duplicate_count
        mismatch_pct = mismatch_count / total_comparable if total_comparable else 0.0

        passed = mismatch_pct <= self.tolerance or (
            self.absolute_tolerance is not None and mismatch_count <= self.absolute_tolerance
        )

        failure_msg = None
        if not passed:
            duplicate_segment = f", {duplicate_count} duplicate keys" if duplicate_count else ""
            failure_msg = (
                f"Checksum reconciliation failed: {len(hash_mismatches)} hash mismatches, "
                f"{len(missing_in_target)} missing in target, "
                f"{len(missing_in_source)} missing in source"
                f"{duplicate_segment} "
                f"(mismatch: {mismatch_pct:.2%}, tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="checksum_reconciliation_check",
            metric_value={
                "missing_in_target": len(missing_in_target),
                "missing_in_source": len(missing_in_source),
                "hash_mismatches": len(hash_mismatches),
                "duplicate_keys": duplicate_count,
                "total_keys": total_keys,
                "mismatch_pct": float(mismatch_pct),
            },
            metadata={
                "source_table": self.source_table,
                "target_table": self.target_table,
                "key_columns": self.key_columns,
                "hash_columns": hash_columns,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "hash_algorithm": self.hash_algorithm,
                "float_precision": self.float_precision,
                "sample": self.sample,
                "limit": self.limit,
                "source_duplicates": source_duplicates,
                "target_duplicates": target_duplicates,
                "source_query": source_query,
                "target_query": target_query,
                "sample_hash_mismatches": [str(key) for key in list(hash_mismatches)[:10]],
            },
            failure_message=failure_msg,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Target DataFrame with data to validate.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context with resources and partition info.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult with hash comparison results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_hash_query&#x22;" type="&#x22;(self, table, hash_columns, partition_key, apply_limit) -> str&#x22;">
  Build SQL query to compute key + hash for a table.

  <PySourceCode>
    ```python
    def _build_hash_query(
        self,
        table: str,
        hash_columns: list[str],
        partition_key: str | None,
        apply_limit: bool,
    ) -> str:
        """Build SQL query to compute key + hash for a table.

        Args:
            table: Table name to query.
            hash_columns: List of columns to include in hash computation.
            partition_key: Optional partition key for filtering.
            apply_limit: Whether to apply the limit clause.

        Returns:
            SQL query string for computing row hashes.

        """
        select_cols = ", ".join(self.key_columns)
        hash_expr = self._hash_expression(hash_columns)
        query = f"SELECT {select_cols}, {hash_expr} AS row_hash FROM {table}"

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        sampling_predicate = self._sampling_predicate()
        if sampling_predicate:
            conditions.append(sampling_predicate)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if apply_limit and self.limit is not None:
            query += f" LIMIT {self.limit}"

        return query
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name to query.
    </PyParameter>

    <PyParameter name="&#x22;hash_columns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of columns to include in hash computation.
    </PyParameter>

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Optional partition key for filtering.
    </PyParameter>

    <PyParameter name="&#x22;apply_limit&#x22;" type="&#x22;bool&#x22;" value="undefined">
      Whether to apply the limit clause.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    SQL query string for computing row hashes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_sampling_predicate&#x22;" type="&#x22;(self) -> str | None&#x22;">
  Build deterministic sampling predicate using key hash.

  <PySourceCode>
    ```python
    def _sampling_predicate(self) -> str | None:
        """Build deterministic sampling predicate using key hash."""
        if self.sample is None:
            return None
        if self.sample <= 0 or self.sample > 1:
            raise ValueError("sample must be within (0, 1]")
        key_expr = " || '|' || ".join(
            [f"coalesce(cast({col} as varchar), '__NULL__')" for col in self.key_columns]
        )
        bucket_count = 10000
        threshold = int(self.sample * bucket_count)
        return f"mod(xxhash64({key_expr}), {bucket_count}) < {threshold}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_hash_expression&#x22;" type="&#x22;(self, hash_columns) -> str&#x22;">
  Build SQL expression to compute the row hash.

  <PySourceCode>
    ```python
    def _hash_expression(self, hash_columns: list[str]) -> str:
        """Build SQL expression to compute the row hash.

        Args:
            hash_columns: List of column names to hash.

        Returns:
            SQL expression string for computing the hash.

        Raises:
            ValueError: If hash_algorithm is not supported.

        """
        normalized_columns = []
        for column in hash_columns:
            normalized_columns.append(
                "coalesce("
                f"cast(round(try_cast({column} as double), {self.float_precision}) as varchar), "
                f"cast({column} as varchar), "
                "'__NULL__'"
                ")"
            )
        concatenated = " || '|' || ".join(normalized_columns) if normalized_columns else "''"

        algorithm = self.hash_algorithm.lower()
        if algorithm == "xxhash64":
            return f"cast(xxhash64({concatenated}) as varchar)"
        if algorithm == "md5":
            return f"lower(to_hex(md5({concatenated})))"
        raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;hash_columns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of column names to hash.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    SQL expression string for computing the hash.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_hash_rows&#x22;" type="&#x22;(self, context, query) -> list[tuple] | None&#x22;">
  Execute query to fetch key + hash rows.

  <PySourceCode>
    ```python
    def _get_hash_rows(self, context: RuntimeContext | None, query: str) -> list[tuple] | None:
        """Execute query to fetch key + hash rows.

        Args:
            context: Runtime context with Trino resource.
            query: SQL query to execute.

        Returns:
            List of (key..., hash) tuples, or None if query failed.

        """
        try:
            if context is None:
                return None
            trino = _get_context_resource(context, "trino")
            if trino is not None:
                result = trino.execute_query(query)
                if result is not None:
                    return [tuple(row) for row in result]
        except Exception as exc:
            if context and context.logger:
                context.logger.warning("hash_query_failed", query=query, error=str(exc))
            return None
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context with Trino resource.
    </PyParameter>

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query to execute.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list[tuple] | None&#x22;">
    List of (key..., hash) tuples, or None if query failed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_rows_to_hash_map&#x22;" type="&#x22;(self, rows) -> tuple[dict[tuple, Any], int]&#x22;">
  Convert query rows to key -> hash mapping and return duplicate count.

  <PySourceCode>
    ```python
    def _rows_to_hash_map(self, rows: list[tuple]) -> tuple[dict[tuple, Any], int]:
        """Convert query rows to key -> hash mapping and return duplicate count.

        Args:
            rows: List of (key..., hash) tuples from query.

        Returns:
            Tuple of (hash_map, duplicate_count) where hash_map maps keys to hashes.

        """
        hashes: dict[tuple, Any] = {}
        duplicates = 0
        for row in rows:
            key = tuple(row[:-1])
            row_hash = row[-1]
            if key not in hashes:
                hashes[key] = row_hash
            else:
                duplicates += 1
        return hashes, duplicates
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rows&#x22;" type="&#x22;list[tuple]&#x22;" value="undefined">
      List of (key..., hash) tuples from query.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of (hash\_map, duplicate\_count) where hash\_map maps keys to hashes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source_table, target_table, key_columns, columns=None, partition_column='_phlo_partition_date', tolerance=0.0, absolute_tolerance=None, hash_algorithm='xxhash64', float_precision=6, sample=None, limit=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;key_columns&#x22;" type="&#x22;list[str]&#x22;" value="null" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;" />

    <PyParameter name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;hash_algorithm&#x22;" type="&#x22;str&#x22;" value="&#x22;'xxhash64'&#x22;" />

    <PyParameter name="&#x22;float_precision&#x22;" type="&#x22;int&#x22;" value="&#x22;6&#x22;" />

    <PyParameter name="&#x22;sample&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
