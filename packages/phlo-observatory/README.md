# phlo-observatory

Observatory web UI service plugin for Phlo.

## Description

Web-based data exploration and management interface for Phlo. Provides:

- Data browser with table preview
- Branch management (Nessie)
- Asset lineage visualization
- Quality check monitoring
- Plugin management

## Installation

```bash
pip install phlo-observatory
# or
phlo plugin install observatory
```

## Configuration

| Variable           | Default | Description |
| ------------------ | ------- | ----------- |
| `OBSERVATORY_PORT` | `5173`  | Web UI port |

## Usage

```bash
phlo services start --service observatory
```

## Endpoints

- **Web UI**: `http://localhost:5173`

## Development

```bash
cd packages/phlo-observatory/src/phlo_observatory
npm install
npm run dev
```
