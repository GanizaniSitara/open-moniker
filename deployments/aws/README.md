# AWS Production Deployment Blueprint

Multi-region, high-availability production deployment with Java/Go resolvers.

## Architecture

- **6 Resolvers** across 2 regions (us-east-1, us-west-2)
- **Choice:** All Java, All Go, or Mixed
- **1 Python Management** service (active-standby)
- **Aurora PostgreSQL** for telemetry
- **Round-robin DNS** via Route 53
- **EKS clusters** for orchestration

## Performance Targets

| Configuration | Total RPS | Latency p95 |
|---------------|-----------|-------------|
| 6x Java | 48,000 | <20ms |
| 6x Go | 126,000 | <10ms |
| 3 Java + 3 Go | 87,000 | <15ms |

## Quick Deploy

```bash
cd deployments/aws/terraform

# Initialize
terraform init

# Review plan
terraform plan -var-file=environments/prod.tfvars

# Deploy infrastructure
terraform apply -var-file=environments/prod.tfvars

# Deploy applications
cd ../kubernetes
kubectl apply -k overlays/us-east-1
kubectl apply -k overlays/us-west-2

# Verify
./scripts/health-check.sh
```

## Directory Structure

```
deployments/aws/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── vpc/              # VPC, subnets, NAT gateways
│   │   ├── eks/              # EKS clusters
│   │   ├── aurora/           # Aurora Serverless v2
│   │   ├── dns/              # Route 53 round-robin
│   │   └── monitoring/       # CloudWatch dashboards
│   └── environments/
│       ├── dev.tfvars
│       ├── staging.tfvars
│       └── prod.tfvars
├── kubernetes/
│   ├── base/
│   │   ├── java-resolver.yaml
│   │   ├── go-resolver.yaml
│   │   ├── python-admin.yaml
│   │   └── configmap.yaml
│   └── overlays/
│       ├── us-east-1/
│       └── us-west-2/
├── docker/
│   ├── Dockerfile.java
│   ├── Dockerfile.go
│   └── Dockerfile.python
├── scripts/
│   ├── deploy.sh
│   ├── health-check.sh
│   └── migrate-db.sh
└── README.md               # This file
```

## Resolver Configuration

### Option A: All Java (Simpler)
```yaml
# terraform/environments/prod.tfvars
resolver_type = "java"
resolver_count_per_region = 3
```

**Pros:** Simpler ops, one runtime, good performance
**Cons:** Lower max throughput than Go

### Option B: All Go (Maximum Performance)
```yaml
resolver_type = "go"
resolver_count_per_region = 3
```

**Pros:** Maximum performance (2.5x Java)
**Cons:** Less mature telemetry implementation

### Option C: Mixed (Test Both)
```yaml
resolver_mix = {
  "us-east-1a" = "java"
  "us-east-1b" = "go"
  "us-east-1c" = "java"
  "us-west-2a" = "go"
  "us-west-2b" = "java"
  "us-west-2c" = "go"
}
```

**Pros:** Compare in production, gradual migration
**Cons:** More complex operations

## Infrastructure Components

### VPC (per region)
- 3 public subnets (one per AZ)
- 3 private subnets (one per AZ)
- 3 NAT gateways (high availability)
- Internet gateway
- Route tables

### EKS Cluster (per region)
- Control plane: $72/month
- 2 node groups:
  - Resolvers: 3x t3.medium (2 vCPU, 4GB)
  - Admin: 1x t3.small (2 vCPU, 2GB)
- Auto-scaling: 3-6 nodes per region

### Aurora PostgreSQL
- **Engine:** PostgreSQL 16
- **Mode:** Serverless v2
- **Capacity:** 0.5-4 ACU (auto-scales)
- **Primary:** us-east-1
- **Replica:** us-west-2 (read-only)
- **Storage:** Auto-scaling, encrypted
- **Backups:** 7-day retention

### Route 53 DNS
- Hosted zone for `example.com`
- Round-robin weighted routing:
  ```
  resolver.example.com → 6 IPs (16.7% each)
  ```
- TTL: 60 seconds (fast failover)

## Cost Breakdown

| Component | Quantity | Cost/Month |
|-----------|----------|------------|
| EKS Control Plane | 2 | $144 |
| EC2 Nodes (t3.medium) | 6 | $150 |
| EC2 Nodes (t3.small) | 2 | $33 |
| Aurora Serverless | 1 | $160 |
| NAT Gateways | 6 | $194 |
| Network Load Balancers | 2 | $32 |
| Route 53 | 1 | $1 |
| Data Transfer (est) | - | $50 |
| CloudWatch Logs | - | $20 |
| **Total** | - | **$784/month** |

**Optimizations:**
- Use Spot instances: -40% ($470/month)
- Single region only: -45% ($430/month)
- Smaller Aurora (0.5 ACU fixed): -$100
- **Optimized Total:** ~$370-470/month

## Deployment Steps

### 1. Prerequisites
```bash
# Install tools
brew install terraform kubectl aws-cli

# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### 2. Deploy Infrastructure
```bash
cd terraform

# Initialize Terraform
terraform init

# Deploy dev environment first
terraform apply -var-file=environments/dev.tfvars

# Then production
terraform apply -var-file=environments/prod.tfvars
```

### 3. Configure kubectl
```bash
# Update kubeconfig for both regions
aws eks update-kubeconfig --name moniker-us-east-1 --region us-east-1
aws eks update-kubeconfig --name moniker-us-west-2 --region us-west-2

# Verify
kubectl get nodes --context=moniker-us-east-1
kubectl get nodes --context=moniker-us-west-2
```

### 4. Deploy Applications
```bash
cd ../kubernetes

# Deploy to us-east-1
kubectl apply -k overlays/us-east-1 --context=moniker-us-east-1

# Deploy to us-west-2
kubectl apply -k overlays/us-west-2 --context=moniker-us-west-2

# Verify pods
kubectl get pods -n moniker --context=moniker-us-east-1
kubectl get pods -n moniker --context=moniker-us-west-2
```

### 5. Verify Deployment
```bash
# Run health checks
./scripts/health-check.sh

# Test DNS round-robin
for i in {1..10}; do
  dig +short resolver.example.com
done

# Load test
hey -z 60s -c 500 http://resolver.example.com/resolve/test/path@latest
```

## Monitoring

### CloudWatch Dashboards
- Resolver metrics (RPS, latency, errors)
- EKS cluster health (CPU, memory, pods)
- Aurora metrics (connections, CPU, storage)
- NAT gateway traffic

### Telemetry Database
```sql
-- Query telemetry
psql -h aurora-endpoint.us-east-1.rds.amazonaws.com \
     -U postgres -d moniker_telemetry

-- Resolver performance
SELECT
  resolver_id,
  COUNT(*) as requests,
  AVG(latency_ms) as avg_latency,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
FROM access_log
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY resolver_id;
```

### Python Dashboard
Navigate to `https://admin.example.com/dashboard` for:
- Live RPS/latency charts
- Resolver health status
- Top monikers
- Error rates

## Scaling

### Horizontal Scaling (more resolvers)
```bash
# Edit terraform/environments/prod.tfvars
resolver_count_per_region = 6  # 12 total

# Apply changes
terraform apply -var-file=environments/prod.tfvars
```

### Vertical Scaling (bigger instances)
```bash
# Edit terraform/modules/eks/main.tf
instance_types = ["t3.large"]  # 2 vCPU → 4 vCPU

terraform apply
```

### Aurora Scaling
```hcl
# Automatic via Serverless v2
serverlessv2_scaling_configuration {
  min_capacity = 0.5
  max_capacity = 8  # Increase max
}
```

## Disaster Recovery

### RTO (Recovery Time Objective): 5 minutes
### RPO (Recovery Point Objective): 5 minutes

**Scenario: us-east-1 region failure**

1. DNS automatically routes to us-west-2 (TTL=60s)
2. Aurora read replica promotes to primary
3. Scale up us-west-2 resolvers to handle full load
4. Python admin fails over to us-west-2 standby

### Runbook
```bash
# Promote Aurora replica
aws rds promote-read-replica \
  --db-instance-identifier moniker-telemetry-us-west-2

# Scale us-west-2
kubectl scale deployment java-resolver \
  --replicas=6 \
  --context=moniker-us-west-2

# Verify
./scripts/health-check.sh --region us-west-2
```

## Migration from Render

### Phase 1: Parallel Run (1 week)
- Deploy AWS infrastructure
- Route 10% traffic to AWS via DNS weights
- Compare telemetry and performance

### Phase 2: Gradual Migration (2 weeks)
- Week 1: 50% AWS, 50% Render
- Week 2: 80% AWS, 20% Render
- Monitor dashboards for anomalies

### Phase 3: Full Cutover (1 week)
- Route 100% traffic to AWS
- Keep Render as backup for 1 week
- Decommission Render services

## Security

- **Network:** Private subnets, security groups, NACLs
- **Encryption:** TLS in transit, encryption at rest (Aurora, EBS)
- **Secrets:** AWS Secrets Manager for DB passwords
- **IAM:** Least-privilege roles for pods (IRSA)
- **Compliance:** HIPAA, SOC 2 ready

## Support

- **Runbooks:** `deployments/aws/runbooks/`
- **Terraform Docs:** `terraform/README.md`
- **Kubernetes Docs:** `kubernetes/README.md`
- **Issues:** GitHub issues
