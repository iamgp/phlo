#!/bin/bash
set -e

# Script to recreate Airbyte connections after Docker restart
# This ensures all connection IDs in .env are valid

echo "Setting up Airbyte connections..."

# Get workspace ID
WORKSPACE_RESPONSE=$(docker exec airbyte-server curl -s http://localhost:8001/api/v1/workspaces/list -H "Content-Type: application/json" -d '{}')
WORKSPACE_ID=$(echo "$WORKSPACE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['workspaces'][0]['workspaceId'])")
echo "Workspace ID: $WORKSPACE_ID"

# Create Nightscout source
echo "Creating Nightscout source..."
SOURCE_RESPONSE=$(docker exec airbyte-server curl -s -X POST http://localhost:8001/api/v1/sources/create -H "Content-Type: application/json" -d "{
  \"sourceDefinitionId\": \"778daa7c-feaf-4db6-96f3-70fd645acc77\",
  \"connectionConfiguration\": {
    \"url\": \"https://gwp-diabetes.fly.dev/api/v1/entries.json?count=10000\",
    \"format\": \"json\",
    \"provider\": {
      \"storage\": \"HTTPS\"
    },
    \"dataset_name\": \"nightscout_entries\"
  },
  \"workspaceId\": \"$WORKSPACE_ID\",
  \"name\": \"Nightscout CGM Data\"
}")
SOURCE_ID=$(echo "$SOURCE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['sourceId'])")
echo "Source ID: $SOURCE_ID"

# Create destination
echo "Creating Local JSON destination..."
DEST_RESPONSE=$(docker exec airbyte-server curl -s -X POST http://localhost:8001/api/v1/destinations/create -H "Content-Type: application/json" -d "{
  \"destinationDefinitionId\": \"a625d593-bba5-4a1c-a53d-2d246268a816\",
  \"connectionConfiguration\": {
    \"destination_path\": \"/data/lake/raw/nightscout\"
  },
  \"workspaceId\": \"$WORKSPACE_ID\",
  \"name\": \"Local JSON - Nightscout\"
}")
DEST_ID=$(echo "$DEST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['destinationId'])")
echo "Destination ID: $DEST_ID"

# Create connection
echo "Creating connection..."
CONN_RESPONSE=$(docker exec airbyte-server curl -s -X POST http://localhost:8001/api/v1/web_backend/connections/create -H "Content-Type: application/json" -d "{
  \"sourceId\": \"$SOURCE_ID\",
  \"destinationId\": \"$DEST_ID\",
  \"name\": \"Nightscout to Local JSON\",
  \"namespaceDefinition\": \"destination\",
  \"namespaceFormat\": \"\${SOURCE_NAMESPACE}\",
  \"status\": \"active\",
  \"scheduleType\": \"manual\",
  \"syncCatalog\": {
    \"streams\": []
  }
}")
CONNECTION_ID=$(echo "$CONN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['connectionId'])")
echo "Connection ID: $CONNECTION_ID"

# Discover schema and enable stream
echo "Discovering schema..."
docker exec airbyte-server curl -s -X POST http://localhost:8001/api/v1/sources/discover_schema -H "Content-Type: application/json" -d "{
  \"sourceId\": \"$SOURCE_ID\"
}" > /tmp/airbyte_catalog.json

python3 << 'EOF'
import json
with open('/tmp/airbyte_catalog.json') as f:
    data = json.load(f)

stream = data['catalog']['streams'][0]
stream['config'] = {
    'syncMode': 'full_refresh',
    'destinationSyncMode': 'overwrite',
    'selected': True
}

update_payload = {
    'connectionId': '${CONNECTION_ID}',
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
EOF

# Replace the placeholder in the Python-generated file
sed -i.bak "s/\${CONNECTION_ID}/$CONNECTION_ID/g" /tmp/update_payload.json

echo "Enabling stream..."
docker cp /tmp/update_payload.json airbyte-server:/tmp/
docker exec airbyte-server curl -s -X POST http://localhost:8001/api/v1/web_backend/connections/update -H "Content-Type: application/json" --data-binary @/tmp/update_payload.json > /dev/null

echo ""
echo "✓ Setup complete!"
echo ""
echo "Update your .env file with:"
echo "AIRBYTE_NIGHTSCOUT_CONNECTION_ID=$CONNECTION_ID"
echo ""
echo "Then restart Dagster:"
echo "docker restart dagster-web dagster-daemon"
