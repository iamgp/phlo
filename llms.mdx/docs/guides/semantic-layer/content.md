# Semantic Layer (/docs/guides/semantic-layer)



SemanticModel [#semanticmodel]

**Module:** `phlo.plugins.semantic`

Frozen dataclass representing a single semantic model.

```python
@dataclass(frozen=True)
class SemanticModel:
    name: str                              # unique model identifier
    description: str | None = None         # human-readable description
    sql: str | None = None                 # SQL definition or reference
    metadata: dict[str, Any] = field(...)  # arbitrary extra attributes
```

`metadata` can carry engine-specific details — column definitions, freshness policies,
access controls, etc.

SemanticLayerProvider [#semanticlayerprovider]

ABC that exposes semantic models from a backend.

```python
class SemanticLayerProvider(ABC):
    @abstractmethod
    def list_models(self) -> Iterable[SemanticModel]:
        """Return all semantic models."""

    @abstractmethod
    def get_model(self, name: str) -> SemanticModel | None:
        """Return a model by name, or None."""
```

Example: implementing a provider [#example-implementing-a-provider]

```python
from phlo.plugins.semantic import SemanticLayerProvider, SemanticModel

class TrinoSemanticProvider(SemanticLayerProvider):
    def __init__(self, catalog: str, schema: str):
        self.catalog = catalog
        self.schema = schema
        self._models: dict[str, SemanticModel] = {}

    def list_models(self):
        return list(self._models.values())

    def get_model(self, name):
        return self._models.get(name)

    def register(self, model: SemanticModel):
        self._models[model.name] = model
```

Plugin system integration [#plugin-system-integration]

Semantic layer providers are discovered through the standard Phlo plugin entry point
system. A package registers its provider under the appropriate entry point group and
the provider is loaded at runtime alongside other plugins.

Providers can be combined — for example, a dbt package can publish `SemanticModel`
entries from its manifest while a Trino package exposes live views. Consumers call
`list_models()` on whichever provider is active without knowing the underlying engine.

See also [#see-also]

* [Plugin Development](plugin-development.md) — entry point registration
* [Capability Primitives](capability-primitives.md) — asset and resource specs
* [Data Modeling](data-modeling.md) — dbt-based transformation models
