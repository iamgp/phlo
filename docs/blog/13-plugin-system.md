# Part 13: Extending Phlo with Plugins

You've built pipelines, added quality checks, and set up monitoring. But what happens when you need something Phlo doesn't provide out of the box? A custom data source, a specialized validation rule, or a domain-specific transformation?

That's where the plugin system comes in.

## Why Plugins?

Every data platform eventually hits limitations:

```
Week 1:  "Phlo is great! It has everything we need."
Week 4:  "Can we add a Salesforce source?"
Week 8:  "We need a custom quality check for our business rules."
Week 12: "The finance team wants a specific transformation pattern."
```

Without plugins, you'd fork the codebase or hack around limitations. With plugins, you extend Phlo cleanly.

## The Three Plugin Types

Phlo supports three types of plugins:

| Type | Purpose | Example |
|------|---------|---------|
| **Source Connectors** | Fetch data from external systems | Salesforce, HubSpot, custom APIs |
| **Quality Checks** | Custom validation rules | Business logic, compliance rules |
| **Transforms** | Data transformation helpers | Domain-specific calculations |

Each type has a base class you inherit from, and Phlo discovers your plugins automatically via Python entry points.

## How Plugin Discovery Works

When Phlo starts, it scans for installed packages that declare entry points:

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Environment                       │
├─────────────────────────────────────────────────────────────┤
│  phlo (core)                                                │
│  phlo-plugin-salesforce (installed via pip)                 │
│  phlo-plugin-custom-checks (your internal package)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Entry Point Discovery                           │
│  importlib.metadata.entry_points()                          │
│                                                             │
│  Groups scanned:                                            │
│    • phlo.plugins.sources                                   │
│    • phlo.plugins.quality                                   │
│    • phlo.plugins.transforms                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Plugin Registry                                 │
│                                                             │
│  Sources:     [rest_api, salesforce, hubspot]               │
│  Quality:     [null_check, range_check, threshold_check]    │
│  Transforms:  [uppercase, currency_convert]                 │
└─────────────────────────────────────────────────────────────┘
```

This means:
- No manual registration required
- Install a package, restart Phlo, plugin is available
- Bad plugins don't crash the system (logged and skipped)

## Creating a Source Connector Plugin

Let's build a plugin that fetches data from JSONPlaceholder (a fake REST API for testing).

### Step 1: Project Structure

```
phlo-plugin-jsonplaceholder/
├── pyproject.toml
├── README.md
├── src/
│   └── phlo_jsonplaceholder/
│       ├── __init__.py
│       └── source.py
└── tests/
    └── test_source.py
```

### Step 2: Define the Plugin Class

```python
# src/phlo_jsonplaceholder/source.py
from typing import Iterator
import httpx
from phlo.plugins import SourceConnectorPlugin, PluginMetadata


class JSONPlaceholderSource(SourceConnectorPlugin):
    """Source connector for JSONPlaceholder API."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="jsonplaceholder",
            version="1.0.0",
            description="Fetch posts, comments, and users from JSONPlaceholder API",
            author="Your Name",
        )
    
    def fetch_data(self, config: dict) -> Iterator[dict]:
        """
        Fetch data from JSONPlaceholder.
        
        Config options:
            base_url: API base URL (default: https://jsonplaceholder.typicode.com)
            resource: posts, comments, users, etc.
            limit: Max records to fetch (default: 100)
        """
        base_url = config.get("base_url", "https://jsonplaceholder.typicode.com")
        resource = config.get("resource", "posts")
        limit = config.get("limit", 100)
        
        with httpx.Client() as client:
            response = client.get(f"{base_url}/{resource}")
            response.raise_for_status()
            
            for i, record in enumerate(response.json()):
                if i >= limit:
                    break
                yield record
    
    def get_schema(self, config: dict) -> dict:
        """Return expected schema for the resource."""
        schemas = {
            "posts": {
                "id": "integer",
                "userId": "integer",
                "title": "string",
                "body": "string",
            },
            "users": {
                "id": "integer",
                "name": "string",
                "email": "string",
                "username": "string",
            },
        }
        resource = config.get("resource", "posts")
        return schemas.get(resource, {})
    
    def test_connection(self, config: dict) -> bool:
        """Verify API is reachable."""
        base_url = config.get("base_url", "https://jsonplaceholder.typicode.com")
        try:
            with httpx.Client() as client:
                response = client.get(base_url)
                return response.status_code == 200
        except Exception:
            return False
```

### Step 3: Register via Entry Points

```toml
# pyproject.toml
[project]
name = "phlo-plugin-jsonplaceholder"
version = "1.0.0"
dependencies = ["httpx>=0.24.0"]

[project.entry-points."phlo.plugins.sources"]
jsonplaceholder = "phlo_jsonplaceholder.source:JSONPlaceholderSource"
```

The entry point format is:
```
plugin_name = "module.path:ClassName"
```

### Step 4: Install and Use

```bash
# Install the plugin
pip install -e ./phlo-plugin-jsonplaceholder

# Verify it's discovered
phlo plugin list
```

Now use it in your ingestion:

```python
# workflows/ingestion/jsonplaceholder/posts.py
from phlo.plugins import get_source_connector

@asset
def jsonplaceholder_posts(context):
    """Ingest posts from JSONPlaceholder."""
    
    # Get the plugin
    source = get_source_connector("jsonplaceholder")
    
    # Fetch data
    config = {
        "resource": "posts",
        "limit": 50,
    }
    
    records = list(source.fetch_data(config))
    context.log.info(f"Fetched {len(records)} posts")
    
    # Write to Iceberg...
```

## Creating a Quality Check Plugin

Custom quality checks let you encode business rules that go beyond standard null/range checks.

### Example: Threshold Check with Tolerance

```python
# src/phlo_custom_checks/threshold.py
from dataclasses import dataclass
from phlo.plugins import QualityCheckPlugin, PluginMetadata
from phlo.quality.checks import QualityCheck, QualityCheckResult


@dataclass
class ThresholdCheck(QualityCheck):
    """Check that values fall within a threshold, with tolerance."""
    
    column: str
    min_value: float
    max_value: float
    tolerance: float = 0.05  # Allow 5% of rows to fail
    
    def execute(self, df) -> QualityCheckResult:
        total_rows = len(df)
        
        # Count violations
        violations = df[
            (df[self.column] < self.min_value) | 
            (df[self.column] > self.max_value)
        ]
        violation_count = len(violations)
        violation_rate = violation_count / total_rows if total_rows > 0 else 0
        
        passed = violation_rate <= self.tolerance
        
        return QualityCheckResult(
            passed=passed,
            check_name=f"threshold_{self.column}",
            message=f"{violation_count}/{total_rows} rows outside [{self.min_value}, {self.max_value}]",
            metadata={
                "column": self.column,
                "violation_count": violation_count,
                "violation_rate": violation_rate,
                "tolerance": self.tolerance,
            },
        )


class ThresholdCheckPlugin(QualityCheckPlugin):
    """Plugin that provides threshold checking with tolerance."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="threshold_check",
            version="1.0.0",
            description="Check values within threshold with configurable tolerance",
        )
    
    def create_check(self, **kwargs) -> QualityCheck:
        return ThresholdCheck(**kwargs)
```

Register it:

```toml
# pyproject.toml
[project.entry-points."phlo.plugins.quality"]
threshold_check = "phlo_custom_checks.threshold:ThresholdCheckPlugin"
```

Use it with `@phlo.quality`:

```python
from phlo.plugins import get_quality_check

# Get the plugin
plugin = get_quality_check("threshold_check")

# Create a check instance
check = plugin.create_check(
    column="revenue",
    min_value=0,
    max_value=1000000,
    tolerance=0.01,  # Allow 1% outliers
)

# Or use directly in @phlo.quality
@phlo.quality(
    table="silver.transactions",
    checks=[
        plugin.create_check(column="amount", min_value=0, max_value=10000),
    ],
)
def transaction_quality():
    pass
```

## Creating a Transform Plugin

Transform plugins provide reusable transformation logic.

### Example: Currency Conversion

```python
# src/phlo_transforms/currency.py
import pandas as pd
from phlo.plugins import TransformationPlugin, PluginMetadata


class CurrencyConvertPlugin(TransformationPlugin):
    """Convert currency columns using exchange rates."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="currency_convert",
            version="1.0.0",
            description="Convert currency values between currencies",
        )
    
    # Exchange rates (in production, fetch from API)
    RATES = {
        ("USD", "EUR"): 0.92,
        ("USD", "GBP"): 0.79,
        ("EUR", "USD"): 1.09,
        ("EUR", "GBP"): 0.86,
        ("GBP", "USD"): 1.27,
        ("GBP", "EUR"): 1.16,
    }
    
    def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """
        Transform currency columns.
        
        Config:
            column: Column to convert
            from_currency: Source currency code
            to_currency: Target currency code
            output_column: Name for converted column (optional)
        """
        column = config["column"]
        from_curr = config["from_currency"]
        to_curr = config["to_currency"]
        output_col = config.get("output_column", f"{column}_{to_curr.lower()}")
        
        rate = self.RATES.get((from_curr, to_curr))
        if rate is None:
            raise ValueError(f"No exchange rate for {from_curr} -> {to_curr}")
        
        result = df.copy()
        result[output_col] = result[column] * rate
        return result
    
    def validate_config(self, config: dict) -> list[str]:
        """Validate configuration, return list of errors."""
        errors = []
        if "column" not in config:
            errors.append("'column' is required")
        if "from_currency" not in config:
            errors.append("'from_currency' is required")
        if "to_currency" not in config:
            errors.append("'to_currency' is required")
        return errors
```

Use it:

```python
from phlo.plugins import get_transformation

currency = get_transformation("currency_convert")

# In a Dagster asset or dbt Python model
df = currency.transform(df, {
    "column": "price_usd",
    "from_currency": "USD",
    "to_currency": "EUR",
    "output_column": "price_eur",
})
```

## Managing Plugins via CLI

The `phlo plugin` commands help you discover and troubleshoot plugins.

### List Installed Plugins

```bash
$ phlo plugin list

Installed Plugins
═════════════════

Sources:
  NAME              VERSION  SOURCE
  rest_api          built-in phlo.ingestion
  jsonplaceholder   1.0.0    phlo-plugin-jsonplaceholder

Quality Checks:
  NAME              VERSION  SOURCE
  null_check        built-in phlo.quality
  range_check       built-in phlo.quality
  freshness_check   built-in phlo.quality
  threshold_check   1.0.0    phlo-custom-checks

Transforms:
  NAME              VERSION  SOURCE
  currency_convert  1.0.0    phlo-transforms
```

### Get Plugin Details

```bash
$ phlo plugin info jsonplaceholder

Plugin: jsonplaceholder
Type: Source Connector
Version: 1.0.0
Package: phlo-plugin-jsonplaceholder
Author: Your Name

Description:
  Fetch posts, comments, and users from JSONPlaceholder API

Configuration Options:
  base_url  (string)  API base URL
  resource  (string)  Resource to fetch (posts, users, comments)
  limit     (integer) Maximum records to fetch

Example:
  source = get_source_connector("jsonplaceholder")
  data = source.fetch_data({"resource": "posts", "limit": 10})
```

### Validate Plugins

```bash
$ phlo plugin check

Validating installed plugins...

Sources:
  ✓ rest_api - OK
  ✓ jsonplaceholder - OK

Quality Checks:
  ✓ null_check - OK
  ✓ range_check - OK
  ⚠ threshold_check - WARNING: No test_check() method

Transforms:
  ✓ currency_convert - OK

Summary: 6 plugins, 0 errors, 1 warning
```

### Scaffold a New Plugin

```bash
$ phlo plugin create my-salesforce-source --type source

Creating plugin scaffold...

Created: phlo-plugin-my-salesforce-source/
├── pyproject.toml
├── README.md
├── src/
│   └── phlo_my_salesforce_source/
│       ├── __init__.py
│       └── source.py
└── tests/
    └── test_source.py

Next steps:
  1. cd phlo-plugin-my-salesforce-source
  2. Edit src/phlo_my_salesforce_source/source.py
  3. pip install -e .
  4. phlo plugin list (verify it appears)
```

## Best Practices

### 1. Keep Plugins Focused

One plugin = one responsibility. Don't create a "kitchen sink" plugin.

```python
# Good: focused plugins
class SalesforceSource(SourceConnectorPlugin): ...
class HubSpotSource(SourceConnectorPlugin): ...

# Bad: monolithic plugin
class CRMSource(SourceConnectorPlugin):
    def fetch_salesforce(self): ...
    def fetch_hubspot(self): ...
    def fetch_dynamics(self): ...
```

### 2. Handle Errors Gracefully

Plugins should never crash Phlo. Catch exceptions and return meaningful errors.

```python
def fetch_data(self, config: dict) -> Iterator[dict]:
    try:
        response = self.client.get(url)
        response.raise_for_status()
        yield from response.json()
    except httpx.HTTPStatusError as e:
        raise PluginError(f"API returned {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise PluginError(f"Network error: {e}")
```

### 3. Include Metadata

Good metadata makes plugins discoverable:

```python
@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="salesforce",
        version="2.1.0",
        description="Ingest Salesforce objects (Accounts, Contacts, Opportunities)",
        author="Data Platform Team",
        documentation_url="https://docs.yourcompany.com/plugins/salesforce",
    )
```

### 4. Write Tests

```python
# tests/test_source.py
def test_fetch_data_returns_records():
    source = JSONPlaceholderSource()
    records = list(source.fetch_data({"resource": "posts", "limit": 5}))
    
    assert len(records) == 5
    assert all("id" in r for r in records)
    assert all("title" in r for r in records)

def test_connection_check():
    source = JSONPlaceholderSource()
    assert source.test_connection({}) is True

def test_invalid_resource_handled():
    source = JSONPlaceholderSource()
    with pytest.raises(PluginError):
        list(source.fetch_data({"resource": "invalid"}))
```

### 5. Version Your Plugins

Use semantic versioning. Breaking changes = major version bump.

```toml
[project]
version = "2.0.0"  # Breaking: changed config schema
version = "1.1.0"  # Feature: added new resource type
version = "1.0.1"  # Fix: handled edge case
```

## Plugin Security

Plugins run with full access to your environment. Only install trusted plugins.

**For organizations:**
- Maintain an internal plugin registry
- Review plugin code before deployment
- Use `plugins_whitelist` in config to restrict allowed plugins:

```python
# config.py
class PhloConfig:
    plugins_whitelist: list[str] = [
        "rest_api",
        "salesforce",
        "internal_*",  # Allow all internal plugins
    ]
```

## Summary

The plugin system lets you extend Phlo without modifying core code:

- **Source Connectors**: Fetch data from any system
- **Quality Checks**: Encode custom business rules
- **Transforms**: Reusable transformation logic

Plugins are discovered automatically via Python entry points, managed via CLI, and integrate seamlessly with Phlo's decorators and assets.

**When to use plugins:**
- You need a data source Phlo doesn't support
- You have organization-specific quality rules
- You want to share reusable logic across teams

**When NOT to use plugins:**
- One-off transformations (just write Python)
- Simple quality checks (use built-in checks)
- Anything that could be a dbt model

**Next**: Return to [Part 1](01-intro-data-lakehouse.md) to review the full architecture, or explore the [example plugin package](../../examples/phlo-plugin-example/).
