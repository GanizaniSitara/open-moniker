#!/bin/bash
# Benchmark script to compare Python and Go resolvers

set -e

PYTHON_PORT=8051
GO_PORT=8053

echo "================================================================"
echo "  Moniker Resolver Benchmark: Python vs Go"
echo "================================================================"
echo ""

# Check both servers are running
if ! curl -s http://localhost:$PYTHON_PORT/health > /dev/null 2>&1; then
    echo "❌ Python resolver not running on port $PYTHON_PORT"
    exit 1
fi

if ! curl -s http://localhost:$GO_PORT/health > /dev/null 2>&1; then
    echo "❌ Go resolver not running on port $GO_PORT"
    exit 1
fi

echo "✅ Both resolvers are running"
echo ""

# Test 1: Health endpoint latency
echo "=== Test 1: Health Endpoint (Sequential, 100 requests) ==="
echo -n "Python: "
time (for i in {1..100}; do curl -s http://localhost:$PYTHON_PORT/health > /dev/null; done) 2>&1 | grep real

echo -n "Go:     "
time (for i in {1..100}; do curl -s http://localhost:$GO_PORT/health > /dev/null; done) 2>&1 | grep real
echo ""

# Test 2: Concurrent health endpoint
echo "=== Test 2: Health Endpoint (Concurrent, 200 requests) ==="
echo -n "Python: "
time (for i in {1..200}; do curl -s http://localhost:$PYTHON_PORT/health > /dev/null & done; wait) 2>&1 | grep real

echo -n "Go:     "
time (for i in {1..200}; do curl -s http://localhost:$GO_PORT/health > /dev/null & done; wait) 2>&1 | grep real
echo ""

# Test 3: Resolve endpoint latency
echo "=== Test 3: Resolve Endpoint (Sequential, 50 requests) ==="
TEST_PATH="benchmarks.constituents/SP500/20260101"

echo -n "Python: "
time (for i in {1..50}; do curl -s "http://localhost:$PYTHON_PORT/resolve/$TEST_PATH" > /dev/null; done) 2>&1 | grep real

echo -n "Go:     "
time (for i in {1..50}; do curl -s "http://localhost:$GO_PORT/resolve/$TEST_PATH" > /dev/null; done) 2>&1 | grep real
echo ""

# Test 4: Response comparison
echo "=== Test 4: Response Comparison ==="
echo "Python response:"
curl -s "http://localhost:$PYTHON_PORT/resolve/$TEST_PATH" | jq -c '{moniker, path, source_type: .source.source_type, ownership: {owner: .ownership.accountable_owner}}'

echo "Go response:"
curl -s "http://localhost:$GO_PORT/resolve/$TEST_PATH" | jq -c '{moniker, path, source_type: .source.source_type, ownership: {owner: .ownership.accountable_owner}}'
echo ""

# Test 5: Catalog stats
echo "=== Test 5: Catalog Statistics ==="
echo "Python:"
curl -s "http://localhost:$PYTHON_PORT/health" | jq '.catalog'

echo "Go:"
curl -s "http://localhost:$GO_PORT/health" | jq '.catalog'
echo ""

echo "================================================================"
echo "  Benchmark Complete"
echo "================================================================"
