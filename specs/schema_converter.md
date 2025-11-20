# PRD: Pandera to PyIceberg Schema Converter

## Problem Statement

Currently, Cascade requires users to define schemas twice:

1. **Pandera schemas** (`schemas/*.py`) for data validation at ingestion
2. **PyIceberg schemas** (`iceberg/schema.py`) for Iceberg table creation

This violates DRY principles and creates maintenance burden. When adding a new field, users must update two schema definitions with identical information but different syntax.

### Current State

```python
# schemas/glucose.py - Pandera validation schema
class RawGlucoseEntries(DataFrameModel):
    _id: str = Field(nullable=False, unique=True)
    sgv: int = Field(ge=1, le=1000, nullable=False)
    date_string: datetime = Field(nullable=False)
    # ... 10+ more fields

# iceberg/schema.py - PyIceberg table schema (duplicated!)
NIGHTSCOUT_ENTRIES_SCHEMA = Schema(
    NestedField(1, "_id", StringType(), required=False, doc="Unique ID"),
    NestedField(2, "sgv", LongType(), required=False, doc="Glucose value"),
    NestedField(3, "date_string", TimestamptzType(), required=False),
    # ... same 10+ fields, different syntax
)
```

**Problems:**
- Schema drift when one is updated but not the other
- 2x the code to maintain
- Inconsistent field documentation
- Error-prone manual type mapping
- Cognitive overhead deciding which schema to trust

## Goals

### Primary Goal
Eliminate schema duplication by auto-generating PyIceberg schemas from Pandera schemas.

### Secondary Goals
1. Maintain data validation at ingestion (Pandera)
2. Preserve Iceberg table creation functionality
3. Zero breaking changes for existing assets
4. Reduce schema maintenance burden by 50%
5. Ensure type mapping correctness

### Non-Goals
- Generating Pandera from PyIceberg (wrong direction - Pandera is more expressive)
- Supporting 100% of PyIceberg features (partitioning, sorting handled separately)
- Bidirectional schema sync
- Runtime schema evolution/migration

## Solution

### Architecture

```
┌─────────────────┐
│ Pandera Schema  │  Single source of truth
│ (User defines)  │  - Data types
└────────┬────────┘  - Validation rules
         │           - Field descriptions
         ↓
┌─────────────────┐
│   Converter     │  pandera_to_iceberg()
│                 │  - Type mapping
└────────┬────────┘  - Field ordering
         │           - Metadata extraction
         ↓
┌─────────────────┐
│ PyIceberg Schema│  Auto-generated
│ (Generated)     │  - Used by ensure_table()
└─────────────────┘  - Never manually edited
```

### Implementation

**Location:** `src/cascade/schemas/converter.py`

**Core Function:**
```python
def pandera_to_iceberg(
    pandera_schema: type[DataFrameModel],
    start_field_id: int = 1,
    required_fields: set[str] | None = None,
) -> Schema:
    """
    Convert Pandera DataFrameModel to PyIceberg Schema.

    Args:
        pandera_schema: Pandera DataFrameModel class
        start_field_id: Starting field ID for PyIceberg (default: 1)
        required_fields: Override required fields (default: use Pandera nullable)

    Returns:
        PyIceberg Schema object

    Raises:
        SchemaConversionError: If type cannot be mapped
    """
```

### Type Mapping

| Pandera Type | PyIceberg Type | Notes |
|--------------|----------------|-------|
| `str` | `StringType()` | UTF-8 strings |
| `int` | `LongType()` | 64-bit integers |
| `float` | `DoubleType()` | 64-bit floats |
| `bool` | `BooleanType()` | Boolean values |
| `datetime` | `TimestamptzType()` | Timezone-aware timestamps |
| `date` | `DateType()` | Date only |
| `bytes` | `BinaryType()` | Binary data |
| `Decimal` | `DecimalType(precision, scale)` | Extract from Pandera metadata |

**Complex Types:**
- JSON strings (Pandera `str` with metadata) → `StringType()` with doc note
- Lists/Arrays → Not supported in initial version (raise clear error)
- Nested objects → Not supported in initial version (raise clear error)

### Metadata Extraction

```python
# Pandera Field description → PyIceberg NestedField doc
_id: str = Field(nullable=False, description="Unique identifier")
# Becomes:
NestedField(1, "_id", StringType(), required=True, doc="Unique identifier")

# Pandera nullable → PyIceberg required
sgv: int = Field(nullable=False)  # required=True in Iceberg
device: str = Field(nullable=True)  # required=False in Iceberg
```

### Field Ordering

PyIceberg requires sequential field IDs. Strategy:
1. Iterate through Pandera schema fields in definition order
2. Assign IDs sequentially starting from `start_field_id`
3. Reserve high IDs (100+) for DLT metadata fields

**Convention:**
- Data fields: IDs 1-99
- DLT metadata: IDs 100+ (`_dlt_load_id`, `_dlt_id`)

### Integration with @cascade_ingestion

**Before (manual):**
```python
@cascade_ingestion(
    table_name="github_user_events",
    unique_key="id",
    iceberg_schema=GITHUB_USER_EVENTS_SCHEMA,  # Manual definition
    validation_schema=RawGitHubUserEvents,
    group="github",
)
```

**After (auto-generated):**
```python
@cascade_ingestion(
    table_name="github_user_events",
    unique_key="id",
    validation_schema=RawGitHubUserEvents,  # Only this required!
    group="github",
)
```

Decorator automatically:
1. Calls `pandera_to_iceberg(RawGitHubUserEvents)`
2. Generates PyIceberg schema
3. Uses it for `ensure_table()`

**Backward compatibility:** Keep `iceberg_schema` parameter optional. If provided, use it; otherwise auto-generate.

## Technical Design

### Module Structure

```
src/cascade/schemas/
├── __init__.py
├── converter.py          # NEW: pandera_to_iceberg()
├── glucose.py           # Pandera schemas only
├── github.py            # Pandera schemas only
└── registry.py          # TableConfig (internal)

src/cascade/iceberg/
├── schema.py            # DELETE: Manual PyIceberg schemas
└── tables.py            # Keep: Table operations
```

### Error Handling

```python
class SchemaConversionError(Exception):
    """Raised when Pandera schema cannot be converted to PyIceberg."""
    pass

# Examples:
- Unsupported type: "Cannot convert Pandera type 'List[str]' to PyIceberg"
- Missing metadata: "Decimal field 'price' missing precision/scale"
- Invalid field name: "Field name '_reserved' conflicts with PyIceberg reserved words"
```

### Testing Strategy

**Unit tests** (`tests/test_schema_converter.py`):
```python
def test_basic_types():
    """Test str, int, float, bool, datetime conversion."""

def test_nullable_to_required():
    """Test nullable=False → required=True mapping."""

def test_field_descriptions():
    """Test description extraction to doc parameter."""

def test_field_ordering():
    """Test sequential field ID assignment."""

def test_unsupported_types():
    """Test clear error for List, Dict, nested types."""

def test_dlt_metadata_fields():
    """Test DLT fields get IDs 100+."""
```

**Integration tests** (`tests/test_ingestion_with_converter.py`):
```python
def test_decorator_auto_generates_schema():
    """Test @cascade_ingestion auto-generates from Pandera."""

def test_ensure_table_with_generated_schema():
    """Test generated schema works with Iceberg table creation."""

def test_backward_compatibility():
    """Test explicit iceberg_schema still works."""
```

## Migration Plan

### Phase 1: Add Converter (Non-Breaking)
1. Implement `pandera_to_iceberg()` in new module
2. Add comprehensive tests
3. Update decorator to support auto-generation
4. Keep `iceberg_schema` parameter optional

**Status:** All existing code continues to work

### Phase 2: Migrate Assets (One-by-one)
1. Update `nightscout/glucose.py` - remove `iceberg_schema` parameter
2. Update `github/events.py` - remove `iceberg_schema` parameter
3. Update `github/repos.py` - remove `iceberg_schema` parameter
4. Test each migration individually

**Status:** Assets gradually adopt auto-generation

### Phase 3: Deprecate Manual Schemas
1. Mark `iceberg_schema` parameter as deprecated
2. Delete unused schemas from `iceberg/schema.py`
3. Update documentation to only show auto-generation
4. Add deprecation warning if `iceberg_schema` is used

**Timeline:** 2 sprints

### Phase 4: Remove Manual Schemas (Breaking)
1. Remove `iceberg_schema` parameter entirely
2. Delete `iceberg/schema.py` file
3. Update all documentation

**Timeline:** Major version bump required

## Success Metrics

### Quantitative
- Schema definition LOC reduced by 50%
- Zero schema drift bugs in ingestion
- 100% test coverage for type mapping
- All 3 existing assets migrated successfully

### Qualitative
- New assets only require Pandera schema definition
- Schema maintenance time reduced
- Improved developer experience (single source of truth)
- Clear error messages for unsupported types

## Open Questions

### Q: What about schema evolution?
**A:** Iceberg handles schema evolution automatically. When parquet schema differs from table schema, Iceberg can add columns automatically (if configured). This is orthogonal to our converter.

### Q: What about partition specs?
**A:** Partition specs stay separate parameter in decorator. They're operational, not schema-related:
```python
@cascade_ingestion(
    validation_schema=MySchema,
    partition_spec=[("date", "day")],  # Separate concern
)
```

### Q: What about complex nested types?
**A:** Phase 1: Not supported, clear error message. Phase 2: Consider if needed based on real use cases. Most raw data is flat or JSON strings.

### Q: Performance impact of schema generation?
**A:** Negligible. Schema conversion happens once at decorator application time (import time), not at runtime. Generated schema is cached in TableConfig.

### Q: What if Pandera schema has validation rules PyIceberg can't express?
**A:** That's fine! Pandera validation happens at runtime on data. PyIceberg schema is just type metadata for table structure. The validation rules (ge=1, le=1000) don't need to be in PyIceberg.

## Dependencies

**Required:**
- Existing: `pandera`, `pyiceberg`
- No new dependencies

**Compatibility:**
- Python 3.11+
- Pandera 0.17+
- PyIceberg 0.5+

## Documentation Updates

**Update:**
- `src/cascade/defs/ingestion/README.md` - Remove `iceberg_schema` from examples
- New: `docs/schemas.md` - Explain single source of truth approach
- New: `docs/migration_guide.md` - Guide for migrating from manual schemas

**Code examples:**
- Show only Pandera schema definition
- Explain auto-generation in decorator docs
- Add troubleshooting section for conversion errors

## Future Enhancements

**Phase 2 (Optional):**
1. Support for Pandera `List[T]` → PyIceberg `ListType`
2. Support for nested structures via Pandera schema composition
3. Schema versioning/migration helpers
4. Visual schema diff tool
5. Automatic schema documentation generation

**Phase 3 (Optional):**
1. Reverse generation: PyIceberg → Pandera (for external tables)
2. Schema registry integration (Confluent, etc.)
3. Cross-environment schema validation

## Appendix: Example Conversions

### Simple Schema
```python
# Input: Pandera
class SimpleData(DataFrameModel):
    id: str = Field(nullable=False, unique=True)
    value: int = Field(ge=0)
    created_at: datetime

# Output: PyIceberg
Schema(
    NestedField(1, "id", StringType(), required=True, doc=""),
    NestedField(2, "value", LongType(), required=False, doc=""),
    NestedField(3, "created_at", TimestamptzType(), required=False, doc=""),
)
```

### With Descriptions
```python
# Input: Pandera
class DocumentedData(DataFrameModel):
    user_id: str = Field(nullable=False, description="Unique user identifier")
    score: int = Field(ge=0, le=100, description="User score (0-100)")

# Output: PyIceberg
Schema(
    NestedField(1, "user_id", StringType(), required=True, doc="Unique user identifier"),
    NestedField(2, "score", LongType(), required=False, doc="User score (0-100)"),
)
```

### With DLT Metadata
```python
# Input: Pandera (with DLT fields)
class WithDLT(DataFrameModel):
    id: str
    value: int
    _dlt_load_id: str
    _dlt_id: str

# Output: PyIceberg
Schema(
    NestedField(1, "id", StringType(), required=False, doc=""),
    NestedField(2, "value", LongType(), required=False, doc=""),
    NestedField(100, "_dlt_load_id", StringType(), required=True, doc="DLT load identifier"),
    NestedField(101, "_dlt_id", StringType(), required=True, doc="DLT record identifier"),
)
```
