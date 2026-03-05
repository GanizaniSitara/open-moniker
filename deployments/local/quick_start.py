#!/usr/bin/env python3
"""
Quick Start Script - Bootstrap, Test, and Verify Open Moniker
==============================================================

This script:
1. Starts the dev environment (Python app + Java resolver)
2. Runs health checks to confirm services are up
3. Generates test traffic to populate telemetry
4. Verifies telemetry is working
5. Opens the dashboard in your browser

Usage:
    python3 quick_start.py              # Start, test, and verify
    python3 quick_start.py --stop       # Stop all services
    python3 quick_start.py --no-browser # Don't open browser
"""

import argparse
import subprocess
import sys
import time
import urllib.request
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(number: int, text: str):
    """Print a step number and description."""
    print(f"\n[{number}] {text}")


def check_health(port: int, service_name: str, timeout: int = 30) -> bool:
    """Check if a service is healthy."""
    url = f"http://localhost:{port}/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read())
                if data.get("status") == "healthy":
                    return True
        except Exception:
            pass
        time.sleep(1)

    return False


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"   ✅ {description}")
            return True
        else:
            print(f"   ❌ {description} failed")
            if result.stderr:
                print(f"      {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ {description} failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Quick start script for Open Moniker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--stop", action="store_true", help="Stop all services and exit")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--skip-load-test", action="store_true", help="Skip load test")
    args = parser.parse_args()

    print_header("🚀 Open Moniker Quick Start")

    # Stop services if requested
    if args.stop:
        print_step(1, "Stopping services...")
        subprocess.run([sys.executable, "bootstrap.py", "stop", "dev"], cwd=SCRIPT_DIR)
        print("\n✅ Services stopped")
        return 0

    # Step 1: Start services
    print_step(1, "Starting services (Python app + Java resolver)...")
    result = subprocess.run(
        [sys.executable, "bootstrap.py", "dev"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("   ❌ Failed to start services")
        print(result.stdout)
        print(result.stderr)
        return 1

    print(result.stdout)

    # Step 2: Health checks
    print_step(2, "Running health checks...")

    python_healthy = check_health(8050, "Python app", timeout=30)
    if python_healthy:
        print("   ✅ Python app is healthy (http://localhost:8050)")
    else:
        print("   ❌ Python app health check failed")
        return 1

    java_healthy = check_health(8054, "Java resolver", timeout=30)
    if java_healthy:
        print("   ✅ Java resolver is healthy (http://localhost:8054)")
    else:
        print("   ❌ Java resolver health check failed")
        return 1

    # Step 3: Generate test traffic
    if not args.skip_load_test:
        print_step(3, "Generating test traffic (15 seconds, 10 RPS)...")
        load_test_script = PROJECT_ROOT / "tests" / "load_tester.py"

        if not load_test_script.exists():
            print("   ⚠️  Load tester not found, skipping...")
        else:
            result = subprocess.run(
                [sys.executable, str(load_test_script), "--duration", "15", "--concurrent", "5", "--rps", "10"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Parse summary
                lines = result.stdout.split("\n")
                for i, line in enumerate(lines):
                    if "Test Summary" in line:
                        summary = "\n".join(lines[i+2:i+9])
                        print("   ✅ Load test completed:")
                        print("      " + "\n      ".join(summary.split("\n")))
                        break
            else:
                print("   ⚠️  Load test had issues (continuing anyway)")

    # Step 4: Verify telemetry
    print_step(4, "Verifying telemetry...")

    try:
        # Check WebSocket endpoint exists
        url = "http://localhost:8050/telemetry"
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                print("   ✅ Telemetry page is accessible")
            else:
                print("   ⚠️  Telemetry page returned status:", response.status)
    except Exception as e:
        print(f"   ❌ Telemetry check failed: {e}")

    # Step 5: Summary and next steps
    print_header("✅ Quick Start Complete!")

    print("\n📊 Services Running:")
    print("   • Python App:      http://localhost:8050/")
    print("   • Live Telemetry:  http://localhost:8050/telemetry")
    print("   • Swagger Docs:    http://localhost:8050/docs")
    print("   • Java Resolver:   http://localhost:8054/health")

    print("\n🧪 Test Commands:")
    print("   # Generate more traffic")
    print("   python3 tests/load_tester.py --duration 60 --rps 20")
    print()
    print("   # Test a resolve query")
    print("   curl http://localhost:8054/resolve/commodities/crypto@latest")

    print("\n🛑 Stop Services:")
    print("   python3 deployments/local/quick_start.py --stop")

    # Open browser
    if not args.no_browser:
        print("\n🌐 Opening dashboard in browser...")
        try:
            import webbrowser
            webbrowser.open("http://localhost:8050/telemetry")
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️  Could not open browser: {e}")

    print("\n" + "=" * 70)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
