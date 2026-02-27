# Control Plane for 6 Go Servers on AWS

## Recommendation: AWS ECS Service Connect + Envoy (with optional go-control-plane)

For 6 Go microservices on AWS, the sweet spot is **ECS Service Connect** for
service mesh basics, with the option to layer in a custom
**go-control-plane** if you need fine-grained traffic shaping beyond what
ECS Service Connect provides out of the box.

---

## Why This Approach

| Concern | Recommendation | Rationale |
|---------|---------------|-----------|
| **Service discovery** | ECS Service Connect (Cloud Map) | Zero-config, no Consul/etcd to run |
| **Load balancing** | Envoy sidecar (managed by ECS) | Already included with Service Connect |
| **mTLS** | ECS Service Connect TLS | Automatic cert rotation, no custom CA |
| **Observability** | Envoy → CloudWatch / X-Ray | Built-in metrics + distributed tracing |
| **Traffic shaping** | go-control-plane (xDS) | Only if you need canary/weighted routing |
| **Config management** | AWS AppConfig or SSM Parameter Store | Centralized, versioned, no restart needed |

### Why NOT Istio / Full Service Mesh

With only 6 services, a full Kubernetes + Istio stack adds significant
operational overhead (EKS cluster, Istio control plane, CRDs, upgrades).
ECS Service Connect gives you 80% of the benefit at 20% of the complexity.

### Why NOT Consul

HashiCorp Consul is excellent but adds another system to operate. Cloud Map
(which backs ECS Service Connect) is fully managed and native to AWS.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  AWS ECS Cluster                                                  │
│                                                                   │
│  ┌─────────────────────┐     ┌─────────────────────┐             │
│  │ Go Service A        │     │ Go Service B        │             │
│  │ ┌───────┐ ┌───────┐ │     │ ┌───────┐ ┌───────┐ │             │
│  │ │ App   │ │ Envoy │◄├─────├►│ Envoy │ │ App   │ │             │
│  │ │       │ │ proxy │ │ mTLS│ │ proxy │ │       │ │             │
│  │ └───────┘ └───┬───┘ │     │ └───┬───┘ └───────┘ │             │
│  └───────────────┼─────┘     └─────┼───────────────┘             │
│                  │                  │                              │
│          ┌───────▼──────────────────▼────────┐                    │
│          │  ECS Service Connect               │                    │
│          │  (Cloud Map + managed Envoy xDS)   │                    │
│          └───────────────┬───────────────────┘                    │
│                          │                                         │
│          ┌───────────────▼───────────────────┐                    │
│          │  Optional: Custom go-control-plane │                    │
│          │  (for advanced xDS policies)       │                    │
│          └───────────────────────────────────┘                    │
│                                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ Svc C   │ │ Svc D   │ │ Svc E   │ │ Svc F   │               │
│  │ +Envoy  │ │ +Envoy  │ │ +Envoy  │ │ +Envoy  │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
└──────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐        ┌──────────────────────┐
│ Open Moniker Svc │        │ CloudWatch / X-Ray   │
│ (Python/FastAPI) │        │ (metrics + traces)   │
└──────────────────┘        └──────────────────────┘
```

---

## The 6 Go Services — Suggested Roles

Based on Open Moniker's data governance domain, the 6 Go servers likely map to:

| Service | Purpose | Why Go |
|---------|---------|--------|
| **gateway** | API gateway / edge proxy | High-throughput, low-latency routing |
| **resolver** | Moniker resolution (hot path) | Sub-ms latency for high-volume lookups |
| **telemetry-collector** | Access telemetry ingestion | High-volume event streaming |
| **cache-manager** | Redis/cache orchestration | Background refresh, TTL management |
| **policy-engine** | Access policy evaluation | Fast rule evaluation at request time |
| **health-monitor** | Health checks + circuit breaker | Monitors upstream sources (Snowflake, Oracle, etc.) |

---

## Phase 1: ECS Service Connect (Start Here)

### ECS Task Definition (per Go service)

```json
{
  "family": "moniker-resolver",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "resolver",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/moniker-resolver:latest",
      "portMappings": [
        {
          "name": "resolver-http",
          "containerPort": 8080,
          "protocol": "tcp",
          "appProtocol": "grpc"
        }
      ],
      "environment": [
        { "name": "OTEL_EXPORTER_OTLP_ENDPOINT", "value": "http://localhost:4317" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/moniker-resolver",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "resolver"
        }
      }
    }
  ]
}
```

### ECS Service with Service Connect

```json
{
  "serviceName": "moniker-resolver",
  "cluster": "moniker-control-plane",
  "serviceConnectConfiguration": {
    "enabled": true,
    "namespace": "moniker.local",
    "services": [
      {
        "portName": "resolver-http",
        "discoveryName": "resolver",
        "clientAliases": [
          { "port": 8080, "dnsName": "resolver.moniker.local" }
        ]
      }
    ]
  }
}
```

### What You Get for Free

- **Service discovery**: `resolver.moniker.local` resolves automatically
- **Load balancing**: Round-robin across tasks
- **Health checks**: Envoy health probes
- **Metrics**: Request count, latency, error rate → CloudWatch
- **TLS**: Opt-in mTLS between services

---

## Phase 2: Custom go-control-plane (When Needed)

Add this only if you need:
- Weighted routing (canary deployments: 95% v1, 5% v2)
- Header-based routing (route by client ID or moniker domain)
- Circuit breaking with custom thresholds
- Rate limiting per upstream

### go-control-plane Server Skeleton

```go
package main

import (
    "context"
    "log"
    "net"

    clusterv3 "github.com/envoyproxy/go-control-plane/envoy/config/cluster/v3"
    corev3 "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
    endpointv3 "github.com/envoyproxy/go-control-plane/envoy/config/endpoint/v3"
    listenerv3 "github.com/envoyproxy/go-control-plane/envoy/config/listener/v3"
    routev3 "github.com/envoyproxy/go-control-plane/envoy/config/route/v3"
    "github.com/envoyproxy/go-control-plane/pkg/cache/v3"
    "github.com/envoyproxy/go-control-plane/pkg/server/v3"
    "google.golang.org/grpc"

    discoveryv3 "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"
)

func main() {
    // Snapshot cache holds the xDS configuration
    snapshotCache := cache.NewSnapshotCache(false, cache.IDHash{}, nil)

    // Build initial snapshot with all 6 services
    snapshot, _ := cache.NewSnapshot("1",
        map[string][]cache.Resource{
            "type.googleapis.com/envoy.config.endpoint.v3.ClusterLoadAssignment": endpoints(),
            "type.googleapis.com/envoy.config.cluster.v3.Cluster":               clusters(),
            "type.googleapis.com/envoy.config.route.v3.RouteConfiguration":      routes(),
            "type.googleapis.com/envoy.config.listener.v3.Listener":             listeners(),
        },
    )
    snapshotCache.SetSnapshot(context.Background(), "moniker-mesh", snapshot)

    // Start xDS gRPC server
    srv := server.NewServer(context.Background(), snapshotCache, nil)
    grpcServer := grpc.NewServer()
    discoveryv3.RegisterAggregatedDiscoveryServiceServer(grpcServer, srv)

    lis, _ := net.Listen("tcp", ":18000")
    log.Println("xDS control plane listening on :18000")
    grpcServer.Serve(lis)
}

// clusters defines the 6 Go services + Open Moniker backend
func clusters() []cache.Resource {
    services := []string{
        "gateway", "resolver", "telemetry-collector",
        "cache-manager", "policy-engine", "health-monitor",
    }
    var resources []cache.Resource
    for _, svc := range services {
        resources = append(resources, &clusterv3.Cluster{
            Name:                 svc,
            ConnectTimeout:       durationpb(5),
            ClusterDiscoveryType: &clusterv3.Cluster_Type{Type: clusterv3.Cluster_EDS},
            LbPolicy:             clusterv3.Cluster_ROUND_ROBIN,
            EdsClusterConfig: &clusterv3.Cluster_EdsClusterConfig{
                EdsConfig: &corev3.ConfigSource{
                    ConfigSourceSpecifier: &corev3.ConfigSource_Ads{},
                },
            },
        })
    }
    return resources
}

// endpoints, routes, listeners would follow same pattern
// ...
```

### go.mod

```
module github.com/your-org/moniker-control-plane

go 1.22

require (
    github.com/envoyproxy/go-control-plane v0.13.1
    google.golang.org/grpc v1.65.0
    google.golang.org/protobuf v1.34.2
)
```

---

## Phase 3: Integration with Open Moniker

The Go control plane can dynamically route based on moniker catalog metadata:

```
Client → Gateway (Go) → Resolver (Go) → Control Plane decision:
  ├── risk.cvar/* → Oracle adapter pod (high-memory)
  ├── prices.*   → Snowflake adapter pod (warehouse-optimized)
  ├── credit.*   → MSSQL adapter pod
  └── nav.*      → REST proxy pod
```

The control plane reads `sample_catalog.yaml` source bindings and generates
Envoy routes that direct traffic to the correct backend adapter based on the
moniker's `source_binding.type`.

---

## Observability Stack

```
Go Services (OpenTelemetry SDK)
    │
    ├── Traces → AWS X-Ray (or Jaeger on ECS)
    ├── Metrics → CloudWatch (via Envoy + OTEL collector)
    └── Logs → CloudWatch Logs (structured JSON)
```

Each Go service should use the OpenTelemetry Go SDK:

```go
import "go.opentelemetry.io/otel"

tracer := otel.Tracer("moniker-resolver")
ctx, span := tracer.Start(ctx, "resolve-moniker")
defer span.End()
```

---

## Security

| Layer | Mechanism |
|-------|-----------|
| Service-to-service | mTLS via ECS Service Connect |
| External ingress | ALB + WAF + Cognito/API keys |
| Secrets | AWS Secrets Manager (DB creds, API keys) |
| IAM | Task roles per service (least privilege) |
| Network | Private subnets, VPC endpoints for AWS services |

---

## Cost Estimate (6 Services)

| Component | Monthly Estimate |
|-----------|-----------------|
| ECS Fargate (6 services × 0.5 vCPU, 1GB) | ~$90 |
| ECS Service Connect (no extra charge) | $0 |
| Cloud Map | ~$1 |
| CloudWatch Logs + Metrics | ~$20 |
| ALB | ~$25 |
| **Total** | **~$136/month** |

Adding a custom go-control-plane server: +$15/month (single small task).

---

## Decision Matrix

| Approach | Complexity | Flexibility | Ops Burden | Best For |
|----------|-----------|-------------|------------|----------|
| **ECS Service Connect** | Low | Medium | Minimal | Start here (Phase 1) |
| **+ go-control-plane** | Medium | High | Low | Canary, header routing |
| Istio on EKS | High | Very High | High | 50+ services |
| Consul Connect | Medium | High | Medium | Multi-cloud / hybrid |
| AWS App Mesh | Medium | Medium | Low | Deprecated path |

---

## Recommendation Summary

1. **Start with ECS Service Connect** — gives you service discovery, load
   balancing, mTLS, and observability with zero custom infrastructure
2. **Add go-control-plane when** you need canary deployments, header-based
   routing, or moniker-aware traffic shaping
3. **Skip Istio/EKS** unless you're scaling well beyond 6 services
4. **Skip App Mesh** — AWS is steering toward Service Connect as the
   replacement
