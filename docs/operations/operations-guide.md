# Operations Guide

Production operations guide for running and maintaining Phlo.

## Daily Operations

### Monitoring Services

Check all services are running:

```bash
phlo services status
```

Expected output:
```
SERVICE              STATUS    PORTS
postgres             running   10000
minio                running   10001-10002
nessie               running   10003
trino                running   10005
dagster-webserver    running   10006
dagster-daemon       running
```

### Viewing Logs

Monitor service logs:

```bash
# All services
phlo services logs -f

# Specific service
phlo services logs -f dagster-webserver

# Last 100 lines
phlo services logs --tail 100 dagster-daemon
```

### Asset Status

Check asset health and freshness:

```bash
# All assets
phlo status

# Only stale assets
phlo status --stale

# Only failed assets
phlo status --failed

# Specific group
phlo status --group nightscout
```

### Manual Materialization

Trigger asset runs manually:

```bash
# Single asset
phlo materialize dlt_glucose_entries

# With downstream
phlo materialize dlt_glucose_entries+

# Specific partition
phlo materialize dlt_glucose_entries --partition 2025-01-15

# By tag
phlo materialize --select "tag:nightscout"
```

## Backup and Recovery

### Database Backups

**PostgreSQL**:

```bash
# Backup
docker exec phlo-postgres-1 pg_dump -U postgres cascade > backup.sql

# Backup with compression
docker exec phlo-postgres-1 pg_dump -U postgres cascade | gzip > backup.sql.gz

# Restore
cat backup.sql | docker exec -i phlo-postgres-1 psql -U postgres cascade

# Restore from compressed
gunzip -c backup.sql.gz | docker exec -i phlo-postgres-1 psql -U postgres cascade
```

**Automated backups**:

```bash
# Add to crontab
0 2 * * * /path/to/backup-postgres.sh
```

```bash
#!/bin/bash
# backup-postgres.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
mkdir -p $BACKUP_DIR
docker exec phlo-postgres-1 pg_dump -U postgres cascade | \
  gzip > $BACKUP_DIR/cascade_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Object Storage Backups

**MinIO/S3**:

```bash
# Install mc (MinIO client)
brew install minio/stable/mc

# Configure
mc alias set local http://localhost:10001 minioadmin minioadmin

# Backup bucket
mc mirror local/lake /backups/minio/lake

# Restore
mc mirror /backups/minio/lake local/lake
```

**Automated S3 sync**:

```bash
# Using AWS CLI or rclone
rclone sync /backups/minio/lake s3://backup-bucket/lake
```

### Nessie Catalog Backups

Nessie state is stored in PostgreSQL, so backing up Postgres includes catalog metadata.

**Export specific branches**:

```bash
# List branches
phlo branch list > branches_backup.txt

# Export branch commits
curl http://localhost:10003/api/v2/trees/main > main_branch.json
```

## Branch Management

### Creating Branches

```bash
# Development branch
phlo branch create dev

# Feature branch from specific ref
phlo branch create feature-xyz --from main

# With description
phlo branch create experiment --description "Testing new ingestion"
```

### Merging Branches

```bash
# Merge dev to main
phlo branch merge dev main

# Force merge commit
phlo branch merge dev main --no-ff
```

### Cleanup Old Branches

```bash
# List all branches
phlo branch list

# Delete specific branch
phlo branch delete old-feature

# Automated cleanup (configure in .env)
BRANCH_CLEANUP_ENABLED=true
BRANCH_RETENTION_DAYS=7
BRANCH_RETENTION_DAYS_FAILED=2
```

**Manual cleanup script**:

```python
from phlo_nessie.resource import BranchManagerResource
from datetime import datetime, timedelta

branch_manager = BranchManagerResource()

# Get all pipeline branches
branches = branch_manager.get_all_pipeline_branches()

retention_days = 7
cutoff_date = datetime.now() - timedelta(days=retention_days)

for branch in branches:
    if branch.created_at < cutoff_date:
        print(f"Deleting old branch: {branch.name}")
        branch_manager.cleanup_branch(branch.name)
```

## Performance Optimization

### Trino Query Optimization

**Enable query profiling**:

```sql
-- In Trino CLI
EXPLAIN ANALYZE SELECT * FROM bronze.events WHERE date = '2025-01-15';
```

**Partition pruning**:

```sql
-- Good: uses partition pruning
SELECT * FROM bronze.events WHERE partition_date = '2025-01-15';

-- Bad: full table scan
SELECT * FROM bronze.events WHERE timestamp > '2025-01-15';
```

**Table statistics**:

```sql
-- Analyze table
ANALYZE iceberg_dev.bronze.events;

-- Show stats
SHOW STATS FOR bronze.events;
```

### Iceberg Maintenance

**Optimize files**:

```python
from phlo_iceberg import get_iceberg_table

table = get_iceberg_table("bronze.events")

# Compact small files
table.optimize.compact()

# Expire old snapshots
table.expire_snapshots(older_than=30)  # days
```

**Automated maintenance**:

```python
# workflows/maintenance/iceberg.py
from dagster import asset, schedule

@asset
def optimize_iceberg_tables():
    tables = ["bronze.events", "silver.events_cleaned"]
    for table_name in tables:
        table = get_iceberg_table(table_name)
        table.optimize.compact()
        table.expire_snapshots(older_than=30)

@schedule(cron_schedule="0 2 * * 0", job_name="weekly_maintenance")
def weekly_iceberg_maintenance():
    return RunRequest()
```

### Dagster Performance

**Use multiprocess executor** for production:

```bash
# .env
DAGSTER_EXECUTOR=multiprocess
```

**Configure resource limits**:

```python
# dagster.yaml
execution:
  multiprocess:
    max_concurrent: 4
    retries:
      enabled: true
      max_retries: 3
```

## Scaling

### Horizontal Scaling

**Trino workers**:

Add workers in `docker-compose.yml`:

```yaml
services:
  trino-worker-1:
    image: trinodb/trino:461
    environment:
      - TRINO_DISCOVERY_URI=http://trino:10005
    depends_on:
      - trino

  trino-worker-2:
    image: trinodb/trino:461
    environment:
      - TRINO_DISCOVERY_URI=http://trino:10005
    depends_on:
      - trino
```

**Dagster daemon replicas**:

```yaml
services:
  dagster-daemon-1:
    # ... configuration

  dagster-daemon-2:
    # ... configuration
```

### Vertical Scaling

**Resource limits** in `docker-compose.yml`:

```yaml
services:
  trino:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Storage Scaling

**MinIO distributed mode**:

```yaml
services:
  minio-1:
    image: minio/minio
    command: server http://minio-{1...4}/data{1...2}

  minio-2:
    image: minio/minio
    command: server http://minio-{1...4}/data{1...2}

  minio-3:
    image: minio/minio
    command: server http://minio-{1...4}/data{1...2}

  minio-4:
    image: minio/minio
    command: server http://minio-{1...4}/data{1...2}
```

## Security

### Access Control

**PostgreSQL roles**:

```sql
-- Read-only role for BI
CREATE ROLE bi_readonly WITH LOGIN PASSWORD 'secure-password';
GRANT CONNECT ON DATABASE cascade TO bi_readonly;
GRANT USAGE ON SCHEMA marts TO bi_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO bi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO bi_readonly;

-- Application role with limited write
CREATE ROLE app_writer WITH LOGIN PASSWORD 'secure-password';
GRANT CONNECT ON DATABASE cascade TO app_writer;
GRANT USAGE ON SCHEMA bronze TO app_writer;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA bronze TO app_writer;
```

**MinIO policies**:

```bash
# Create read-only policy
mc admin policy create local readonly-policy policy.json

# policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::lake/*"]
    }
  ]
}

# Create user and assign policy
mc admin user add local readonly secure-password
mc admin policy attach local readonly-policy --user readonly
```

### Network Security

**Docker network isolation**:

```yaml
# docker-compose.yml
networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge

services:
  postgres:
    networks:
      - backend

  dagster-webserver:
    networks:
      - backend
      - frontend
    ports:
      - "10006:10006"  # Only expose webserver
```

**Firewall rules**:

```bash
# Allow only specific IPs to access services
iptables -A INPUT -p tcp --dport 10006 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 10006 -j DROP
```

### Secrets Management

**Use secret managers**:

```bash
# AWS Secrets Manager
export POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id phlo/postgres/password \
  --query SecretString --output text)

# HashiCorp Vault
export POSTGRES_PASSWORD=$(vault kv get -field=password secret/phlo/postgres)
```

**Docker secrets**:

```yaml
# docker-compose.yml
secrets:
  postgres_password:
    external: true

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

## Monitoring

### Prometheus Metrics

**Enable Prometheus** in Dagster:

```yaml
# dagster.yaml
telemetry:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
```

**Key metrics to monitor**:

```promql
# Asset materialization success rate
rate(dagster_asset_materializations_total[5m])

# Asset materialization duration
histogram_quantile(0.95, rate(dagster_asset_materialization_duration_seconds_bucket[5m]))

# Failed materializations
rate(dagster_asset_materializations_failed_total[5m])

# Trino query duration
trino_query_execution_time_seconds

# MinIO storage usage
minio_disk_storage_used_bytes
```

### Grafana Dashboards

**Import dashboards**:

1. Start with observability profile:
```bash
phlo services start --profile observability
```

2. Access Grafana: http://localhost:3000

3. Import pre-built dashboards:
   - Dagster metrics
   - Trino performance
   - MinIO storage
   - PostgreSQL queries

### Alerting

**Configure Prometheus alerts**:

```yaml
# prometheus/alerts.yml
groups:
  - name: phlo_alerts
    rules:
      - alert: AssetMaterializationFailed
        expr: rate(dagster_asset_materializations_failed_total[5m]) > 0
        for: 5m
        annotations:
          summary: "Asset materialization failures detected"

      - alert: HighQueryLatency
        expr: histogram_quantile(0.95, rate(trino_query_execution_time_seconds_bucket[5m])) > 30
        for: 10m
        annotations:
          summary: "High Trino query latency"

      - alert: LowStorageSpace
        expr: (minio_disk_storage_free_bytes / minio_disk_storage_total_bytes) < 0.1
        for: 5m
        annotations:
          summary: "Low MinIO storage space"
```

**Slack integration**:

```bash
# .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#data-alerts
```

## Disaster Recovery

### Recovery Plan

**RTO/RPO targets**:

- **RTO** (Recovery Time Objective): 4 hours
- **RPO** (Recovery Point Objective): 24 hours

**Recovery steps**:

1. **Restore PostgreSQL**:
```bash
# Stop services
phlo services stop

# Restore database
gunzip -c backup.sql.gz | docker exec -i phlo-postgres-1 psql -U postgres cascade

# Start services
phlo services start
```

2. **Restore MinIO**:
```bash
# Sync from backup
mc mirror /backups/minio/lake local/lake
```

3. **Verify Nessie catalog**:
```bash
# Check branches
phlo branch list

# Verify table metadata
curl http://localhost:10003/api/v2/trees/main
```

4. **Re-materialize recent partitions**:
```bash
# Last 7 days
for i in {0..6}; do
  date=$(date -d "$i days ago" +%Y-%m-%d)
  phlo materialize --partition $date
done
```

### Testing Recovery

**Regular DR drills**:

```bash
#!/bin/bash
# dr-test.sh

# 1. Backup current state
./backup-all.sh

# 2. Destroy services
phlo services stop --volumes

# 3. Restore from backup
./restore-all.sh

# 4. Verify services
phlo services status

# 5. Test asset materialization
phlo materialize --select "tag:critical" --partition $(date -d "yesterday" +%Y-%m-%d)

# 6. Validate data
./validate-data.sh
```

## Maintenance Windows

### Planned Downtime

**Communication**:

```bash
# Announce maintenance
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "#data-alerts",
    "text": "Scheduled maintenance: Phlo will be down 2025-01-15 02:00-04:00 UTC"
  }'
```

**Maintenance tasks**:

```bash
#!/bin/bash
# maintenance.sh

# 1. Stop Dagster daemon (prevent new runs)
docker stop phlo-dagster-daemon-1

# 2. Wait for running jobs to complete
while [ $(dagster job list --running) -gt 0 ]; do
  sleep 60
done

# 3. Backup databases
./backup-postgres.sh
./backup-minio.sh

# 4. Perform maintenance
docker exec phlo-postgres-1 vacuumdb -U postgres -z cascade

# 5. Optimize Iceberg tables
python -m phlo.maintenance.optimize_tables

# 6. Restart services
phlo services stop
phlo services start

# 7. Verify health
./health-check.sh

# 8. Announce completion
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "#data-alerts",
    "text": "Maintenance complete. Phlo is back online."
  }'
```

## Next Steps

- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Configuration Reference](../reference/configuration-reference.md) - Detailed configuration
- [Best Practices](best-practices.md) - Production patterns
