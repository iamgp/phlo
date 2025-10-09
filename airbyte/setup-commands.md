# Airbyte Setup Commands

Commands used to configure Nightscout ingestion via Airbyte API.

## Prerequisites

- Airbyte running at localhost:8001
- Workspace ID: `d064f4da-c226-47af-9612-763f6f855a33`

## 1. Create Nightscout Source

Using the File connector (supports HTTPS URLs):

```bash
curl -X POST http://localhost:8001/api/v1/sources/create \
  -H "Content-Type: application/json" \
  -d '{
  "sourceDefinitionId": "778daa7c-feaf-4db6-96f3-70fd645acc77",
  "connectionConfiguration": {
    "url": "https://gwp-diabetes.fly.dev/api/v1/entries.json?count=10000",
    "format": "json",
    "provider": {
      "storage": "HTTPS"
    },
    "dataset_name": "nightscout_entries"
  },
  "workspaceId": "d064f4da-c226-47af-9612-763f6f855a33",
  "name": "Nightscout CGM Data"
}'
```

**Response**: Source ID: `1b7916b7-abb5-4feb-b644-536ec477e929`

## 2. Create Local JSON Destination

```bash
curl -X POST http://localhost:8001/api/v1/destinations/create \
  -H "Content-Type: application/json" \
  -d '{
  "destinationDefinitionId": "a625d593-bba5-4a1c-a53d-2d246268a816",
  "connectionConfiguration": {
    "destination_path": "/data/lake/raw/nightscout"
  },
  "workspaceId": "d064f4da-c226-47af-9612-763f6f855a33",
  "name": "Local JSON - Nightscout"
}'
```

**Response**: Destination ID: `9cd376df-b004-467e-8607-9b0fb89da01c`

## 3. Discover Schema

```bash
curl -X POST http://localhost:8001/api/v1/sources/discover_schema \
  -H "Content-Type: application/json" \
  -d '{
  "sourceId": "1b7916b7-abb5-4feb-b644-536ec477e929"
}'
```

## 4. Create Connection

```bash
curl -X POST http://localhost:8001/api/v1/web_backend/connections/create \
  -H "Content-Type: application/json" \
  -d '{
  "sourceId": "1b7916b7-abb5-4feb-b644-536ec477e929",
  "destinationId": "9cd376df-b004-467e-8607-9b0fb89da01c",
  "name": "Nightscout to Local JSON",
  "namespaceDefinition": "destination",
  "namespaceFormat": "${SOURCE_NAMESPACE}",
  "status": "active",
  "scheduleType": "manual",
  "syncCatalog": {
    "streams": []
  }
}'
```

**Response**: Connection ID: `015ab542-1a18-4156-a44a-861b17f8d03c`

## 5. Enable Stream in Connection

First, discover the schema and save it to build the proper update payload:

```bash
# Discover schema and build update payload
curl -X POST http://localhost:8001/api/v1/sources/discover_schema \
  -H "Content-Type: application/json" \
  -d '{
  "sourceId": "1b7916b7-abb5-4feb-b644-536ec477e929"
}' > /tmp/catalog.json

# Build update payload with full schema
python3 -c "
import json
with open('/tmp/catalog.json') as f:
    data = json.load(f)

stream = data['catalog']['streams'][0]
stream['config'] = {
    'syncMode': 'full_refresh',
    'destinationSyncMode': 'overwrite',
    'selected': True
}

update_payload = {
    'connectionId': '015ab542-1a18-4156-a44a-861b17f8d03c',
    'name': 'Nightscout to Local JSON',
    'namespaceDefinition': 'destination',
    'status': 'active',
    'scheduleType': 'manual',
    'syncCatalog': {
        'streams': [stream]
    }
}

with open('/tmp/update_payload.json', 'w') as f:
    json.dump(update_payload, f)
"

# Update connection with enabled stream
curl -X POST http://localhost:8001/api/v1/web_backend/connections/update \
  -H "Content-Type: application/json" \
  -d @/tmp/update_payload.json
```

## 6. Trigger Sync

```bash
curl -X POST http://localhost:8001/api/v1/connections/sync \
  -H "Content-Type: application/json" \
  -d '{
  "connectionId": "015ab542-1a18-4156-a44a-861b17f8d03c"
}'
```

**Response**: Job ID: `3`, Status: `running`

## 7. Check Sync Status

```bash
curl -X POST http://localhost:8001/api/v1/jobs/get \
  -H "Content-Type: application/json" \
  -d '{
  "id": 3
}'
```

## Key Connector Definition IDs

- File (CSV, JSON, Excel, Feather, Parquet): `778daa7c-feaf-4db6-96f3-70fd645acc77`
- Local JSON: `a625d593-bba5-4a1c-a53d-2d246268a816`

## Output

Data is written to: `data/airbyte/workspace/data/lake/raw/nightscout/_airbyte_raw_nightscout_entries.jsonl`

## Notes

- The File connector supports HTTPS URLs for remote JSON files
- Schedule type is set to "manual" - syncs run on demand
- Streams must be enabled with proper sync mode after connection creation
- The update payload requires the full JSON schema from schema discovery
- Local JSON destination writes relative to `/local` mount (workspace directory)
