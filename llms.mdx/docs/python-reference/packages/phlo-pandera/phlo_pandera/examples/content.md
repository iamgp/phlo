# examples (/docs/python-reference/packages/phlo-pandera/phlo_pandera/examples)



Examples of using the @phlo\_pandera decorator.

This module demonstrates all quality check types and decorator patterns.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;CustomerDimensionsSchema&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/examples/CustomerDimensionsSchema&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;weather_quality_basic&#x22;" type="&#x22;()&#x22;">
      Quality checks for weather observations.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="bronze.weather_observations",
            checks=[
                NullCheck(columns=["station_id", "temperature"]),
                RangeCheck(column="temperature", min_value=-50, max_value=60),
            ],
            group="weather",
        )
        def weather_quality_basic():
            """Quality checks for weather observations."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;sensor_quality_comprehensive&#x22;" type="&#x22;()&#x22;">
      Comprehensive quality checks for sensor readings.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="bronze.sensor_readings",
            checks=[
                # No nulls in critical columns
                NullCheck(columns=["sensor_id", "reading_value", "timestamp"]),
                # Values within expected range
                RangeCheck(column="reading_value", min_value=0, max_value=100),
                # Data is fresh (< 2 hours old)
                FreshnessCheck(timestamp_column="timestamp", max_age_hours=2),
                # Sensor IDs are unique per timestamp
                UniqueCheck(columns=["sensor_id", "timestamp"]),
                # At least 100 readings expected
                CountCheck(min_rows=100),
            ],
            group="sensors",
            blocking=True,
        )
        def sensor_quality_comprehensive():
            """Comprehensive quality checks for sensor readings."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;customer_quality_permissive&#x22;" type="&#x22;()&#x22;">
      Quality checks for customer data with permissive thresholds.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="bronze.customer_data",
            checks=[
                # Allow up to 5% null values in optional fields
                NullCheck(columns=["phone", "address"], allow_threshold=0.05),
                # Allow up to 1% out-of-range values
                RangeCheck(column="age", min_value=0, max_value=150, allow_threshold=0.01),
                # Allow up to 0.5% duplicates
                UniqueCheck(columns=["customer_id"], allow_threshold=0.005),
            ],
            group="crm",
            warn_threshold=0.3,  # Warn if more than 30% of checks fail
        )
        def customer_quality_permissive():
            """Quality checks for customer data with permissive thresholds."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;transaction_quality_custom&#x22;" type="&#x22;()&#x22;">
      Quality checks for transactions with custom SQL validation.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="bronze.transactions",
            checks=[
                NullCheck(columns=["transaction_id", "amount"]),
                # Custom check: amount must be positive
                CustomSQLCheck(
                    name_="positive_amount",
                    sql="SELECT (amount > 0) AS is_valid FROM data",
                ),
                # Custom check: end_date must be after start_date
                CustomSQLCheck(
                    name_="date_consistency",
                    sql="SELECT (end_date >= start_date) AS is_valid FROM data",
                ),
            ],
            group="payments",
        )
        def transaction_quality_custom():
            """Quality checks for transactions with custom SQL validation."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;customer_dims_quality_schema&#x22;" type="&#x22;()&#x22;">
      Quality checks using Pandera schema validation.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="silver.customer_dimensions",
            checks=[
                SchemaCheck(schema=CustomerDimensionsSchema),
            ],
            group="dimensions",
            blocking=True,
        )
        def customer_dims_quality_schema():
            """Quality checks using Pandera schema validation."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;telemetry_quality_partitioned&#x22;" type="&#x22;()&#x22;">
      Quality checks for partitioned telemetry data.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="bronze.sensor_events",
            checks=[
                NullCheck(columns=["sensor_id", "timestamp"]),
                RangeCheck(column="reading_value", min_value=0, max_value=1000),
                FreshnessCheck(timestamp_column="timestamp", max_age_hours=24),
            ],
            group="telemetry",
            blocking=True,
        )
        def telemetry_quality_partitioned():
            """Quality checks for partitioned telemetry data."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;test_quality_duckdb&#x22;" type="&#x22;()&#x22;">
      Quality checks using DuckDB backend.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="local.test_data",
            checks=[
                NullCheck(columns=["id", "value"]),
                CountCheck(min_rows=1, max_rows=1000),
            ],
            group="testing",
            backend="duckdb",
        )
        def test_quality_duckdb():
            """Quality checks using DuckDB backend."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;order_quality_business_rules&#x22;" type="&#x22;()&#x22;">
      Quality checks for orders with business rule validation.

      <PySourceCode>
        ```python
        @phlo_pandera(
            table="silver.order_details",
            checks=[
                # Data quality
                NullCheck(columns=["order_id", "product_id", "quantity", "unit_price"]),
                CountCheck(min_rows=0),  # Allow empty
                # Value validation
                RangeCheck(column="quantity", min_value=1, max_value=10000),
                RangeCheck(column="unit_price", min_value=0, max_value=1000000),
                # Business rules
                CustomSQLCheck(
                    name_="valid_total",
                    sql="SELECT (quantity * unit_price = total_price) FROM data",
                ),
                CustomSQLCheck(
                    name_="valid_discount",
                    sql="SELECT (discount_percent BETWEEN 0 AND 100) FROM data",
                ),
                # Uniqueness
                UniqueCheck(columns=["order_id", "line_item_number"]),
            ],
            group="sales",
            warn_threshold=0.1,  # Warn if more than 10% fail
        )
        def order_quality_business_rules():
            """Quality checks for orders with business rule validation."""
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;demo_decorator_benefits&#x22;" type="&#x22;()&#x22;">
      Demonstrate the benefits of @phlo\_pandera decorator.

      BEFORE (Manual, \~40 lines of boilerplate, Dagster adapter example):

      ```python
      from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
      import pandas as pd

      @asset_check(name="weather_quality", asset=AssetKey(["weather_observations"]), blocking=True)
      def weather_quality_check(context, trino) -> AssetCheckResult:
          with trino.cursor() as cursor:
              cursor.execute("SELECT * FROM bronze.weather_observations")
              df = pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description])

          null_count = df['station_id'].isna().sum()
          if null_count > 0:
              return AssetCheckResult(passed=False, metadata=\{"error": f"\{null_count\} nulls"\})

          violations = ((df['temperature'] \< -50) | (df['temperature'] > 60)).sum()
          if violations > 0:
              return AssetCheckResult(passed=False, metadata=\{"error": f"\{violations\} out-of-range"\})

          return AssetCheckResult(passed=True, metadata=\{"rows": len(df)\})
      ```

      AFTER (With @phlo\_pandera, 8 lines - 80% reduction!):

      ```python
      from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

      @phlo_pandera(
          table="bronze.weather_observations",
          checks=[
              NullCheck(columns=["station_id", "temperature"]),
              RangeCheck(column="temperature", min_value=-50, max_value=60),
          ],
      )
      def weather_quality():
          pass
      ```

      <PySourceCode>
        ````python
        def demo_decorator_benefits():
            """
            Demonstrate the benefits of @phlo_pandera decorator.

            BEFORE (Manual, ~40 lines of boilerplate, Dagster adapter example):
            \```python
            from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
            import pandas as pd

            @asset_check(name="weather_quality", asset=AssetKey(["weather_observations"]), blocking=True)
            def weather_quality_check(context, trino) -> AssetCheckResult:
                with trino.cursor() as cursor:
                    cursor.execute("SELECT * FROM bronze.weather_observations")
                    df = pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description])

                null_count = df['station_id'].isna().sum()
                if null_count > 0:
                    return AssetCheckResult(passed=False, metadata={"error": f"{null_count} nulls"})

                violations = ((df['temperature'] < -50) | (df['temperature'] > 60)).sum()
                if violations > 0:
                    return AssetCheckResult(passed=False, metadata={"error": f"{violations} out-of-range"})

                return AssetCheckResult(passed=True, metadata={"rows": len(df)})
            \```

            AFTER (With @phlo_pandera, 8 lines - 80% reduction!):
            \```python
            from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

            @phlo_pandera(
                table="bronze.weather_observations",
                checks=[
                    NullCheck(columns=["station_id", "temperature"]),
                    RangeCheck(column="temperature", min_value=-50, max_value=60),
                ],
            )
            def weather_quality():
                pass
            \```
            """
            pass
        ````
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
