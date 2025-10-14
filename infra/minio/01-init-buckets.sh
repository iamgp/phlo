#!/bin/sh
set -e

# Wait for MinIO to be ready
sleep 5

# Configure mc client
mc alias set myminio http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Create lake bucket if it doesn't exist
mc mb --ignore-existing myminio/lake

echo "MinIO buckets initialized"
