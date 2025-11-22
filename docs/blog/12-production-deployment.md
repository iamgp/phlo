# Part 12: Production Deployment and Scaling

You've built, tested, and monitored your data lakehouse. Now let's deploy it to production and scale it reliably.

## Development vs Production

What differs between your laptop and production:

| Aspect | Development | Production |
|--------|-----------|-----------|
| **Uptime SLA** | None (stop anytime) | 99.9%+ |
| **Data Retention** | Days | Years |
| **Backup Strategy** | Optional | Required (PITR) |
| **Access Control** | All devs have all access | Role-based, audited |
| **Failure Recovery** | Restart containers | Auto-recovery, failover |
| **Monitoring** | None (ad-hoc) | Continuous |
| **Capacity** | 16GB RAM, 1TB disk | 256GB+ RAM, PB+ storage |
| **Cost** | Minimal | Optimized |
| **Compliance** | None | HIPAA, GDPR, etc. |

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

```bash
# Production environment variables
cat > .env.prod << 'EOF'
# Deployment
ENVIRONMENT=production
REGION=us-east-1
AVAILABILITY_ZONES=us-east-1a,us-east-1b,us-east-1c

# Database
POSTGRES_HOST=phlo-prod.c123456.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=phlo
POSTGRES_USER=cascade_admin
POSTGRES_PASSWORD=<SECURE_PASSWORD>

# Storage
S3_ENDPOINT=s3.us-east-1.amazonaws.com
S3_BUCKET=phlo-prod-lake
S3_ACCESS_KEY=<AWS_ACCESS_KEY>
S3_SECRET_KEY=<AWS_SECRET_KEY>
S3_REGION=us-east-1

# Dagster
DAGSTER_DAEMON_INTERVAL=30
DAGSTER_LOG_LEVEL=INFO
DAGSTER_STORAGE_BACKEND=postgres

# Security
JWT_SECRET_KEY=<SECURE_JWT_KEY>
ENCRYPTION_KEY=<SECURE_ENCRYPTION_KEY>

# Monitoring
NEWRELIC_LICENSE_KEY=<LICENSE_KEY>
DATADOG_API_KEY=<API_KEY>

# Slack (alerts)
SLACK_BOT_TOKEN=xoxb-<TOKEN>
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/<PATH>

# PagerDuty (on-call)
PAGERDUTY_API_KEY=<API_KEY>
PAGERDUTY_SERVICE_ID=<SERVICE_ID>
EOF

# Never commit .env files to git
echo ".env.prod" >> .gitignore
```

### Step 2: Database Setup

```bash
# Create RDS instance (AWS CLI)
aws rds create-db-instance \
  --db-instance-identifier phlo-prod \
  --db-instance-class db.m5.xlarge \
  --engine postgres \
  --master-username cascade_admin \
  --master-user-password $POSTGRES_PASSWORD \
  --allocated-storage 500 \
  --storage-type gp3 \
  --backup-retention-period 30 \
  --enable-iam-database-authentication \
  --enable-cloudwatch-logs-exports postgresql \
  --multi-az \
  --region us-east-1

# Wait for instance to be available
aws rds wait db-instance-available \
  --db-instance-identifier phlo-prod

# Initialize schema
docker run -it \
  -e POSTGRES_HOST=phlo-prod.c123456.us-east-1.rds.amazonaws.com \
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  phlo:latest \
  bash -c "cd services/dagster && alembic upgrade head"
```

### Step 3: Storage (S3) Setup

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

# Block public access
aws s3api put-public-access-block \
  --bucket phlo-prod-lake \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create IAM role for services
aws iam create-role --role-name phlo-prod-role \
  --assume-role-policy-document file://trust-policy.json

# Attach S3 policy
aws iam put-role-policy --role-name phlo-prod-role \
  --policy-name phlo-s3-policy \
  --policy-document file://s3-policy.json
```

### Step 4: Containerization

```dockerfile
# Dockerfile for production
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install uv && uv pip install --system -e .

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:3000/health')"

# Run Dagster
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
```

Push to registry:

```bash
# Build
docker build -t phlo:1.0.0 .

# Tag for registry
docker tag phlo:1.0.0 <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phlo:1.0.0

# Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phlo:1.0.0
```

### Step 5: Kubernetes Deployment

```yaml
# k8s/dagster-deployment.yaml
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

Deploy:

```bash
# Create namespace
kubectl create namespace dagster

# Create secrets
kubectl create secret generic phlo-secrets \
  --from-file=.env.prod \
  -n dagster

# Deploy
kubectl apply -f k8s/dagster-deployment.yaml

# Monitor rollout
kubectl rollout status deployment/dagster-webserver -n dagster

# Check status
kubectl get pods -n dagster
kubectl logs -f deployment/dagster-webserver -n dagster
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

```bash
# Daily backup to S3
aws s3 sync s3://phlo-prod-lake s3://phlo-prod-backup \
  --delete \
  --exclude "tmp/*"

# Backup automation (CronJob)
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

```bash
# CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name CascadeProdStatus \
  --dashboard-body file://dashboard.json

# Real-time alerts
aws sns create-topic --name phlo-alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789:phlo-alerts \
  --protocol email \
  --notification-endpoint ops@company.com

# Automated response
aws lambda create-function \
  --function-name phlo-auto-remediate \
  --runtime python3.11 \
  --handler index.handler \
  --zip-file fileb://lambda.zip
```

## Summary

Production deployment requires:

**Infrastructure**: RDS, S3, Kubernetes cluster  
**Security**: Secrets management, encryption, RBAC  
**Reliability**: Backups, failover, disaster recovery  
**Scalability**: Autoscaling, resource management  
**Observability**: Monitoring, logging, alerts  
**Cost Control**: Tracking, optimization  

With these foundations, Phlo scales from prototype to enterprise-grade data platform.

---

**Series Complete!**

You've now learned the full Phlo stack:

1. **Part 1**: Data Lakehouse concepts
2. **Part 2**: Getting started
3. **Part 3**: Apache Iceberg
4. **Part 4**: Project Nessie
5. **Part 5**: Data ingestion
6. **Part 6**: dbt transformations
7. **Part 7**: Dagster orchestration
8. **Part 8**: Real-world example
9. **Part 9**: Data quality with Pandera
10. **Part 10**: Metadata and governance
11. **Part 11**: Observability and monitoring
12. **Part 12**: Production deployment

Next steps:
- Deploy Phlo to your organization
- Extend with your own data sources
- Contribute improvements back to the community

Happy data engineering!
