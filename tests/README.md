# Open Moniker Test Suite

Cross-platform testing tools for Open Moniker. Works on **Windows**, **Linux**, and **macOS**.

## Quick Start

### Option 1: Automated Testing (Recommended)

The bootstrap script handles everything:

```bash
# Quick test (100 requests)
python tests/bootstrap_test.py --quick

# Full test (5000 requests, 20 workers)
python tests/bootstrap_test.py --full

# Stress test (30 seconds sustained, 50 workers)
python tests/bootstrap_test.py --stress

# Custom test
python tests/bootstrap_test.py  # Default: 1000 requests, 10 workers
```

The bootstrap script will:
1. ✅ Check dependencies
2. ✅ Check if services are running
3. ✅ Start them if needed (using `deployments/local/bootstrap.py`)
4. ✅ Wait for health checks
5. ✅ Open dashboard in browser
6. ✅ Run load test
7. ✅ Display comprehensive statistics

### Option 2: Manual Testing

If services are already running:

```bash
# Run load test manually
python tests/load_test.py --requests 1000 --workers 10

# Different profiles
python tests/load_test.py --profile read_heavy --requests 5000
python tests/load_test.py --profile catalog_heavy --duration 60

# Verbose mode (show each request)
python tests/load_test.py --requests 100 --verbose
```

## Prerequisites

Install dependencies (one-time setup):

```bash
# On all platforms
pip install aiohttp requests

# Or use requirements
pip install -r tests/requirements.txt
```

## Traffic Profiles

### `read_heavy` (Default for Quick Tests)
- 90% resolve operations
- 5% list operations
- 5% describe operations
- **Use case:** Typical production traffic

### `mixed` (Default)
- 70% resolve operations
- 15% list operations
- 10% describe operations
- 5% lineage operations
- **Use case:** Balanced testing

### `catalog_heavy`
- 50% resolve operations
- 30% list operations
- 20% describe operations
- **Use case:** Catalog exploration workloads

## Test Scripts

### `bootstrap_test.py`

**Full automation script** - starts services, opens dashboard, runs tests.

```bash
python tests/bootstrap_test.py [options]
```

**Options:**
- `--quick` - Quick test (100 requests, 5 workers)
- `--full` - Full test (5000 requests, 20 workers)
- `--stress` - Stress test (30s duration, 50 workers)
- `--no-start` - Don't start services (assume already running)
- `--no-browser` - Don't open dashboard
- `--profile PROFILE` - Traffic profile (read_heavy, mixed, catalog_heavy)

**Example output:**
```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           Open Moniker Test Bootstrap                         ║
║           Cross-Platform Testing Suite                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Platform: Linux 6.17.0-14-generic
Python: 3.13.1

===============================================================================
  Checking Dependencies
===============================================================================

  ✓ aiohttp
  ✓ requests

===============================================================================
  Checking Services
===============================================================================

  ✓ Java Resolver is healthy on port 8054
  ✓ Python Admin is healthy on port 8052

===============================================================================
  Opening Dashboard
===============================================================================

  Opening: http://localhost:8052/dashboard
  ✓ Dashboard opened

  Watch the live telemetry charts while the load test runs!

===============================================================================
  Running Load Test (mixed profile)
===============================================================================

🚀 Starting Load Test
Profile: 70% reads, 15% list, 10% describe, 5% lineage
Target: http://localhost:8054
Requests: 1000
Workers: 10

✓ Service healthy

📊 Test Summary
────────────────────────────────────────────────────────────────────────────────
Duration:      12.34s
Total Requests: 1,000
Successful:     998
Failed:         2
Success Rate:   99.80%
Throughput:     81.03 req/s

Per-Operation Breakdown:
Operation    Requests     Success    Errors     Min      Avg      p95      p99      Max
──────────────────────────────────────────────────────────────────────────────────────────────
describe     98           98         0          5.2      12.3     18.5     22.1     28.3
lineage      52           51         1          6.1      14.2     21.3     25.8     31.2
list         151          151        0          4.8      11.8     17.2     20.5     26.7
resolve      699          698        1          3.9      10.5     15.8     19.3     25.1

✓ Load test complete!

🎉 Testing Complete!

Next steps:
  1. View dashboard: http://localhost:8052/dashboard
  2. Java resolver: http://localhost:8054/health
  3. Run custom test: python tests/load_test.py --help

To stop services:
  python deployments/local/bootstrap.py stop dev
```

### `load_test.py`

**Flexible load testing tool** - run custom tests against any endpoint.

```bash
python tests/load_test.py [options]
```

**Options:**
- `--url URL` - Target URL (default: http://localhost:8054)
- `--requests N` - Total requests to make
- `--duration N` - Run for N seconds (mutually exclusive with --requests)
- `--workers N` - Concurrent workers (default: 10)
- `--profile PROFILE` - Traffic profile
- `--verbose` - Show each request

**Examples:**

```bash
# Quick test
python tests/load_test.py --requests 100 --workers 5

# Sustained load
python tests/load_test.py --duration 60 --workers 20

# Heavy load
python tests/load_test.py --requests 10000 --workers 50 --profile read_heavy

# Watch requests in real-time
python tests/load_test.py --requests 100 --verbose

# Test remote instance
python tests/load_test.py --url https://moniker.example.com --requests 1000
```

**Sample output (verbose mode):**
```
● resolve   sales/customers@latest          200   8.2ms
● describe  analytics/revenue@latest        200  12.5ms
● list      sales                           200  15.3ms
● resolve   ml/features@latest              200   6.8ms
● lineage   data_warehouse/fact_sales@v2    200  18.7ms
```

## Windows-Specific Notes

### PowerShell
```powershell
# Run bootstrap test
python tests\bootstrap_test.py --quick

# Run load test
python tests\load_test.py --requests 1000
```

### Command Prompt
```cmd
REM Run bootstrap test
python tests\bootstrap_test.py --quick

REM Run load test
python tests\load_test.py --requests 1000
```

### ANSI Colors on Windows

The scripts automatically enable ANSI color support on Windows 10+. If colors don't work, update your terminal or use Windows Terminal.

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install aiohttp requests
          pip install -r tests/requirements.txt

      - name: Run tests
        run: python tests/bootstrap_test.py --quick --no-browser
```

### Docker Testing

```bash
# Build test container
docker build -t moniker-test -f tests/Dockerfile .

# Run tests in container
docker run --rm moniker-test python tests/bootstrap_test.py --quick --no-browser
```

## Performance Benchmarks

Typical performance on common hardware:

### Development Machine (4-core, 8GB RAM)
- **Throughput:** 500-1,000 req/s (Java resolver)
- **Latency p95:** 15-25ms
- **Latency p99:** 25-40ms

### Production (t3.medium, 2 vCPU, 4GB RAM)
- **Throughput:** 8,000-10,000 req/s (Java resolver)
- **Latency p95:** 8-15ms
- **Latency p99:** 15-25ms

### Production (6 resolvers, multi-region)
- **Throughput:** 40,000+ req/s combined
- **Latency p95:** 10-20ms
- **Latency p99:** 20-35ms

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
# Linux/Mac:
lsof -i :8054
lsof -i :8052

# Windows:
netstat -ano | findstr :8054
netstat -ano | findstr :8052

# Force stop and restart
python deployments/local/bootstrap.py stop dev
python deployments/local/bootstrap.py dev
```

### Connection refused

```bash
# Check if services are actually running
python deployments/local/bootstrap.py status

# Check service logs
tail -f deployments/local/dev-java.log
tail -f deployments/local/dev-python.log

# On Windows:
type deployments\local\dev-java.log
type deployments\local\dev-python.log
```

### Import errors

```bash
# Install dependencies
pip install aiohttp requests

# Or use the requirements file
pip install -r tests/requirements.txt
```

### Dashboard not opening

The dashboard should open automatically. If not:
1. Manually open: http://localhost:8052/dashboard
2. Check Python admin service is running: http://localhost:8052/health
3. Check browser console for JavaScript errors

## File Structure

```
tests/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── bootstrap_test.py      # Full automation script
├── load_test.py          # Flexible load testing tool
├── stress/               # Stress testing utilities
│   ├── gen_catalog.py    # Generate large catalogs
│   └── harness.py        # Test harness utilities
└── fixtures/             # Test data (optional)
    └── sample_monikers.json
```

## Next Steps

1. **Run the quick test:**
   ```bash
   python tests/bootstrap_test.py --quick
   ```

2. **Watch the dashboard** while the test runs to see live telemetry

3. **Run stress tests** to find the limits:
   ```bash
   python tests/bootstrap_test.py --stress
   ```

4. **Customize tests** for your use case:
   ```bash
   python tests/load_test.py --help
   ```

5. **Integrate with CI/CD** using the examples above

## Contributing

When adding new tests:
1. Ensure cross-platform compatibility (test on Windows + Linux)
2. Use `platform.system()` to detect OS
3. Use `Path` objects instead of string paths
4. Avoid shell-specific commands
5. Add color output for better UX
6. Include comprehensive `--help` text

## Support

- 📖 Main docs: `/docs/`
- 🚀 Deployment: `/deployments/README.md`
- 🐛 Issues: GitHub Issues
- 💬 Questions: GitHub Discussions
