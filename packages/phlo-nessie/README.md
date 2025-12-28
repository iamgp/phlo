# phlo-nessie

Nessie Git-like catalog for Phlo.

## Description

Nessie provides Git-like version control for Iceberg tables. Enables branching, merging, and time travel for the data lakehouse.

## Installation

```bash
pip install phlo-nessie
# or
phlo plugin install nessie
```

## Configuration

| Variable               | Default   | Description                |
| ---------------------- | --------- | -------------------------- |
| `NESSIE_PORT`          | `19120`   | Nessie API port            |
| `NESSIE_VERSION`       | `0.106.0` | Nessie version             |
| `NESSIE_OIDC_ENABLED`  | `false`   | Enable OIDC authentication |
| `NESSIE_AUTHZ_ENABLED` | `false`   | Enable authorization       |

## Auto-Configuration

Works out-of-the-box with sensible defaults:

| Feature              | How It Works                                               |
| -------------------- | ---------------------------------------------------------- |
| **Branch Init**      | Auto-creates `main` and `dev` branches via post_start hook |
| **Metrics Labels**   | Exposes Quarkus metrics at `/q/metrics`                    |
| **Postgres Storage** | Uses PostgreSQL for version store (default backend)        |

### Post-Start Hook

```yaml
hooks:
  post_start:
    - name: init-branches
      command: python -m phlo_nessie.hooks init-branches
```

## Usage

```bash
# Start Nessie
phlo services start --service nessie

# List branches
phlo nessie branches

# Create a new branch
phlo nessie branch create feature/my-feature
```

## Endpoints

- **API**: `http://localhost:19120/api/v1`
- **Iceberg REST**: `http://localhost:19120/iceberg`

## Entry Points

- `phlo.plugins.services` - Provides `NessieServicePlugin`
- `phlo.plugins.cli` - Provides Nessie CLI commands
