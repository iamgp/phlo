# CASCADE-003: Invalid Cron Expression

**Error Type:** Discovery and Configuration Error
**Severity:** Medium
**Exception Class:** `CascadeCronError`

## Description

This error occurs when the `cron` schedule expression provided to the `@cascade_ingestion` decorator is invalid or malformed. Cascade validates cron expressions to ensure assets are scheduled correctly.

## Common Causes

1. **Invalid cron syntax**
   - Wrong number of fields (must be 5 fields)
   - Invalid field values
   - Unsupported special characters

2. **Incorrect field order**
   - Fields must be: minute hour day_of_month month day_of_week
   - Common mistake: swapping day_of_month and month

3. **Invalid ranges**
   - Values outside valid ranges (e.g., hour=25)
   - Invalid step values (e.g., */0)

4. **Quoting issues**
   - Missing quotes around cron expression
   - Extra quotes or escape characters

## Cron Expression Format

```
 ┌───────────── minute (0 - 59)
 │ ┌───────────── hour (0 - 23)
 │ │ ┌───────────── day of month (1 - 31)
 │ │ │ ┌───────────── month (1 - 12)
 │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday=0)
 │ │ │ │ │
 * * * * *
```

## Solutions

### Solution 1: Use standard cron syntax

Ensure your cron expression has 5 fields with valid values:

```python
@cascade_ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
    cron="0 */1 * * *",  # ✅ Valid: Every hour at minute 0
)
def weather_observations(partition: str):
    pass
```

### Solution 2: Test on crontab.guru

Before using a cron expression, test it at [crontab.guru](https://crontab.guru):

```python
# Test this expression: 0 */1 * * *
# crontab.guru will show: "At minute 0 past every hour"
```

### Solution 3: Use common schedules

Use these verified common schedules:

```python
# Every hour
cron="0 */1 * * *"

# Every day at midnight
cron="0 0 * * *"

# Every day at 2 AM
cron="0 2 * * *"

# Every Monday at 9 AM
cron="0 9 * * 1"

# Every 15 minutes
cron="*/15 * * * *"

# Twice daily (6 AM and 6 PM)
cron="0 6,18 * * *"
```

### Solution 4: Quote the expression

Always quote your cron expression:

```python
# ✅ Correct
cron="0 */1 * * *"

# ❌ Wrong (no quotes)
cron=0 */1 * * *  # SyntaxError!
```

## Examples

### ❌ Incorrect: Wrong number of fields

```python
@cascade_ingestion(
    cron="0 */1 * *",  # ❌ Only 4 fields (need 5)
    ...
)
```

### ✅ Correct: 5 fields

```python
@cascade_ingestion(
    cron="0 */1 * * *",  # ✅ All 5 fields present
    ...
)
```

### ❌ Incorrect: Invalid hour value

```python
@cascade_ingestion(
    cron="0 25 * * *",  # ❌ Hour 25 is invalid (max is 23)
    ...
)
```

### ✅ Correct: Valid hour value

```python
@cascade_ingestion(
    cron="0 23 * * *",  # ✅ Hour 23 is valid (11 PM)
    ...
)
```

### ❌ Incorrect: Invalid step value

```python
@cascade_ingestion(
    cron="*/0 * * * *",  # ❌ Step value 0 is invalid
    ...
)
```

### ✅ Correct: Valid step value

```python
@cascade_ingestion(
    cron="*/5 * * * *",  # ✅ Every 5 minutes
    ...
)
```

## Cron Field Ranges

| Field | Valid Values | Special Characters |
|-------|--------------|-------------------|
| minute | 0-59 | `*` `,` `-` `/` |
| hour | 0-23 | `*` `,` `-` `/` |
| day_of_month | 1-31 | `*` `,` `-` `/` `?` `L` `W` |
| month | 1-12 | `*` `,` `-` `/` |
| day_of_week | 0-6 (Sun=0) | `*` `,` `-` `/` `?` `L` `#` |

## Common Patterns

### Hourly Schedules
```python
cron="0 */1 * * *"     # Every hour
cron="0 */2 * * *"     # Every 2 hours
cron="0 */6 * * *"     # Every 6 hours
cron="30 */1 * * *"    # Every hour at :30
```

### Daily Schedules
```python
cron="0 0 * * *"       # Midnight
cron="0 6 * * *"       # 6 AM
cron="0 12 * * *"      # Noon
cron="0 18 * * *"      # 6 PM
```

### Weekly Schedules
```python
cron="0 0 * * 0"       # Sunday midnight
cron="0 9 * * 1"       # Monday 9 AM
cron="0 0 * * 5"       # Friday midnight
```

### Monthly Schedules
```python
cron="0 0 1 * *"       # First day of month
cron="0 0 15 * *"      # 15th of month
cron="0 0 L * *"       # Last day of month (if supported)
```

## Debugging Steps

1. **Validate cron syntax**
   ```python
   from croniter import croniter
   from datetime import datetime

   try:
       cron_expr = "0 */1 * * *"
       base = datetime.now()
       iter = croniter(cron_expr, base)
       print(f"✅ Valid cron: next run at {iter.get_next(datetime)}")
   except Exception as e:
       print(f"❌ Invalid cron: {e}")
   ```

2. **Test on crontab.guru**
   ```
   Visit: https://crontab.guru/
   Enter: 0 */1 * * *
   Verify: "At minute 0 past every hour"
   ```

3. **Check Dagster schedule**
   ```bash
   dagster schedule list
   dagster schedule logs my_schedule
   ```

4. **Verify schedule in UI**
   - Open Dagster UI
   - Navigate to Schedules
   - Check if your schedule appears
   - View next scheduled run time

## Related Errors

- [CASCADE-001: Asset Not Discovered](./CASCADE-001.md) - Asset with schedule not found
- [CASCADE-005: Missing Schema](./CASCADE-005.md) - Schema required for scheduled assets

## Prevention

1. **Use constants for common schedules**
   ```python
   # config.py
   HOURLY = "0 */1 * * *"
   DAILY = "0 0 * * *"
   WEEKLY = "0 0 * * 0"

   # ingestion.py
   from config import HOURLY

   @cascade_ingestion(
       cron=HOURLY,  # ✅ Use constant
       ...
   )
   ```

2. **Add cron validation tests**
   ```python
   # tests/test_schedules.py
   from croniter import croniter

   def test_cron_expressions_valid():
       schedules = [
           "0 */1 * * *",  # Hourly
           "0 0 * * *",    # Daily
       ]

       for cron_expr in schedules:
           try:
               croniter(cron_expr)
           except Exception as e:
               pytest.fail(f"Invalid cron '{cron_expr}': {e}")
   ```

3. **Document schedule rationale**
   ```python
   @cascade_ingestion(
       unique_key="observation_id",
       validation_schema=WeatherObservations,
       cron="0 */1 * * *",  # Run hourly to match API update frequency
   )
   def weather_observations(partition: str):
       """
       Fetch weather observations every hour.

       Schedule: Hourly (0 */1 * * *)
       Rationale: Weather API updates hourly at :00
       """
       pass
   ```

4. **Use schedule builders**
   ```python
   def hourly(minute: int = 0) -> str:
       """Generate hourly cron expression."""
       return f"{minute} */1 * * *"

   def daily(hour: int = 0, minute: int = 0) -> str:
       """Generate daily cron expression."""
       return f"{minute} {hour} * * *"

   @cascade_ingestion(
       cron=hourly(minute=0),  # ✅ Type-safe schedule builder
       ...
   )
   ```

## Additional Resources

- [Crontab Guru](https://crontab.guru) - Interactive cron expression tester
- [Cron Wikipedia](https://en.wikipedia.org/wiki/Cron) - Cron format specification
- [Dagster Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) - Dagster scheduling guide
- [croniter Library](https://github.com/kiorky/croniter) - Python cron iterator
