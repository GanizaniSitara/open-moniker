#!/usr/bin/env python3
"""
Cross-platform test bootstrap for Open Moniker.

Automatically:
1. Checks if services are running
2. Starts them if needed
3. Waits for health checks
4. Runs load tests
5. Opens dashboard
6. Displays live metrics

Works on Windows, Linux, and macOS.

Usage:
    python tests/bootstrap_test.py                  # Quick test (100 requests)
    python tests/bootstrap_test.py --full           # Full test (5000 requests)
    python tests/bootstrap_test.py --stress         # Stress test (30s sustained)
    python tests/bootstrap_test.py --no-start       # Don't start services
"""

import argparse
import os
import platform
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests not installed. Install with: pip install requests")
    sys.exit(1)


class Colors:
    """Cross-platform ANSI colors."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    @staticmethod
    def enabled():
        if platform.system() == "Windows":
            # Enable ANSI on Windows 10+
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        return sys.stdout.isatty()


def color(code: str, text: str) -> str:
    """Apply color if terminal supports it."""
    if Colors.enabled():
        return f"{code}{text}{Colors.RESET}"
    return text


def print_header(text: str):
    """Print a section header."""
    print()
    print(color(Colors.BOLD + Colors.BLUE, f"{'=' * 80}"))
    print(color(Colors.BOLD + Colors.BLUE, f"  {text}"))
    print(color(Colors.BOLD + Colors.BLUE, f"{'=' * 80}"))
    print()


def check_service_health(port: int, name: str, timeout: int = 2) -> bool:
    """Check if a service is healthy."""
    try:
        resp = requests.get(f"http://localhost:{port}/health", timeout=timeout)
        if resp.status_code == 200:
            print(f"  {color(Colors.GREEN, '✓')} {name} is healthy on port {port}")
            return True
        else:
            print(f"  {color(Colors.YELLOW, '⚠')} {name} returned status {resp.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"  {color(Colors.RED, '✗')} {name} not responding on port {port}")
        return False


def find_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root (no .git directory)")


def start_services():
    """Start local dev services using bootstrap.py."""
    print_header("Starting Services")

    repo_root = find_repo_root()
    bootstrap_script = repo_root / "deployments" / "local" / "bootstrap.py"

    if not bootstrap_script.exists():
        print(f"{color(Colors.RED, '❌')} Bootstrap script not found at {bootstrap_script}")
        return False

    print(f"  Using bootstrap script: {bootstrap_script}")
    print(f"  Starting dev environment...")

    try:
        # Determine Python command (python3 on Linux/Mac, python on Windows)
        python_cmd = "python3" if platform.system() != "Windows" else "python"

        # Stop any existing services first
        subprocess.run(
            [python_cmd, str(bootstrap_script), "stop", "dev"],
            cwd=bootstrap_script.parent,
            capture_output=True,
        )
        time.sleep(2)

        # Start services
        result = subprocess.run(
            [python_cmd, str(bootstrap_script), "dev"],
            cwd=bootstrap_script.parent,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"  {color(Colors.GREEN, '✓')} Services started successfully")
            print()
            print("  Waiting for services to be ready...")

            # Wait for services to be healthy
            max_wait = 30
            start = time.time()
            java_ok = False
            python_ok = False

            while (time.time() - start) < max_wait:
                if not java_ok:
                    java_ok = check_service_health(8054, "Java Resolver", timeout=1)
                if not python_ok:
                    python_ok = check_service_health(8052, "Python Admin", timeout=1)

                if java_ok and python_ok:
                    print()
                    print(f"  {color(Colors.GREEN, '✓')} All services ready!")
                    return True

                time.sleep(2)

            print()
            print(f"  {color(Colors.YELLOW, '⚠')} Some services did not become healthy in time")
            return java_ok  # At least Java resolver should be working

        else:
            print(f"  {color(Colors.RED, '❌')} Failed to start services")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"  {color(Colors.RED, '❌')} Error starting services: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")

    deps = {
        "aiohttp": "pip install aiohttp",
        "requests": "pip install requests",
    }

    all_ok = True
    for dep, install_cmd in deps.items():
        try:
            __import__(dep)
            print(f"  {color(Colors.GREEN, '✓')} {dep}")
        except ImportError:
            print(f"  {color(Colors.RED, '✗')} {dep} not installed")
            print(f"      Install with: {install_cmd}")
            all_ok = False

    if not all_ok:
        print()
        print(f"{color(Colors.YELLOW, '⚠ Missing dependencies. Install them first.')}")
        return False

    return True


def run_load_test(profile: str, requests: int = None, duration: int = None, workers: int = 10):
    """Run the load test."""
    print_header(f"Running Load Test ({profile} profile)")

    repo_root = find_repo_root()
    load_test_script = repo_root / "tests" / "load_test.py"

    if not load_test_script.exists():
        print(f"{color(Colors.RED, '❌')} Load test script not found")
        return False

    # Build command
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    cmd = [python_cmd, str(load_test_script), "--profile", profile, "--workers", str(workers)]

    if requests:
        cmd.extend(["--requests", str(requests)])
    elif duration:
        cmd.extend(["--duration", str(duration)])

    try:
        result = subprocess.run(cmd, cwd=repo_root)
        return result.returncode == 0
    except Exception as e:
        print(f"{color(Colors.RED, '❌')} Error running load test: {e}")
        return False


def open_dashboard():
    """Open the admin dashboard in the default browser."""
    print_header("Opening Dashboard")

    dashboard_url = "http://localhost:8052/dashboard"
    print(f"  Opening: {color(Colors.CYAN, dashboard_url)}")

    try:
        webbrowser.open(dashboard_url)
        print(f"  {color(Colors.GREEN, '✓')} Dashboard opened")
        print()
        print(f"  {color(Colors.CYAN, 'Watch the live telemetry charts while the load test runs!')}")
        return True
    except Exception as e:
        print(f"  {color(Colors.YELLOW, '⚠')} Could not open browser: {e}")
        print(f"  {color(Colors.CYAN, f'Manually open: {dashboard_url}')}")
        return False


def print_final_summary():
    """Print final summary and next steps."""
    print()
    print(color(Colors.BOLD + Colors.GREEN, "🎉 Testing Complete!"))
    print()
    print("Next steps:")
    print(f"  1. View dashboard: {color(Colors.CYAN, 'http://localhost:8052/dashboard')}")
    print(f"  2. Java resolver: {color(Colors.CYAN, 'http://localhost:8054/health')}")
    print(f"  3. Run custom test: {color(Colors.CYAN, 'python tests/load_test.py --help')}")
    print()
    print("To stop services:")
    print(f"  {color(Colors.CYAN, 'python deployments/local/bootstrap.py stop dev')}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform test bootstrap for Open Moniker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test (100 requests)",
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Full test (5000 requests)",
    )

    parser.add_argument(
        "--stress",
        action="store_true",
        help="Stress test (30 seconds sustained)",
    )

    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Don't start services (assume already running)",
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open dashboard in browser",
    )

    parser.add_argument(
        "--profile",
        choices=["read_heavy", "mixed", "catalog_heavy"],
        default="mixed",
        help="Traffic profile (default: mixed)",
    )

    args = parser.parse_args()

    # Determine test parameters
    if args.quick:
        requests = 100
        duration = None
        workers = 5
    elif args.full:
        requests = 5000
        duration = None
        workers = 20
    elif args.stress:
        requests = None
        duration = 30
        workers = 50
    else:
        # Default: moderate test
        requests = 1000
        duration = None
        workers = 10

    print()
    print(color(Colors.BOLD + Colors.MAGENTA, "╔═══════════════════════════════════════════════════════════════╗"))
    print(color(Colors.BOLD + Colors.MAGENTA, "║                                                               ║"))
    print(color(Colors.BOLD + Colors.MAGENTA, "║           Open Moniker Test Bootstrap                         ║"))
    print(color(Colors.BOLD + Colors.MAGENTA, "║           Cross-Platform Testing Suite                        ║"))
    print(color(Colors.BOLD + Colors.MAGENTA, "║                                                               ║"))
    print(color(Colors.BOLD + Colors.MAGENTA, "╚═══════════════════════════════════════════════════════════════╝"))
    print()
    print(f"Platform: {color(Colors.CYAN, platform.system())} {platform.release()}")
    print(f"Python: {color(Colors.CYAN, platform.python_version())}")
    print()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check if services are running
    print_header("Checking Services")
    java_running = check_service_health(8054, "Java Resolver")
    python_running = check_service_health(8052, "Python Admin")

    if not java_running and not args.no_start:
        if not start_services():
            print()
            print(f"{color(Colors.RED, '❌ Failed to start services. Aborting.')}")
            sys.exit(1)
    elif not java_running:
        print()
        print(f"{color(Colors.RED, '❌ Services not running and --no-start specified. Aborting.')}")
        print("Start services with: python deployments/local/bootstrap.py dev")
        sys.exit(1)

    # Open dashboard
    if not args.no_browser:
        open_dashboard()
        print()
        print(f"{color(Colors.YELLOW, '⏳')} Waiting 5 seconds for you to see the dashboard...")
        time.sleep(5)

    # Run load test
    success = run_load_test(args.profile, requests=requests, duration=duration, workers=workers)

    # Final summary
    print_final_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
