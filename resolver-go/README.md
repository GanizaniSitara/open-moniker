# Moniker Resolver - Go Implementation

High-performance Go implementation of the moniker resolution service, designed to achieve 20K+ req/s while maintaining 100% API equivalence with the Python implementation.

## Status: 🚧 Under Development (Phase 1 MVP)

### Completed Components

- ✅ **Moniker Types** (`internal/moniker/types.go`)
  - MonikerPath, Moniker, QueryParams, VersionType
  - 100% field parity with Python

- ✅ **Moniker Parser** (`internal/moniker/parser.go`)
  - Complete regex pattern support (segments, namespaces, versions)
  - Parse, ClassifyVersion, ValidateSegment/Namespace
  - All version types: DATE, LATEST, LOOKBACK, FREQUENCY, ALL, CUSTOM

- ✅ **Catalog Types** (`internal/catalog/types.go`)
  - SourceType, NodeStatus enums
  - Ownership, SourceBinding, AccessPolicy
  - CatalogNode, ResolvedOwnership
  - DataQuality, SLA, Freshness, DataSchema, Documentation, AuditEntry
  - All ~30 fields per CatalogNode

- ✅ **Catalog Registry** (`internal/catalog/registry.go`)
  - Thread-safe operations with RWMutex
  - Hierarchical lookup and ownership inheritance
  - FindSourceBinding, ResolveOwnership
  - Search, pagination, atomic replace

- ✅ **Configuration** (`internal/config/config.go`)
  - YAML config loading (shared with Python)
  - All config sections: server, telemetry, cache, catalog, auth

- ✅ **In-Memory Cache** (`internal/cache/memory.go`)
  - Thread-safe cache with TTL
  - Background cleanup goroutine

- ✅ **Main Entry Point** (`cmd/resolver/main.go`)
  - Basic HTTP server setup
  - Health endpoint
  - Graceful shutdown

### In Progress / TODO

- ⏳ **Catalog Loader** (`internal/catalog/loader.go`)
  - YAML parsing for catalog nodes
  - Hot reload support

- ⏳ **Service Layer** (`internal/service/service.go`)
  - Core resolution algorithm
  - Ownership hierarchy walking
  - Access policy validation
  - Template formatting

- ⏳ **HTTP Handlers** (`internal/handlers/`)
  - 19 routes to implement
  - Error handling with exact Python parity

- ⏳ **Dialect System** (`internal/dialect/`)
  - SQL placeholder expansion
  - Snowflake/Oracle/MSSQL dialects

- ⏳ **Telemetry** (`internal/telemetry/`)
  - Event emitter, batcher, sinks

- ⏳ **Domains** (`internal/domains/`)
  - Domain registry integration

- ⏳ **Governance** (`internal/governance/`)
  - Rate limiter, circuit breaker

## Building

```bash
# Install dependencies
cd resolver-go
go mod tidy

# Build
go build -o bin/resolver ./cmd/resolver

# Run
./bin/resolver --config ../config.yaml --port 8053
```

## Quick Start

```bash
# From project root
export PATH=$HOME/go-local/go/bin:$PATH
cd resolver-go

# Run with default config
go run ./cmd/resolver --config ../config.yaml --port 8053

# Test health endpoint
curl http://localhost:8053/health
```

## Project Structure

```
resolver-go/
├── cmd/
│   └── resolver/
│       └── main.go              # Entry point
├── internal/
│   ├── moniker/                 # Moniker parsing (✅ complete)
│   │   ├── types.go
│   │   └── parser.go
│   ├── catalog/                 # Catalog registry (✅ complete)
│   │   ├── types.go
│   │   ├── registry.go
│   │   └── loader.go            # TODO
│   ├── service/                 # Core resolution (TODO)
│   ├── handlers/                # HTTP routes (TODO)
│   ├── config/                  # Config loading (✅ complete)
│   ├── cache/                   # In-memory cache (✅ complete)
│   ├── domains/                 # Domain registry (TODO)
│   ├── dialect/                 # SQL dialects (TODO)
│   ├── telemetry/               # Telemetry system (TODO)
│   └── governance/              # Rate limiting (TODO)
├── go.mod
└── README.md
```

## Performance Targets

- **Throughput:** 20K-25K req/s on 8 cores (vs Python: 600 req/s)
- **Latency:** p50 < 2ms, p99 < 10ms (vs Python: p50 ~15ms)
- **Memory:** 100-200MB (vs Python: ~500MB per process)

## API Equivalence

The Go implementation is designed to be 100% API-compatible with the Python resolver:

- Same HTTP routes (19 total)
- Same request/response JSON structure
- Same error messages and status codes
- Reads same YAML config files
- Can be swapped by changing Docker image only

## Development Roadmap

### Phase 1: MVP (Current - 1-2 weeks)
- [x] Moniker parser
- [x] Catalog types & registry
- [x] Basic config loading
- [x] In-memory cache
- [ ] Catalog loader (YAML)
- [ ] Core resolver service
- [ ] 4 critical routes: `/health`, `/resolve`, `/describe`, `/list`
- [ ] Contract tests

### Phase 2: Feature Completion (1 week)
- [ ] Remaining 15 routes
- [ ] Domain registry
- [ ] Access policy validation
- [ ] All error handlers
- [ ] Contract tests for all routes

### Phase 3: Production Hardening (1 week)
- [ ] Rate limiter
- [ ] Circuit breaker
- [ ] Structured logging
- [ ] Prometheus metrics
- [ ] Hot reload

### Phase 4: Performance Optimization (1-2 weeks)
- [ ] Goroutine pool for batch resolution
- [ ] Zero-allocation JSON encoding
- [ ] sync.Pool optimizations
- [ ] HTTP/2 support
- [ ] Load testing @ 20K req/s

## License

Same as parent project (see LICENSE in repo root)
