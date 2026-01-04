# Phlo Pokemon Reference Data Demo

A demo project showing how to build a reference data lakehouse with Phlo. Ingests Pokemon, types, abilities, moves, and generations from PokeAPI into an Iceberg lakehouse with medallion architecture.

## Why Pokemon Reference Data?

This example demonstrates clean reference data patterns for building dimensional data warehouses:

- **Simple, familiar domain**: Pokemon data is easy to understand and verify
- **Multiple reference entities**: 5 distinct entities with clean relationships
- **Generic API pattern**: Reusable REST API helper for any PokeAPI resource
- **Minimal configuration**: Demonstrates phlo's zero-config approach
- **Clean silver/gold separation**: Simple staging → dimensions → metrics flow
- **Production-ready patterns**: Proper schema validation, freshness checks, and merge strategies

## Quick Start

### Standard Mode

```bash
cd phlo-examples/pokemon
phlo services init
phlo services start
```

### Development Mode

For developing phlo itself with instant iteration:

```bash
cd phlo-examples/pokemon
phlo services init --dev --phlo-source /path/to/phlo
phlo services start
```

This mounts the phlo monorepo into the Dagster container and installs `phlo[defaults]` as an editable install.

### First Ingestion

```bash
# Materialize all Pokemon reference data
phlo materialize --select "group:pokemon"

# Or materialize individual entities
phlo materialize pokemon --partition 2024-01-15
phlo materialize pokemon_types --partition 2024-01-15
phlo materialize pokemon_abilities --partition 2024-01-15
phlo materialize pokemon_moves --partition 2024-01-15
phlo materialize pokemon_generations --partition 2024-01-15
```

## Services

After starting, access:

- **Dagster UI**: http://localhost:3000 - Orchestration & monitoring
- **Trino**: http://localhost:8080 - Query engine
- **MinIO Console**: http://localhost:9101 - Object storage (minio/minio123)
- **pgweb**: http://localhost:8081 - Database admin

Note: Superset is disabled in this example (`phlo.yaml`) to keep the stack minimal.

## Project Structure

```
pokemon/
├── .phlo/                      # Infrastructure config
│   └── dagster/                # Dagster workspace
├── workflows/                  # Data workflows
│   ├── ingestion/              # Ingestion assets (@phlo_ingestion)
│   │   ├── helpers.py          # Generic PokeAPI DLT source
│   │   └── pokemon.py          # 5 ingestion assets
│   ├── schemas/                # Pandera validation schemas
│   │   └── pokemon.py          # 5 entity schemas
│   └── transforms/dbt/         # dbt transformation models
│       ├── silver/             # Staging models (3)
│       │   ├── stg_pokemon.sql
│       │   ├── stg_pokemon_types.sql
│       │   └── stg_pokemon_abilities.sql
│       └── gold/               # Dimension & fact tables (3)
│           ├── dim_pokemon.sql
│           ├── dim_types.sql
│           └── fct_pokemon_by_generation.sql
├── tests/                      # Workflow tests
├── phlo.yaml                   # Minimal infrastructure config
└── pyproject.toml              # Project dependencies
```

## Architecture

### Data Flow

```
PokeAPI → Bronze (raw) → Silver (staged) → Gold (analytics)
```

**1. Ingestion (Bronze)**

Five DLT ingestion pipelines fetch reference data from PokeAPI:

- `pokemon`: ~1,000 Pokemon (Gen 1-9)
- `pokemon_types`: ~20 types (fire, water, grass, etc.)
- `pokemon_abilities`: ~400 abilities
- `pokemon_moves`: ~1,000 moves
- `pokemon_generations`: 9 generations

**2. Silver Layer**

Staging models clean and standardize raw data:

- Extract IDs from API URLs
- Normalize names (lowercase, trim)
- Add phlo metadata columns

**3. Gold Layer**

Analytics-ready dimensions and facts:

- `dim_pokemon`: Pokemon with generation/region enrichment
- `dim_types`: Type reference dimension
- `fct_pokemon_by_generation`: Aggregated metrics

### Generic API Helper Pattern

The key pattern in this example is the **reusable REST API source**:

**workflows/ingestion/helpers.py**:
```python
from dlt.sources.rest_api import rest_api_source

def pokeapi(resource: str, limit: int = 100):
    """Create a DLT source for any PokeAPI resource."""
    config = {
        "client": {"base_url": "https://pokeapi.co/api/v2/"},
        "resources": [{
            "name": resource,
            "endpoint": {
                "path": resource,
                "params": {"limit": limit, "offset": 0},
                "data_selector": "results",
            },
        }],
    }
    return rest_api_source(config)
```

**Usage**:
```python
@phlo_ingestion(
    table_name="pokemon",
    unique_key="name",
    validation_schema=RawPokemon,
    group="pokemon",
    merge_strategy="merge",
)
def pokemon(partition_date: str):
    """Ingest Pokemon list from PokeAPI."""
    return pokeapi("pokemon", limit=1025)
```

This pattern makes it trivial to add new PokeAPI resources - just call `pokeapi("new-resource")`.

## Data Model

### 5 Reference Entities

**1. Pokemon** (`pokemon`)
- Core entity: ~1,000 Pokemon across 9 generations
- Fields: `name`, `url` (API endpoint)
- Unique key: `name`
- Update frequency: Weekly (new Pokemon rarely added)

**2. Types** (`pokemon_types`)
- Type taxonomy: fire, water, grass, electric, etc.
- Fields: `name`, `url`
- Unique key: `name`
- Update frequency: Monthly (types very stable)

**3. Abilities** (`pokemon_abilities`)
- Pokemon abilities: levitate, overgrow, torrent, etc.
- Fields: `name`, `url`
- Unique key: `name`
- Update frequency: Monthly

**4. Moves** (`pokemon_moves`)
- Pokemon moves: tackle, thunderbolt, hydro-pump, etc.
- Fields: `name`, `url`
- Unique key: `name`
- Update frequency: Monthly

**5. Generations** (`pokemon_generations`)
- Pokemon generations: generation-i through generation-ix
- Fields: `name`, `url`
- Unique key: `name`
- Update frequency: Monthly (new generations rare)

### Entity Relationships

```
pokemon (1,000)
  ├─ generation (1:N) → pokemon_generations (9)
  ├─ region (1:N) → derived from generation
  └─ future: types, abilities, moves (many:many via detailed API)
```

Note: This example ingests **list endpoints only**. The PokeAPI detail endpoints (e.g., `/pokemon/1`) contain relationships between entities, which could be added as a future enhancement.

## Merge Strategy

All Pokemon reference data uses **merge strategy** with **merge deduplication**:

```python
@phlo_ingestion(
    table_name="pokemon",
    unique_key="name",
    merge_strategy="merge",     # Upsert mode
    freshness_hours=(168, 336), # 1 week warn, 2 weeks fail
)
```

### Why Merge Strategy?

**1. Idempotent Pipeline Runs**
- Re-running a partition safely updates existing data
- No duplicates from overlapping queries
- Pipeline failures can be retried without cleanup

**2. Reference Data Updates**
- New Pokemon can be added (rare but happens)
- Metadata can be corrected (typos, translations)
- Merge strategy ensures latest data wins

**3. Operational Simplicity**
- No manual deduplication needed
- Safe for scheduled refreshes
- Consistent behavior across all entities

### Freshness Monitoring

Different update schedules reflect data stability:

- **Pokemon**: Weekly refresh (new Pokemon occasionally added)
- **Types/Abilities/Moves/Generations**: Monthly (very stable)

Freshness checks alert on stale data:
- Warning: 1 week (Pokemon) or 30 days (others)
- Failure: 2 weeks (Pokemon) or 60 days (others)

## Example Queries

### 1. Pokemon by Generation

```sql
SELECT
  generation,
  region,
  pokemon_count,
  pct_of_total
FROM gold.fct_pokemon_by_generation
ORDER BY generation;
```

**Sample Output**:
```
generation | region  | pokemon_count | pct_of_total
-----------|---------|---------------|-------------
1          | Kanto   | 151           | 14.73
2          | Johto   | 100           | 9.76
3          | Hoenn   | 135           | 13.17
...
```

### 2. Find Kanto Pokemon

```sql
SELECT
  pokemon_id,
  pokemon_name,
  generation,
  region
FROM gold.dim_pokemon
WHERE region = 'Kanto'
ORDER BY pokemon_id
LIMIT 10;
```

**Sample Output**:
```
pokemon_id | pokemon_name | generation | region
-----------|--------------|------------|-------
1          | bulbasaur    | 1          | Kanto
2          | ivysaur      | 1          | Kanto
3          | venusaur     | 1          | Kanto
...
```

### 3. Count Pokemon by Type

```sql
-- Note: This requires ingesting detailed Pokemon data (future enhancement)
-- For now, this shows the types dimension:

SELECT
  type_id,
  type_name,
  type_display_name
FROM gold.dim_types
ORDER BY type_id;
```

**Sample Output**:
```
type_id | type_name | type_display_name
--------|-----------|------------------
1       | normal    | Normal
2       | fighting  | Fighting
3       | flying    | Flying
10      | fire      | Fire
11      | water     | Water
12      | grass     | Grass
...
```

### 4. Pokemon ID Ranges by Generation

```sql
SELECT
  generation,
  region,
  first_pokemon_id,
  last_pokemon_id,
  last_pokemon_id - first_pokemon_id + 1 AS range_size
FROM gold.fct_pokemon_by_generation
ORDER BY generation;
```

### 5. Recent Ingestion Timestamps

```sql
SELECT
  pokemon_name,
  loaded_at
FROM gold.dim_pokemon
ORDER BY loaded_at DESC
LIMIT 10;
```

## CLI Commands

### Core Operations

```bash
phlo services start          # Start infrastructure
phlo services stop           # Stop infrastructure
phlo services status         # Check health
phlo materialize <asset>     # Materialize asset
phlo test                    # Run test suite
```

### Asset Materialization

```bash
# Single asset
phlo materialize pokemon --partition 2024-01-15

# All Pokemon entities
phlo materialize --select "group:pokemon"

# Via Dagster UI
# Navigate to Assets > select asset > Materialize
```

### Query Data

```bash
# Connect to Trino CLI
docker exec -it pokemon-lakehouse-trino-1 trino

# Run queries
SELECT * FROM gold.dim_pokemon LIMIT 10;
SELECT * FROM gold.fct_pokemon_by_generation;
```

### Monitoring

```bash
# View logs
phlo logs --asset pokemon
phlo logs --level ERROR --since 1h

# Check lineage
phlo lineage show pokemon --downstream
```

## Minimal Configuration

This example demonstrates phlo's **zero-config philosophy**. The entire `phlo.yaml`:

```yaml
name: pokemon-lakehouse
description: "Pokemon data lakehouse powered by PokeAPI"

services:
  superset:
    enabled: false  # Keep stack minimal
```

That's it! No database credentials, no S3 buckets, no complex service definitions. Phlo handles all infrastructure automatically.

## Real-World Applicability

This Pokemon example teaches patterns applicable to:

**Product Reference Data**
- E-commerce: Product catalogs, categories, brands
- SaaS: Feature flags, plans, pricing tiers
- Healthcare: Drug formularies, procedure codes

**Taxonomies & Classifications**
- Content: Tags, categories, genres
- Finance: Account types, transaction categories
- HR: Job titles, departments, locations

**Slowly Changing Dimensions**
- Customer master data
- Supplier/vendor information
- Configuration management databases (CMDB)

**Public API Integration**
- Any REST API with list endpoints
- Reference data from external services
- Third-party data enrichment

## Learning Path

1. **Start here**: Understand the generic API helper pattern in `workflows/ingestion/helpers.py`
2. **Read the schemas**: See how Pandera validates API responses in `workflows/schemas/pokemon.py`
3. **Follow the flow**: Trace data from ingestion → silver → gold
4. **Run the ingestion**: `phlo materialize --select "group:pokemon"`
5. **Query the results**: Use Trino to explore the gold layer
6. **Add your own entity**: Try adding `pokemon_items` or `pokemon_locations`

## Next Steps

**Extend with Detailed Data**
- Ingest detail endpoints (e.g., `/pokemon/1`) for full Pokemon stats
- Add many-to-many relationships (Pokemon → Types, Abilities, Moves)
- Build fact tables for Pokemon stats, evolution chains

**Add Analytics**
- Average stats by generation
- Type effectiveness matrix
- Evolution chain analysis
- Move power distribution

**Build Dashboards**
- Enable Superset in `phlo.yaml`
- Create Pokemon visualizations
- Generation comparison charts

## Documentation

- [Phlo Documentation](https://github.com/iamgp/phlo)
- [PokeAPI Documentation](https://pokeapi.co/docs/v2)
- [DLT REST API Source](https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api)

## Why This Example Matters

Most data engineering tutorials use complex domains or synthetic data. Pokemon provides:

✅ Familiar, verifiable data everyone understands
✅ Real public API with consistent patterns
✅ Clean dimensional modeling examples
✅ Minimal configuration overhead
✅ Reusable patterns for any REST API

Use this as a template for your reference data lakehouses.
