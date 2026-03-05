#!/usr/bin/env python3
"""
Comprehensive Test Suite for Open Moniker
==========================================

Tests all components end-to-end:
1. Service startup (Python + Java + Go)
2. Health checks
3. Resolution endpoints
4. Telemetry flow
5. Dashboard functionality
"""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str, fn):
        """Run a test and track results."""
        print(f"\n[TEST] {name}")
        try:
            fn()
            print(f"   ✅ PASS")
            self.passed += 1
            self.tests.append((name, True))
        except AssertionError as e:
            print(f"   ❌ FAIL: {e}")
            self.failed += 1
            self.tests.append((name, False))
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.failed += 1
            self.tests.append((name, False))

    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        print("=" * 70)

        if self.failed > 0:
            print("\nFailed tests:")
            for name, passed in self.tests:
                if not passed:
                    print(f"   ❌ {name}")

        print()
        return 0 if self.failed == 0 else 1


def http_get(url: str, timeout: int = 5):
    """Make HTTP GET request and return JSON."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = response.read()
        return json.loads(data) if data else {}


def main():
    runner = TestRunner()

    print("=" * 70)
    print("OPEN MONIKER - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # Test 1: Python app health
    def test_python_health():
        data = http_get("http://localhost:8050/health")
        assert data.get("status") == "healthy", f"Expected healthy, got {data.get('status')}"
        assert "service" in data, "Missing service name"

    runner.test("Python App Health Check", test_python_health)

    # Test 2: Java resolver health
    def test_java_health():
        data = http_get("http://localhost:8054/health")
        assert data.get("status") == "healthy", f"Expected healthy, got {data.get('status')}"
        assert data.get("catalog_nodes", 0) > 0, "No catalog nodes loaded"

    runner.test("Java Resolver Health Check", test_java_health)

    # Test 3: Go resolver health (if running)
    def test_go_health():
        try:
            data = http_get("http://localhost:8053/health")
            assert data.get("status") == "healthy", f"Expected healthy, got {data.get('status')}"
        except Exception:
            # Go resolver might not be running, that's ok
            raise AssertionError("Go resolver not running (optional)")

    runner.test("Go Resolver Health Check (optional)", test_go_health)

    # Test 4: Python resolve endpoint
    def test_python_resolve():
        data = http_get("http://localhost:8050/resolve/prices.equity/AAPL@latest")
        assert "moniker" in data, "Missing moniker in response"
        assert "source_type" in data, "Missing source_type in response"

    runner.test("Python Resolve Endpoint", test_python_resolve)

    # Test 5: Java resolve endpoint
    def test_java_resolve():
        data = http_get("http://localhost:8054/resolve/commodities.crypto")
        assert "moniker" in data, "Missing moniker in response"
        assert "sourceType" in data or "source_type" in data, "Missing source_type in response"

    runner.test("Java Resolve Endpoint", test_java_resolve)

    # Test 6: Catalog endpoint
    def test_catalog():
        data = http_get("http://localhost:8050/catalog")
        assert "paths" in data, "Missing paths in catalog"
        assert len(data["paths"]) > 0, "Catalog is empty"

    runner.test("Catalog Endpoint", test_catalog)

    # Test 7: Dashboard API
    def test_dashboard_api():
        data = http_get("http://localhost:8050/dashboard/api/stats")
        assert "catalog" in data, "Missing catalog stats"
        # Note: resolvers might be empty if no telemetry yet

    runner.test("Dashboard API", test_dashboard_api)

    # Test 8: Landing page
    def test_landing_page():
        with urllib.request.urlopen("http://localhost:8050/", timeout=5) as response:
            html = response.read().decode()
            assert "Open Moniker" in html, "Missing project name in landing page"
            assert "Live Telemetry" in html, "Missing Live Telemetry link"

    runner.test("Landing Page", test_landing_page)

    # Test 9: Telemetry page
    def test_telemetry_page():
        with urllib.request.urlopen("http://localhost:8050/telemetry", timeout=5) as response:
            html = response.read().decode()
            assert "Live Telemetry" in html, "Missing telemetry header"
            assert "WebSocket" in html or "ws://" in html, "Missing WebSocket code"

    runner.test("Telemetry Page", test_telemetry_page)

    # Test 10: Config UI
    def test_config_ui():
        with urllib.request.urlopen("http://localhost:8050/config/ui", timeout=5) as response:
            html = response.read().decode()
            assert response.status == 200, f"Config UI returned {response.status}"

    runner.test("Config UI", test_config_ui)

    # Test 11: Generate traffic and check telemetry
    def test_telemetry_flow():
        print("      Generating 20 test requests...")
        for i in range(20):
            try:
                http_get("http://localhost:8054/resolve/commodities.crypto", timeout=2)
            except:
                pass

        print("      Waiting for telemetry to flush (6 seconds)...")
        time.sleep(6)

        # Check if telemetry was recorded
        result = subprocess.run(
            ["python3", "-c", """
import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('/home/user/open-moniker-svc/deployments/local/dev/telemetry.db') as conn:
        cursor = await conn.execute('SELECT COUNT(*) FROM access_log')
        count = (await cursor.fetchone())[0]
        print(count)

asyncio.run(check())
"""],
            capture_output=True,
            text=True
        )

        count = int(result.stdout.strip())
        assert count > 0, f"No telemetry records found (count: {count})"
        print(f"      Found {count} telemetry records")

    runner.test("Telemetry Flow (Generate + Verify)", test_telemetry_flow)

    # Test 12: Swagger docs
    def test_swagger():
        with urllib.request.urlopen("http://localhost:8050/docs", timeout=5) as response:
            html = response.read().decode()
            assert "swagger" in html.lower(), "Missing Swagger UI"

    runner.test("Swagger Documentation", test_swagger)

    # Test 13: OpenAPI spec
    def test_openapi():
        data = http_get("http://localhost:8050/openapi.json")
        assert "openapi" in data, "Missing OpenAPI version"
        assert "paths" in data, "Missing API paths"
        assert len(data["paths"]) > 0, "No API paths defined"

    runner.test("OpenAPI Specification", test_openapi)

    return runner.summary()


if __name__ == "__main__":
    sys.exit(main())
