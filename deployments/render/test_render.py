#!/usr/bin/env python3
"""
Comprehensive Test Suite for Render.com Deployment

Tests all services end-to-end on Render.
"""
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

class RenderTester:
    def __init__(self, python_url, java_url):
        self.python_url = python_url.rstrip('/')
        self.java_url = java_url.rstrip('/')
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def http_get(self, url, timeout=10):
        """Make HTTP GET request."""
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                data = response.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "detail": str(e.read())}
        except Exception as e:
            return {"error": "Request failed", "detail": str(e)}
    
    def test(self, name, fn):
        """Run a test."""
        print(f"\n[TEST] {name}")
        try:
            fn()
            print(f"   ✅ PASS")
            self.passed += 1
            self.tests.append((name, True, None))
        except AssertionError as e:
            print(f"   ❌ FAIL: {e}")
            self.failed += 1
            self.tests.append((name, False, str(e)))
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.failed += 1
            self.tests.append((name, False, str(e)))
    
    def summary(self):
        """Print summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        print("=" * 70)
        
        if self.failed > 0:
            print("\n❌ Failed tests:")
            for name, passed, error in self.tests:
                if not passed:
                    print(f"   - {name}")
                    if error:
                        print(f"     Error: {error}")
        
        print()
        return 0 if self.failed == 0 else 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python test_render.py <python_url> <java_url>")
        print("Example: python test_render.py https://moniker-admin.onrender.com https://moniker-resolver-java.onrender.com")
        sys.exit(1)
    
    python_url = sys.argv[1]
    java_url = sys.argv[2]
    
    tester = RenderTester(python_url, java_url)
    
    print("=" * 70)
    print("RENDER.COM DEPLOYMENT - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"Python URL: {python_url}")
    print(f"Java URL: {java_url}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Python health
    def test_python_health():
        data = tester.http_get(f"{python_url}/health")
        assert "error" not in data, f"Health check failed: {data.get('error')}"
        assert data.get("status") == "healthy", f"Expected healthy, got {data.get('status')}"
        assert "service" in data, "Missing service name"
        print(f"      Catalog nodes: {data.get('catalog_counts', {}).get('active', 'N/A')}")
    
    tester.test("Python Health Check", test_python_health)
    
    # Test 2: Java health
    def test_java_health():
        data = tester.http_get(f"{java_url}/health")
        assert "error" not in data, f"Health check failed: {data.get('error')}"
        assert data.get("status") == "healthy", f"Expected healthy, got {data.get('status')}"
        assert data.get("catalog_nodes", 0) > 0, "No catalog nodes loaded"
        print(f"      Catalog nodes: {data.get('catalog_nodes')}")
    
    tester.test("Java Health Check", test_java_health)
    
    # Test 3: Python parent node
    def test_python_parent():
        data = tester.http_get(f"{python_url}/resolve/reference")
        assert "error" not in data, f"Resolve failed: {data.get('error')}"
        assert data.get("type") == "parent", f"Expected parent, got {data.get('type')}"
        assert "children" in data, "Missing children field"
        assert len(data.get("children", [])) > 0, "No children returned"
        print(f"      Children: {data.get('children')}")
    
    tester.test("Python Parent Node (reference)", test_python_parent)
    
    # Test 4: Python leaf node
    def test_python_leaf():
        data = tester.http_get(f"{python_url}/resolve/prices.equity/AAPL@latest")
        assert "error" not in data, f"Resolve failed: {data.get('error')}"
        assert data.get("type") == "leaf", f"Expected leaf, got {data.get('type')}"
        assert "source_type" in data, "Missing source_type"
        assert "connection" in data, "Missing connection"
        print(f"      Source: {data.get('source_type')}")
    
    tester.test("Python Leaf Node (prices.equity)", test_python_leaf)
    
    # Test 5: Java parent node
    def test_java_parent():
        data = tester.http_get(f"{java_url}/resolve/reference")
        assert "error" not in data, f"Resolve failed: {data.get('error')}"
        assert data.get("type") == "parent", f"Expected parent, got {data.get('type')}"
        assert "children" in data, "Missing children field"
        assert len(data.get("children", [])) > 0, "No children returned"
        print(f"      Children: {len(data.get('children'))} nodes")
    
    tester.test("Java Parent Node (reference)", test_java_parent)
    
    # Test 6: Java leaf node
    def test_java_leaf():
        data = tester.http_get(f"{java_url}/resolve/commodities.crypto")
        assert "error" not in data, f"Resolve failed: {data.get('error')}"
        assert data.get("type") == "leaf", f"Expected leaf, got {data.get('type')}"
        assert "sourceType" in data or "source_type" in data, "Missing sourceType"
        print(f"      Source: {data.get('sourceType', data.get('source_type'))}")
    
    tester.test("Java Leaf Node (commodities.crypto)", test_java_leaf)
    
    # Test 7: Python catalog
    def test_python_catalog():
        data = tester.http_get(f"{python_url}/catalog")
        assert "error" not in data, f"Catalog failed: {data.get('error')}"
        assert "paths" in data, "Missing paths in catalog"
        assert len(data.get("paths", [])) > 0, "Catalog is empty"
        print(f"      Total paths: {len(data.get('paths'))}")
    
    tester.test("Python Catalog Endpoint", test_python_catalog)
    
    # Test 8: Java catalog
    def test_java_catalog():
        data = tester.http_get(f"{java_url}/catalog?limit=5")
        assert "error" not in data, f"Catalog failed: {data.get('error')}"
        assert "nodes" in data, "Missing nodes in catalog"
        assert data.get("total", 0) > 0, "Catalog is empty"
        print(f"      Total nodes: {data.get('total')}")
    
    tester.test("Java Catalog Endpoint", test_java_catalog)
    
    # Test 9: Python docs
    def test_python_docs():
        try:
            with urllib.request.urlopen(f"{python_url}/docs", timeout=10) as response:
                html = response.read().decode()
                assert "swagger" in html.lower(), "Missing Swagger UI"
                print(f"      Swagger UI loaded")
        except Exception as e:
            raise AssertionError(f"Failed to load docs: {e}")
    
    tester.test("Python Swagger Docs", test_python_docs)
    
    # Test 10: Load test
    def test_load():
        print("      Generating 50 test requests...")
        success = 0
        failed = 0
        for i in range(50):
            data = tester.http_get(f"{java_url}/resolve/commodities.crypto", timeout=5)
            if "error" not in data:
                success += 1
            else:
                failed += 1
        
        assert success > 0, "All requests failed"
        print(f"      Success: {success}/50, Failed: {failed}/50")
        assert failed < 10, f"Too many failures: {failed}"
    
    tester.test("Load Test (50 requests)", test_load)
    
    return tester.summary()

if __name__ == "__main__":
    sys.exit(main())
