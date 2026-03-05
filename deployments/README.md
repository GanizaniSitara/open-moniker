# Open Moniker Deployment Guide

**The Full Monty:** Local, Render, and AWS deployments with Java and Go resolvers.

## Resolver Implementations

| Language | Performance | Status | Port |
|----------|-------------|--------|------|
| **Python** | ~2K req/s | ✅ Production | 8051 (resolver), 8052 (management) |
| **Java** | ~8.5K req/s | ✅ Production | 8054 |
| **Go** | ~21K req/s | ✅ Production | 8053 |

**Architecture Requirements:**
- Interchangeable resolvers (Java ↔ Go)
- Backwards compatible with Python monolith
- Performance benchmarks maintained
- All tested with same test suite

---

## 1. LOCAL DEVELOPMENT

### Quick Start
```bash
cd deployments/local

# Dev with Java
python3 bootstrap.py dev

# Dev with Go
python3 bootstrap.py dev --resolver go

# Both environments side-by-side
python3 bootstrap.py both
```

**Ports:** Dev (8054 Java, 8053 Go, 8052 Python), UAT (9054, 9053, 9052)

---

## 2. RENDER.COM (✅ DEPLOYED)

**Services:**
- Java Resolver: https://moniker-resolver-java.onrender.com
- Python Admin: https://moniker-admin.onrender.com
- PostgreSQL: moniker-telemetry

**Test:**
```bash
python3 test_render.py \
  https://moniker-admin.onrender.com \
  https://moniker-resolver-java.onrender.com
```

**Cost:** $21/month (3 starter services)

---

## 3. AWS PRODUCTION (Blueprint)

**Architecture:**
- 6 resolvers (Java or Go, interchangeable)
- Multi-region (us-east-1, us-west-2)
- Aurora PostgreSQL telemetry
- Round-robin DNS

**Deploy:**
```bash
cd deployments/aws/terraform
terraform apply -var-file=environments/prod.tfvars
```

**Cost:** ~$700/month (or $420 with Spot instances)

---

See `deployments/{local,render,aws}/README.md` for details.
