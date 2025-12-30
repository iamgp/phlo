# Part 12: Production Deployment and Scaling

You've built, tested, and monitored your data lakehouse. Now let's deploy it to production and scale it reliably.

## Development vs Production

What differs between your laptop and production:

| Aspect               | Development              | Production              |
| -------------------- | ------------------------ | ----------------------- |
| **Uptime SLA**       | None (stop anytime)      | 99.9%+                  |
| **Data Retention**   | Days                     | Years                   |
| **Backup Strategy**  | Optional                 | Required (PITR)         |
| **Access Control**   | All devs have all access | Role-based, audited     |
| **Failure Recovery** | Restart containers       | Auto-recovery, failover |
| **Monitoring**       | None (ad-hoc)            | Continuous              |
| **Capacity**         | 16GB RAM, 1TB disk       | 256GB+ RAM, PB+ storage |
| **Cost**             | Minimal                  | Optimized               |
| **Compliance**       | None                     | HIPAA, GDPR, etc.       |

## Architecture: From Laptop to Kubernetes

### Stage 1: Docker Compose (Development)

```
┌─────────────────────────────┐
│   Docker Compose Host       │
├─────────────────────────────┤
│ ┌──────────┐ ┌──────────┐  │
│ │ Dagster  │ │ Trino    │  │
│ └──────────┘ └──────────┘  │
│ ┌──────────┐ ┌──────────┐  │
│ │ MinIO    │ │ Postgres │  │
│ └──────────┘ └──────────┘  │
│ ┌──────────┐ ┌──────────┐  │
│ │ Nessie   │ │ Superset │  │
│ └──────────┘ └──────────┘  │
└─────────────────────────────┘

Use: docker-compose up
```

### Stage 2: Single Server (Small Prod)

```
┌──────────────────────────────────┐
│     Production Server            │
│     (AWS EC2, DigitalOcean)      │
├──────────────────────────────────┤
│ ┌────────────────────────────┐   │
│ │   Systemd Services         │   │
│ │  (instead of docker-compose)   │
│ │                            │   │
│ │ ├─ Dagster (web + daemon) │   │
│ │ ├─ Trino                   │   │
│ │ ├─ Postgres                │   │
│ │ └─ MinIO                   │   │
│ └────────────────────────────┘   │
│                                  │
│  + S3-compatible external storage│
│  + Managed RDS for Postgres      │
│  + CloudWatch monitoring         │
└──────────────────────────────────┘
```

### Stage 3: Kubernetes (High-Scale Prod)

```
┌─────────────────────────────────────────┐
│      Kubernetes Cluster                 │
├─────────────────────────────────────────┤
│  ┌──────────────────────────────────┐   │
│  │    Namespace: dagster          │   │
│  │  ┌────────────────────────────┐ │   │
│  │  │  Dagster Webserver Pods    │ │   │
│  │  │  (replicas: 2)             │ │   │
│  │  └────────────────────────────┘ │   │
│  │  ┌────────────────────────────┐ │   │
│  │  │  Dagster Daemon Pods       │ │   │
│  │  │  (replicas: 1)             │ │   │
│  │  └────────────────────────────┘ │   │
│  │  ┌────────────────────────────┐ │   │
│  │  │  Compute Pods (auto-scale) │ │   │
│  │  │  (replicas: 1-10)          │ │   │
│  │  └────────────────────────────┘ │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │    Namespace: data-warehouse    │   │
│  │  ├─ Trino Coordinator           │   │
│  │  ├─ Trino Workers (3-10)        │   │
│  │  └─ Nessie                      │   │
│  └──────────────────────────────────┘   │
│                                          │
│  External Services:                      │
│  ├─ AWS RDS (Postgres, HA)              │
│  ├─ AWS S3 (data lake)                  │
│  ├─ AWS ElastiCache (caching)           │
│  └─ AWS CloudWatch (monitoring)         │
└─────────────────────────────────────────┘
```

## Deployment Steps

### Step 1: Prepare the Environment

Phlo uses environment variables for configuration. Generate local env files and set defaults:

```bash
# Generate .phlo/.env and .phlo/.env.local
phlo services init

# Copy secrets template
cp .env.example .phlo/.env.local
```

Based on the actual `.env.example`, here are the critical production settings:

```yaml
# phlo.yaml (committed defaults)
env:
  # Database (consider managed RDS for production)
  POSTGRES_USER: lake
  POSTGRES_DB: lakehouse
  POSTGRES_PORT: 10000

  # MinIO / S3 Storage
  MINIO_API_PORT: 10001
  MINIO_CONSOLE_PORT: 10002

  # Nessie (Data Catalog)
  NESSIE_VERSION: 0.105.5
  NESSIE_PORT: 10003

  # Trino (Query Engine)
  TRINO_VERSION: 477
  TRINO_PORT: 10005

  # Iceberg Configuration
  ICEBERG_WAREHOUSE_PATH: s3://lake/warehouse
  ICEBERG_STAGING_PATH: s3://lake/stage
  ICEBERG_NESSIE_REF: main

  # Dagster (Orchestration)
  DAGSTER_PORT: 10006

  # Superset (BI)
  SUPERSET_PORT: 10007

  # API Layer
  API_PORT: 10010

  # Observability Stack
  GRAFANA_PORT: 10016
  PROMETHEUS_PORT: 10013

  # Data Catalog (OpenMetadata)
  OPENMETADATA_PORT: 10020
```

```bash
# .phlo/.env.local (secrets, not committed)
POSTGRES_PASSWORD=<SECURE_PASSWORD>  # Change from default!
MINIO_ROOT_USER=<SECURE_USER>        # Change from default!
MINIO_ROOT_PASSWORD=<SECURE_PASSWORD>
SUPERSET_ADMIN_PASSWORD=<SECURE_PASSWORD>
JWT_SECRET=<SECURE_JWT_SECRET>
HASURA_ADMIN_SECRET=<SECURE_ADMIN_SECRET>
POSTGREST_AUTHENTICATOR_PASSWORD=<SECURE_PASSWORD>
GRAFANA_ADMIN_PASSWORD=<SECURE_PASSWORD>
OPENMETADATA_ADMIN_PASSWORD=<SECURE_PASSWORD>
OPENMETADATA_MYSQL_PASSWORD=<SECURE_PASSWORD>
```

### Step 1b: Infrastructure Configuration (phlo.yaml)

For production deployments, especially when running multiple Phlo projects or customizing service configurations, use `phlo.yaml` for project-level infrastructure settings.

#### Why Infrastructure Configuration?

Secrets in `.phlo/.env.local` and defaults in `phlo.yaml` (env:) handle configuration, but they don't handle:

- **Multi-project deployments**: Running multiple Phlo instances on the same host
- **Container naming patterns**: Custom naming for service discovery
- **Port customization**: Per-project port assignments
- **Service-specific overrides**: Custom configurations for individual services

#### Creating phlo.yaml

Create a `phlo.yaml` file in your project root:

```yaml
# phlo.yaml - Production infrastructure configuration

name: production-lakehouse
description: Production data lakehouse for analytics

infrastructure:
  # Container naming pattern (supports {{project}} and {{service}} variables)
  container_naming_pattern: "{{project}}-{{service}}-1"

  # Service-specific configuration
  services:
    dagster_webserver:
      container_name: null # Use pattern above
      service_name: dagster-webserver
      host: localhost
      internal_host: dagster-webserver
      port: 10006

    postgres:
      container_name: null
      service_name: postgres
      host: localhost
      internal_host: postgres
      port: 10000
      credentials:
        user: postgres
        password: ${POSTGRES_PASSWORD} # References .phlo/.env.local
        database: cascade

    minio:
      container_name: null
      service_name: minio
      host: localhost
      internal_host: minio
      api_port: 10001
      console_port: 10002

    nessie:
      container_name: null
      service_name: nessie
      host: localhost
      internal_host: nessie
      port: 10003

    trino:
      container_name: null
      service_name: trino
      host: localhost
      internal_host: trino
      port: 10005
```

#### Multi-Project Example

Running two Phlo projects on the same server:

**Project 1: Analytics Lakehouse**

```yaml
# analytics/phlo.yaml
name: analytics
description: Analytics data lakehouse

infrastructure:
  container_naming_pattern: "{{project}}-{{service}}-1"
  services:
    dagster_webserver:
      port: 11006 # Different port
    postgres:
      port: 11000
    # ... other services with unique ports
```

**Project 2: ML Platform**

```yaml
# ml-platform/phlo.yaml
name: ml-platform
description: Machine learning data platform

infrastructure:
  container_naming_pattern: "{{project}}-{{service}}-1"
  services:
    dagster_webserver:
      port: 12006 # Different port
    postgres:
      port: 12000
    # ... other services with unique ports
```

Now you can run both simultaneously:

```bash
# Terminal 1: Analytics project
cd analytics/
phlo services start

# Terminal 2: ML platform
cd ml-platform/
phlo services start

# Check running containers
docker ps
# Shows:
# - analytics-dagster-webserver-1 (port 11006)
# - analytics-postgres-1 (port 11000)
# - ml-platform-dagster-webserver-1 (port 12006)
# - ml-platform-postgres-1 (port 12000)
```

#### Configuration Loading

Phlo automatically loads configuration in this order:

1. **phlo.yaml** (project-level infrastructure + env defaults)
2. **.phlo/.env** (generated non-secret defaults)
3. **.phlo/.env.local** (secrets and local overrides)
4. **Environment variables** (runtime overrides)
5. **Defaults** (built-in fallbacks)

Access configuration programmatically:

```python
from phlo.infrastructure.config import (
    load_infrastructure_config,
    get_container_name,
    get_service_config
)

# Load project configuration
config = load_infrastructure_config()
print(config.name)  # "production-lakehouse"

# Get container name for a service
container = get_container_name("dagster-webserver")
# Returns: "production-lakehouse-dagster-webserver-1"

# Get service configuration
postgres_config = get_service_config("postgres")
print(postgres_config["port"])  # 10000
print(postgres_config["internal_host"])  # "postgres"
```

#### Production Best Practices

**1. Use descriptive project names:**

```yaml
name: prod-analytics-us-east
description: Production analytics lakehouse (US East region)
```

**2. Document service purposes:**

```yaml
services:
  dagster_webserver:
    description: Dagster UI and GraphQL API
    port: 10006
```

**3. Reference secrets from .phlo/.env.local:**

```yaml
postgres:
  credentials:
    password: ${POSTGRES_PASSWORD} # Never hardcode secrets
```

**4. Version control phlo.yaml:**

```bash
# Commit to git (no secrets here)
git add phlo.yaml
git commit -m "Add infrastructure configuration"

# But NOT .phlo/.env.local (contains secrets)
echo ".phlo/.env.local" >> .gitignore
```

**5. Use different configs per environment:**

```bash
phlo.yaml              # Base configuration
phlo.staging.yaml      # Staging overrides
phlo.production.yaml   # Production overrides
```

#### Service Discovery

With infrastructure configuration, services can discover each other:

```python
from phlo.infrastructure.config import get_service_config

# Get Postgres connection from config
pg_config = get_service_config("postgres")
connection_string = (
    f"postgresql://{pg_config['credentials']['user']}:"
    f"{pg_config['credentials']['password']}@"
    f"{pg_config['internal_host']}:{pg_config['port']}/"
    f"{pg_config['credentials']['database']}"
)

# Get Trino endpoint
trino_config = get_service_config("trino")
trino_endpoint = f"http://{trino_config['internal_host']}:{trino_config['port']}"
```

#### Kubernetes Integration

For Kubernetes deployments, `phlo.yaml` provides a single source of truth:

```bash
# Generate k8s manifests from phlo.yaml
phlo k8s generate --config phlo.yaml

# Deploys with:
# - Service names from phlo.yaml
# - Port mappings from phlo.yaml
# - Resource limits from phlo.yaml
```

This ensures consistency between Docker Compose (dev) and Kubernetes (prod).

### Step 2: Deploy with Docker Compose

Phlo includes a comprehensive `docker-compose.yml` that orchestrates all services. For production, you have options:

**Option A: Docker Compose (Current Implementation)**

```bash
# Start all core services
docker-compose up -d

# Or start with observability stack
docker-compose --profile observability up -d

# Or start with API layer
docker-compose --profile api up -d

# Or start with data catalog
docker-compose --profile catalog up -d

# Or start everything
docker-compose --profile all up -d

# Check service health
docker-compose ps
```

The actual `docker-compose.yml` includes:

- **Core Services**: postgres, minio, nessie, trino, dagster-webserver, dagster-daemon, superset
- **Observability** (profile: observability): prometheus, loki, grafana, alloy, postgres-exporter
- **API Layer** (profile: api): FastAPI, Hasura GraphQL, PostgREST
- **Data Catalog** (profile: catalog): OpenMetadata with MySQL and Elasticsearch
- **Documentation** (profile: docs): MkDocs server

**Option B: Managed Services (Recommended for Production)**

For production workloads, consider replacing containerized services with managed alternatives:

```bash
# Use AWS RDS for PostgreSQL
POSTGRES_HOST=phlo-prod.xxxxx.rds.amazonaws.com
POSTGRES_PORT=5432

# Use AWS S3 instead of MinIO
ICEBERG_WAREHOUSE_PATH=s3://your-prod-bucket/warehouse
MINIO_API_PORT=9000  # Or S3 endpoint

# Keep Dagster, Trino, Nessie containerized with docker-compose
docker-compose up -d dagster-webserver dagster-daemon trino nessie
```

### Step 3: Verify Service Health

The docker-compose configuration includes health checks for all services:

```bash
# View service status
docker-compose ps

# Check logs for specific service
docker-compose logs -f dagster-webserver
docker-compose logs -f trino
docker-compose logs -f nessie

# Access services
# Dagster UI: http://localhost:10006
# Trino: http://localhost:10005
# Nessie API: http://localhost:10003
# Superset: http://localhost:10007
# MinIO Console: http://localhost:10002
# Grafana (with observability profile): http://localhost:10016
# OpenMetadata (with catalog profile): http://localhost:10020
```

### Step 4: Storage Configuration (Production S3)

For production, replace MinIO with AWS S3:

```bash
# Create S3 bucket
aws s3 mb s3://phlo-prod-lake --region us-east-1

# Enable versioning (for Nessie and time-travel)
aws s3api put-bucket-versioning \
  --bucket phlo-prod-lake \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket phlo-prod-lake \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Update environment variables
ICEBERG_WAREHOUSE_PATH=s3://phlo-prod-lake/warehouse
ICEBERG_STAGING_PATH=s3://phlo-prod-lake/stage
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
```

### Step 5: Observability Stack

Enable Grafana, Prometheus, and Loki for monitoring:

```bash
# Start with observability profile
docker-compose --profile observability up -d

# Access Grafana at http://localhost:10016
# Default credentials from .phlo/.env.local:
# Username: admin
# Password: admin123 (change in production!)

# Prometheus metrics: http://localhost:10013
# Loki logs: Accessible via Grafana data source
```

The observability stack includes:

- **Prometheus**: Metrics collection and storage
- **Loki**: Log aggregation
- **Grafana**: Dashboards and visualization
- **Alloy**: Metrics and log forwarding
- **postgres-exporter**: PostgreSQL metrics

## Future: Kubernetes Deployment

> **Note**: Kubernetes manifests are not yet included in the repository. The following is a reference architecture for future implementation.

For large-scale production deployments, Kubernetes provides better orchestration:

```yaml
# Future: k8s/dagster-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dagster-webserver
  namespace: dagster
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dagster-webserver
  template:
    metadata:
      labels:
        app: dagster-webserver
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: dagster
      containers:
        - name: dagster-webserver
          image: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phlo:1.0.0
          ports:
            - containerPort: 3000
              name: http
            - containerPort: 9090
              name: metrics

          # Resource limits
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"

          # Environment from secrets
          envFrom:
            - secretRef:
                name: phlo-secrets
            - configMapRef:
                name: phlo-config

          # Health checks
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 40
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 5
            failureThreshold: 1

          # Logging
          volumeMounts:
            - name: logs
              mountPath: /app/logs

      # Node selection
      nodeSelector:
        workload: compute

      # Pod disruption budget (for rolling updates)
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - dagster-webserver
                topologyKey: kubernetes.io/hostname

      volumes:
        - name: logs
          emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: dagster-webserver
  namespace: dagster
spec:
  type: LoadBalancer
  selector:
    app: dagster-webserver
  ports:
    - port: 80
      targetPort: 3000
      protocol: TCP
```

**Future Kubernetes deployment** would look like:

```bash
# Create namespace
kubectl create namespace dagster

# Create secrets from .phlo/.env.local
kubectl create secret generic phlo-secrets \
  --from-env-file=.phlo/.env.local \
  -n dagster

# Deploy (when k8s/ manifests are available)
kubectl apply -f k8s/dagster-deployment.yaml
kubectl apply -f k8s/trino-deployment.yaml
kubectl apply -f k8s/nessie-deployment.yaml

# Monitor rollout
kubectl rollout status deployment/dagster-webserver -n dagster
```

## Scaling Strategies

### Vertical Scaling (Bigger Machines)

```bash
# Increase machine size for compute-intensive workloads
kubectl set resources deployment dagster-compute \
  --requests=cpu=2000m,memory=8Gi \
  --limits=cpu=4000m,memory=16Gi \
  -n dagster
```

### Horizontal Scaling (More Machines)

```bash
# Add more Trino workers
kubectl scale deployment trino-worker --replicas=10 -n data-warehouse

# Add more Dagster compute pods
kubectl set env deployment/dagster-compute \
  DAGSTER_K8S_INSTANCE_CONFIG_WORKERS=10 \
  -n dagster
```

### Autoscaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dagster-compute-hpa
  namespace: dagster
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dagster-compute
  minReplicas: 1
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
      selectPolicy: Max
```

## High Availability

### Database Failover

```bash
# RDS Multi-AZ setup (automatic failover)
aws rds modify-db-instance \
  --db-instance-identifier phlo-prod \
  --multi-az \
  --apply-immediately

# Automated backups
aws rds modify-db-instance \
  --db-instance-identifier phlo-prod \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately

# Point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier phlo-prod \
  --target-db-instance-identifier phlo-prod-restored \
  --restore-time 2024-10-15T10:30:00Z
```

### Service Redundancy

```yaml
# k8s/pdb.yaml (Pod Disruption Budget)
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: dagster-pdb
  namespace: dagster
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: dagster-webserver
```

This ensures at least 1 pod is always running during maintenance.

## Disaster Recovery

**Current Implementation: Docker Compose Backups**

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U lake lakehouse > backup_$(date +%Y%m%d).sql

# Backup MinIO data (if using MinIO)
docker run --rm -v $(pwd)/volumes/minio:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data

# For production S3, use cross-region replication
aws s3api put-bucket-replication \
  --bucket phlo-prod-lake \
  --replication-configuration file://replication.json
```

**Future: Kubernetes Backup Automation**

```bash
# Future backup automation with CronJob
cat > k8s/backup-cronjob.yaml << 'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: phlo-backup
  namespace: dagster
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: dagster
          containers:
          - name: backup
            image: amazon/aws-cli:latest
            command:
            - /bin/sh
            - -c
            - |
              aws s3 sync s3://phlo-prod-lake s3://phlo-prod-backup \
                --delete \
                --exclude "tmp/*" \
                --region us-east-1
            env:
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access_key
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret_key
          restartPolicy: OnFailure
EOF

kubectl apply -f k8s/backup-cronjob.yaml
```

## Cost Optimization

```python
# phlo/monitoring/cost_tracking.py
import boto3

def estimate_monthly_cost():
    """Estimate AWS costs."""

    # S3 storage costs
    s3 = boto3.client('s3')
    response = s3.list_bucket_metrics_configurations(Bucket='phlo-prod-lake')

    storage_size_gb = get_bucket_size() / (1024**3)
    storage_cost = storage_size_gb * 0.023  # $0.023/GB/month

    # RDS costs
    rds = boto3.client('rds')
    instances = rds.describe_db_instances()
    rds_cost = len(instances) * 365  # Estimate

    # Compute costs (EC2/ECS)
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances()
    compute_cost = len(instances) * 150  # Estimate

    total = storage_cost + rds_cost + compute_cost

    print(f"Monthly cost estimate:")
    print(f"  Storage (S3): ${storage_cost:,.0f}")
    print(f"  Database (RDS): ${rds_cost:,.0f}")
    print(f"  Compute (K8s): ${compute_cost:,.0f}")
    print(f"  Total: ${total:,.0f}")

    return {
        "storage": storage_cost,
        "database": rds_cost,
        "compute": compute_cost,
        "total": total,
    }

# Optimization strategies
def optimize_costs():
    """Implement cost optimization."""

    # 1. S3 Intelligent-Tiering
    # Automatically move old data to cheaper storage classes

    # 2. Reserved Instances
    # Commit to 1-3 year terms for 40% discount

    # 3. Spot instances for Trino workers
    # Use spot instances for non-critical compute

    # 4. Data lifecycle policies
    # Archive to Glacier after 90 days

    # 5. Compression
    # Compress old Parquet files
    pass
```

## Monitoring Production

**Current Implementation: Grafana + Prometheus**

```bash
# Start observability stack
docker-compose --profile observability up -d

# Access Grafana dashboards
# http://localhost:10016

# View Prometheus metrics
# http://localhost:10013

# Query logs with Loki
# Available via Grafana Explore interface
```

Grafana dashboards are pre-provisioned in `.phlo/grafana/dashboards/`:

- Lakehouse overview
- Dagster pipeline metrics
- PostgreSQL database metrics
- Trino query performance

**Future: Cloud-Native Monitoring**

For AWS deployments, integrate with CloudWatch:

```bash
# CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name PhloProductionStatus \
  --dashboard-body file://dashboard.json

# Set up alerts
aws cloudwatch put-metric-alarm \
  --alarm-name phlo-dagster-failures \
  --alarm-description "Alert on Dagster failures" \
  --metric-name PipelineFailures \
  --namespace Phlo \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

## Summary

Production deployment with Phlo:

### Current Implementation (Docker Compose)

**Deployment Method**: `docker-compose up -d` with profiles
**Infrastructure**: Containerized services with health checks
**Storage**: MinIO (dev) or S3 (production)
**Database**: PostgreSQL (containerized or RDS)
**Monitoring**: Grafana + Prometheus + Loki
**Scaling**: Vertical (increase container resources)

### Production Readiness Checklist

✅ **Implemented**:

- Docker Compose orchestration with health checks
- Environment-based configuration (`phlo.yaml` + `.phlo/.env.local`)
- Observability stack (Grafana, Prometheus, Loki)
- API layer with authentication (FastAPI, Hasura, PostgREST)
- Data catalog integration (OpenMetadata)
- Multi-profile deployment (core, observability, api, catalog)

📋 **Recommended for Production**:

- Replace MinIO with AWS S3 or similar object storage
- Use managed PostgreSQL (RDS, Cloud SQL)
- Implement backup automation
- Set up SSL/TLS certificates
- Configure firewall rules and VPC
- Change all default passwords in `.phlo/.env.local`
- Enable audit logging

🔮 **Future (Kubernetes)**:

- Kubernetes manifests for k8s/ directory
- Horizontal pod autoscaling
- Multi-region deployment
- Service mesh integration

### Quick Start

```bash
# Development
phlo services init
docker-compose up -d

# Production (all features)
cp .env.example .phlo/.env.local
# Edit .phlo/.env.local with production credentials
docker-compose --profile all up -d

# Access services
# Dagster: http://localhost:10006
# Grafana: http://localhost:10016
# Superset: http://localhost:10007
# OpenMetadata: http://localhost:10020
```

---

**Next**: [Part 13 - Plugin System](13-plugin-system.md) - Extend Phlo with custom plugins

**Series**:

1. Data Lakehouse concepts
2. Getting started
3. Apache Iceberg
4. Project Nessie
5. Data ingestion
6. dbt transformations
7. Dagster orchestration
8. Real-world example
9. Data quality with Pandera
10. Metadata and governance
11. Observability and monitoring
12. **Production deployment** ← You are here
13. Plugin system

Happy data engineering!
