# github-stats

Phlo data workflows for github-stats.

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Create your first workflow:**
   ```bash
   phlo create-workflow
   ```

3. **Start Dagster UI:**
   ```bash
   phlo dev
   ```

4. **Access the UI:**
   Open http://localhost:3000 in your browser

## Project Structure

```
github-stats/
├── workflows/          # Your workflow definitions
│   ├── ingestion/     # Data ingestion workflows
│   └── schemas/       # Pandera validation schemas
├── transforms/dbt/    # dbt transformation models
└── tests/            # Workflow tests
```

## Documentation

- [Phlo Documentation](https://github.com/iamgp/phlo)
- [Workflow Development Guide](https://github.com/iamgp/phlo/blob/main/docs/guides/workflow-development.md)

## Commands

- `phlo dev` - Start Dagster development server
- `phlo create-workflow` - Scaffold new workflow
- `phlo test` - Run tests
