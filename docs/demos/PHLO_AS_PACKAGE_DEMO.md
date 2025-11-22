# Building a Glucose Platform with Phlo (As an Installable Package)

**Demonstrates the separation between Phlo framework and user workflow code**

This guide shows how to build a glucose monitoring platform by **installing Phlo as a package** and creating your own separate project with workflow code.

---

## The Key Concept: Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    PHLO PACKAGE (Framework)                  │
├─────────────────────────────────────────────────────────────┤
│ • Installed via: pip install phlo                           │
│ • Provides: @phlo_ingestion decorator, CLI tools, core      │
│ • Location: site-packages/phlo/                             │
│ • Maintained by: Phlo team                                  │
│ • Updated: pip install --upgrade phlo                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    User installs and uses
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               USER PROJECT (Your Workflows)                  │
├─────────────────────────────────────────────────────────────┤
│ • Created via: phlo init glucose-platform                   │
│ • Contains: Your workflows, schemas, dbt models             │
│ • Location: ./glucose-platform/                             │
│ • Maintained by: You                                        │
│ • Version controlled: Your git repo                         │
└─────────────────────────────────────────────────────────────┘
```

**Users never modify Phlo package code - they only create their own workflows!**

---

## Step-by-Step: Building Your Glucose Platform

### 1. Install Phlo Package (One-time)

```bash
# Install phlo framework from PyPI (when published)
pip install phlo

# Or install from source (current development)
cd /path/to/phlo
pip install -e .

# Verify installation
phlo --version
# Output: phlo, version 1.0.0
```

**What you get:**
- ✅ `@phlo_ingestion` decorator
- ✅ `phlo` CLI tool
- ✅ Core framework code
- ✅ Testing utilities

**What you DON'T get:**
- ❌ Pre-built workflows (you create these)
- ❌ Domain-specific code
- ❌ Your business logic

---

### 2. Create Your Glucose Platform Project

```bash
# Create a new phlo project (separate from phlo package)
phlo init glucose-platform

# Output:
# 🚀 Cascade Project Initializer
#
# Creating new project: glucose-platform
#
# ✅ Successfully initialized Cascade project: glucose-platform
#
# 📁 Created structure:
#   glucose-platform/
#   ├── pyproject.toml       # Project dependencies
#   ├── .env.example         # Environment variables template
#   ├── workflows/           # Your workflow definitions
#   │   ├── ingestion/       # Data ingestion workflows
#   │   └── schemas/         # Pandera validation schemas
#   ├── transforms/dbt/      # dbt transformation models
#   └── tests/               # Workflow tests

# Navigate into your new project
cd glucose-platform
```

**Project structure (YOUR code):**
```
glucose-platform/                    ← Your project root
├── pyproject.toml                   ← Lists "phlo" as dependency
├── workflows/                       ← YOUR workflows (not in phlo package)
│   ├── ingestion/
│   │   └── nightscout/             ← You'll create this
│   │       └── glucose.py          ← Your glucose ingestion
│   └── schemas/
│       └── nightscout.py           ← Your validation schemas
├── transforms/dbt/                  ← YOUR dbt models
│   └── models/
│       ├── bronze/
│       ├── silver/
│       └── gold/
└── tests/                           ← YOUR tests
    └── test_glucose.py
```

**Key point:** This is YOUR repository, YOUR version control, YOUR code!

---

### 3. Install Your Project Dependencies

```bash
# Install your project (which includes phlo as a dependency)
pip install -e .

# This installs:
# - phlo package (from PyPI or local)
# - Your project in editable mode
# - All dependencies from pyproject.toml
```

**Your `pyproject.toml`:**
```toml
[project]
name = "glucose-platform"
version = "0.1.0"
description = "Glucose monitoring data platform"
requires-python = ">=3.11"
dependencies = [
    "phlo",  # ← Phlo as a dependency, not embedded code
]
```

---

### 4. Create Your First Workflow Using Phlo CLI

```bash
# Interactive workflow creation
phlo create-workflow

# Prompts:
# Workflow type: ingestion
# Domain name: nightscout
# Table name: glucose_entries
# Unique key field: _id
# Cron schedule: 0 */1 * * *
# API base URL: https://gwp-diabetes.fly.dev/api/v1

# Output:
# 🚀 Creating ingestion workflow for nightscout.glucose_entries...
#
# ✅ Created files:
#   ✓ workflows/schemas/nightscout.py
#   ✓ workflows/ingestion/nightscout/glucose_entries.py
#   ✓ tests/test_nightscout_glucose_entries.py
#
# 📝 Next steps:
#   1. Edit schema: workflows/schemas/nightscout.py
#   2. Configure API: workflows/ingestion/nightscout/glucose_entries.py
#   3. Start Dagster: phlo dev
#   4. Test: phlo test nightscout
```

**What just happened:**
- ✅ Phlo CLI (from installed package) scaffolded files
- ✅ Files created in YOUR `workflows/` directory
- ✅ Templates use `@phlo_ingestion` from installed package
- ✅ All code is yours to customize

---

### 5. Define Your Schema (Your Code)

**Edit `workflows/schemas/nightscout.py`:**

```python
"""
Pandera schemas for nightscout domain.

This is YOUR code in YOUR project - not part of the phlo package.
"""

import pandera as pa
from pandera.typing import Series


class RawGlucoseEntries(pa.DataFrameModel):
    """
    Raw glucose entries data schema.

    Define YOUR validation rules here.
    """

    _id: Series[str] = pa.Field(
        description="Unique identifier for deduplication",
        nullable=False,
    )

    # Add your fields based on Nightscout API
    sgv: Series[int] = pa.Field(
        ge=1,
        le=1000,
        description="Sensor glucose value in mg/dL"
    )

    date: Series[int] = pa.Field(
        description="Unix timestamp in milliseconds"
    )

    dateString: Series[str] = pa.Field(
        description="ISO 8601 timestamp"
    )

    direction: Series[str] = pa.Field(
        isin=["Flat", "FortyFiveUp", "SingleUp", "DoubleUp",
              "FortyFiveDown", "SingleDown", "DoubleDown", "NONE"],
        nullable=True,
        description="Trend direction"
    )

    device: Series[str] = pa.Field(
        nullable=True,
        description="Device name"
    )

    class Config:
        strict = True
        coerce = True
```

**Key point:** This schema is in YOUR project, not in the phlo package!

---

### 6. Configure Your Ingestion (Your Code)

**Edit `workflows/ingestion/nightscout/glucose_entries.py`:**

```python
"""
Nightscout glucose entries ingestion asset.

This is YOUR ingestion logic - uses @phlo_ingestion from installed package.
"""

from dlt.sources.rest_api import rest_api
from phlo.ingestion import phlo_ingestion  # ← Import from installed package
from workflows.schemas.nightscout import RawGlucoseEntries  # ← Your schema


@phlo_ingestion(  # ← Decorator from phlo package
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,  # ← Your schema class
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """
    YOUR ingestion logic for glucose data.

    The @phlo_ingestion decorator (from phlo package) handles:
    - Schema generation
    - Validation
    - Iceberg operations
    - Branch management

    You only define the data source!
    """
    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    # YOUR API configuration
    source = rest_api({
        "client": {
            "base_url": "https://gwp-diabetes.fly.dev/api/v1",
        },
        "resources": [{
            "name": "entries",
            "endpoint": {
                "path": "entries.json",
                "params": {
                    "count": 10000,
                    "find[dateString][$gte]": start_time,
                    "find[dateString][$lt]": end_time,
                },
            },
        }],
    })

    return source
```

**Separation illustrated:**
- `@phlo_ingestion` → From **phlo package** (framework)
- `glucose_entries()` → YOUR code (business logic)
- `RawGlucoseEntries` → YOUR schema (domain model)

---

### 7. Create Your dbt Models (Your Code)

**Create `transforms/dbt/models/bronze/stg_glucose_entries.sql`:**

```sql
-- YOUR dbt model in YOUR project

{{ config(
    materialized='table',
    tags=['nightscout', 'bronze']
) }}

-- Clean and standardize raw glucose data
select
    _id as entry_id,
    sgv as glucose_mg_dl,
    cast(from_unixtime(date / 1000) as timestamp) as reading_timestamp,
    "dateString" as timestamp_iso,
    direction,
    coalesce(direction, 'NONE') as trend,
    device
from {{ source('raw_iceberg', 'glucose_entries') }}
where sgv is not null
```

**Create `transforms/dbt/models/silver/fct_glucose_readings.sql`:**

```sql
-- YOUR business logic in YOUR project

{{ config(
    materialized='table',
    tags=['nightscout', 'silver']
) }}

select
    entry_id,
    glucose_mg_dl,
    reading_timestamp,

    -- YOUR time dimensions
    extract(hour from reading_timestamp) as hour_of_day,
    day_of_week(reading_timestamp) as day_of_week,

    -- YOUR business logic for glucose categories
    case
        when glucose_mg_dl < 70 then 'hypoglycemia'
        when glucose_mg_dl between 70 and 180 then 'in_range'
        when glucose_mg_dl > 180 then 'hyperglycemia'
    end as glucose_category,

    -- YOUR KPI calculations
    case when glucose_mg_dl between 70 and 180 then 1 else 0 end as is_in_range

from {{ ref('stg_glucose_entries') }}
```

---

### 8. Start Your Platform

```bash
# Start Dagster UI (using phlo CLI from installed package)
phlo dev

# Output:
# 🚀 Starting Cascade development server...
#
# 📂 Workflows directory: workflows
# 🌐 Starting server at http://127.0.0.1:3000
#
# Dagster launches and discovers YOUR workflows automatically!
```

**What happens:**
1. `phlo dev` command (from installed package) starts Dagster
2. Dagster auto-discovers workflows in YOUR `workflows/` directory
3. Your `@phlo_ingestion` assets appear in Dagster UI
4. Framework code runs from installed package
5. Your business logic runs from YOUR project

---

### 9. Run Your Ingestion

**Option A: Via Phlo CLI**

```bash
# Use phlo CLI to materialize (for Docker deployments)
phlo materialize glucose_entries --partition 2024-01-20

# Output:
# ⚡ Materializing glucose_entries...
# [Dagster executes your workflow using framework from installed package]
# ✅ Successfully materialized glucose_entries
```

**Option B: Via Dagster UI**

1. Open http://localhost:3000
2. Navigate to Assets → nightscout → glucose_entries
3. Click "Materialize"
4. Select partition: 2024-01-20
5. Watch YOUR workflow execute using PHLO framework

---

### 10. Run dbt Transformations (Your Models)

```bash
cd transforms/dbt

# Run YOUR dbt models (not part of phlo package)
dbt run --models bronze.stg_glucose_entries
dbt run --models silver.fct_glucose_readings

# These are YOUR transformations, YOUR business logic
```

---

## The Complete Separation

### What's in the Phlo Package (Framework)

**Location:** `site-packages/phlo/` (installed)

```
phlo/
├── ingestion/
│   └── decorator.py           # @phlo_ingestion decorator
├── schemas/
│   └── converter.py           # Pandera → PyIceberg conversion
├── iceberg/
│   ├── catalog.py             # Nessie integration
│   └── tables.py              # Table management
├── cli/
│   ├── main.py                # phlo CLI commands
│   └── scaffold.py            # Workflow scaffolding
├── testing/
│   └── fixtures.py            # Test utilities
└── config.py                  # Framework configuration
```

**Users never modify these files!**

### What's in Your Project (Your Code)

**Location:** `./glucose-platform/` (your repo)

```
glucose-platform/
├── workflows/                  # YOUR workflows
│   ├── ingestion/
│   │   └── nightscout/
│   │       └── glucose_entries.py
│   └── schemas/
│       └── nightscout.py
├── transforms/dbt/             # YOUR dbt models
│   └── models/
│       ├── bronze/
│       │   └── stg_glucose_entries.sql
│       └── silver/
│           └── fct_glucose_readings.sql
└── tests/                      # YOUR tests
    └── test_glucose.py
```

**You maintain these files in your git repo!**

---

## How the Separation Works

### 1. Imports Show the Separation

**Your workflow file:**
```python
# Import framework from installed package
from phlo.ingestion import phlo_ingestion  # ← Phlo package

# Import your code from your project
from workflows.schemas.nightscout import RawGlucoseEntries  # ← Your code

# Use framework decorator on your function
@phlo_ingestion(  # ← Framework
    validation_schema=RawGlucoseEntries,  # ← Your schema
)
def glucose_entries(partition_date: str):  # ← Your logic
    # Your code here
    pass
```

### 2. CLI Shows the Separation

```bash
# CLI from installed package
phlo --version                    # Framework version

# Creates files in YOUR project
phlo create-workflow              # Scaffolds in ./workflows/

# Runs YOUR workflows using framework
phlo dev                          # Discovers ./workflows/
```

### 3. Version Control Shows the Separation

```bash
# Your git repo (glucose-platform)
git init
git add workflows/ transforms/ tests/
git commit -m "Add glucose monitoring workflows"
git push origin main

# Phlo package updates separately
pip install --upgrade phlo
```

---

## Workflow: Adding a New Data Source

Let's add medication tracking to show the pattern:

### Step 1: Scaffold with Phlo CLI

```bash
# Still in your glucose-platform project
phlo create-workflow

# Prompts:
# Workflow type: ingestion
# Domain name: nightscout
# Table name: medication_entries
# Unique key field: _id
# Cron schedule: 0 */6 * * *
# API base URL: https://gwp-diabetes.fly.dev/api/v1
```

**Created in YOUR project:**
- `workflows/schemas/nightscout.py` (updated)
- `workflows/ingestion/nightscout/medication_entries.py` (new)
- `tests/test_nightscout_medication_entries.py` (new)

### Step 2: Customize Your Schema

**Edit `workflows/schemas/nightscout.py`:**
```python
class RawMedicationEntries(pa.DataFrameModel):
    """YOUR medication schema."""
    _id: Series[str] = pa.Field(nullable=False)
    insulin_type: Series[str] = pa.Field()
    units: Series[float] = pa.Field(ge=0)
    timestamp: Series[str] = pa.Field()
```

### Step 3: Configure Your API

**Edit `workflows/ingestion/nightscout/medication_entries.py`:**
```python
@phlo_ingestion(  # ← Framework
    table_name="medication_entries",
    unique_key="_id",
    validation_schema=RawMedicationEntries,  # ← Your schema
    group="nightscout",
)
def medication_entries(partition_date: str):  # ← Your logic
    # YOUR API configuration
    source = rest_api({...})
    return source
```

### Step 4: Restart and Run

```bash
# Restart Dagster (picks up new workflow)
phlo dev

# Run your new workflow
phlo materialize medication_entries --partition 2024-01-20
```

**All your code, using phlo framework!**

---

## Benefits of This Separation

### 1. Clean Upgrades

```bash
# Upgrade phlo framework without touching YOUR code
pip install --upgrade phlo

# Your workflows continue working
# No merge conflicts
# No need to update your project
```

### 2. Multiple Projects

```bash
# Create different projects for different domains
phlo init glucose-platform
phlo init weather-analytics
phlo init financial-pipeline

# All use same phlo package
# Each has its own workflows
# Independent version control
```

### 3. Team Collaboration

```
Team A: Maintains phlo package (framework)
   ↓
Releases to PyPI
   ↓
Team B: Uses phlo to build glucose platform (your workflows)
Team C: Uses phlo to build weather platform (their workflows)
Team D: Uses phlo to build financial platform (their workflows)
```

### 4. Testing Isolation

```bash
# Test phlo framework
cd /path/to/phlo
pytest tests/

# Test YOUR workflows
cd /path/to/glucose-platform
phlo test
pytest tests/
```

---

## Directory Comparison

### ❌ Wrong: Everything in Phlo Repo

```
phlo/                                    # Single repo
├── src/phlo/                           # Framework code
│   └── defs/ingestion/
│       ├── nightscout/                 # Mixed in!
│       │   └── glucose.py
│       └── github/                     # Mixed in!
│           └── repos.py
```

**Problems:**
- User workflows mixed with framework code
- Can't upgrade framework without affecting workflows
- Users must fork entire repo
- Merge conflicts on framework updates

### ✅ Correct: Separate Package and Projects

```
# Phlo package (installed via pip)
site-packages/phlo/
└── ingestion/decorator.py              # Framework only

# Your glucose project (your repo)
glucose-platform/
└── workflows/ingestion/nightscout/
    └── glucose.py                      # Your code

# Someone else's weather project (their repo)
weather-analytics/
└── workflows/ingestion/openweather/
    └── observations.py                 # Their code
```

**Benefits:**
- ✅ Clear separation
- ✅ Independent upgrades
- ✅ Multiple projects use same framework
- ✅ No merge conflicts

---

## Publishing Your Platform

Once you've built your glucose platform:

```bash
# Your project is a standard Python package
cd glucose-platform

# Build distribution
python -m build

# Publish to your private PyPI or deploy
# - Docker image with your workflows
# - Deploy to cloud
# - Share with team

# Others can use your platform:
pip install glucose-platform
```

---

## Summary

### The Phlo Package (Framework)
- **What:** Core framework, decorators, CLI tools
- **Installed:** `pip install phlo`
- **Location:** `site-packages/phlo/`
- **Maintained by:** Phlo team
- **Updated:** `pip install --upgrade phlo`

### Your Glucose Platform (Workflows)
- **What:** Your workflows, schemas, dbt models
- **Created:** `phlo init glucose-platform`
- **Location:** `./glucose-platform/`
- **Maintained by:** You
- **Version control:** Your git repo

### The Workflow

```bash
# 1. Install framework (once)
pip install phlo

# 2. Create your project (once)
phlo init glucose-platform
cd glucose-platform

# 3. Add workflows (repeatable)
phlo create-workflow  # Scaffolds in YOUR project

# 4. Customize (ongoing)
# Edit workflows/schemas/
# Edit workflows/ingestion/
# Edit transforms/dbt/

# 5. Run (ongoing)
phlo dev              # Start Dagster with YOUR workflows
phlo test             # Test YOUR code
phlo materialize      # Run YOUR pipelines

# 6. Upgrade framework (as needed)
pip install --upgrade phlo  # YOUR code unchanged
```

---

## Next Steps

1. **Try it yourself:**
   ```bash
   phlo init my-glucose-platform
   cd my-glucose-platform
   phlo create-workflow
   ```

2. **Read the guides:**
   - Package architecture: `/INSTALLABLE_PACKAGE_PLAN.md`
   - Workflow development: `/docs/guides/workflow-development.md`

3. **Build more pipelines:**
   - Add medication tracking
   - Add meal logging
   - Add exercise data
   - Join all sources

**The key: Phlo is a framework you install, not a repo you fork!**
