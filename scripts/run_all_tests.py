"""Run the full Open Moniker test suite.

Usage:
    python scripts/run_all_tests.py            # run everything
    python scripts/run_all_tests.py --python    # Python tests only
    python scripts/run_all_tests.py --mcp       # MCP SSE tests only
    python scripts/run_all_tests.py --go        # Go resolver tests only
    python scripts/run_all_tests.py --java      # Java resolver tests only
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
SERVER_PORT = 8060


class colours:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def _banner(label: str) -> None:
    print(f"\n{colours.BOLD}{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}{colours.NC}\n")


def _run(cmd: list[str], cwd: str | Path | None = None, timeout: int = 300) -> bool:
    """Run a command and return True on success."""
    try:
        result = subprocess.run(cmd, cwd=cwd or REPO_ROOT, timeout=timeout)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"{colours.RED}TIMEOUT{colours.NC} after {timeout}s")
        return False
    except FileNotFoundError:
        print(f"{colours.RED}NOT FOUND{colours.NC} {cmd[0]}")
        return False


def _wait_for_server(port: int, retries: int = 30) -> bool:
    """Poll the health endpoint until the server is ready."""
    import urllib.request
    import urllib.error

    url = f"http://127.0.0.1:{port}/health"
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1)
    return False


def run_python_tests() -> bool:
    _banner("Python unit & integration tests")
    return _run([
        PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short", "-x",
        "--ignore=tests/test_mcp.py",
    ])


def run_mcp_tests() -> bool:
    _banner("MCP SSE tests")

    # Start server
    print("Starting moniker service...")
    server = subprocess.Popen(
        [PYTHON, "start.py"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        if not _wait_for_server(SERVER_PORT):
            print(f"{colours.RED}Server failed to start{colours.NC}")
            return False

        print(f"Server ready on port {SERVER_PORT}")
        env = {**os.environ, "MCP_URL": f"http://127.0.0.1:{SERVER_PORT}/mcp/sse"}
        result = subprocess.run(
            [PYTHON, "-m", "pytest", "tests/test_mcp.py", "-v", "--tb=short"],
            cwd=REPO_ROOT,
            env=env,
        )
        return result.returncode == 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def run_go_tests() -> bool:
    _banner("Go resolver tests")
    go_dir = REPO_ROOT / "resolver-go"
    if not go_dir.exists():
        print("SKIP (resolver-go/ not found)")
        return True
    if not shutil.which("go"):
        print("SKIP (go not installed)")
        return True
    return _run(["go", "test", "./...", "-v", "-race"], cwd=go_dir)


def run_java_tests() -> bool:
    _banner("Java resolver tests")
    java_dir = REPO_ROOT / "resolver-java"
    mvnw = java_dir / "mvnw.cmd" if sys.platform == "win32" else java_dir / "mvnw"
    if not java_dir.exists():
        print("SKIP (resolver-java/ not found)")
        return True
    if not mvnw.exists():
        print("SKIP (mvnw not found)")
        return True
    return _run([str(mvnw), "test", "-q"], cwd=java_dir, timeout=600)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Open Moniker test suite")
    parser.add_argument("--python", action="store_true", help="Python tests only")
    parser.add_argument("--mcp", action="store_true", help="MCP SSE tests only")
    parser.add_argument("--go", action="store_true", help="Go tests only")
    parser.add_argument("--java", action="store_true", help="Java tests only")
    args = parser.parse_args()

    run_all = not (args.python or args.mcp or args.go or args.java)

    results: dict[str, bool] = {}

    if run_all or args.python:
        results["Python"] = run_python_tests()
    if run_all or args.mcp:
        results["MCP"] = run_mcp_tests()
    if run_all or args.go:
        results["Go"] = run_go_tests()
    if run_all or args.java:
        results["Java"] = run_java_tests()

    # Summary
    print(f"\n{colours.BOLD}{'=' * 50}")
    print("  Results")
    print(f"{'=' * 50}{colours.NC}")
    all_pass = True
    for name, passed in results.items():
        icon = f"{colours.GREEN}PASS{colours.NC}" if passed else f"{colours.RED}FAIL{colours.NC}"
        print(f"  {icon}  {name}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print(f"{colours.GREEN}{colours.BOLD}All tests passed!{colours.NC}")
    else:
        print(f"{colours.RED}{colours.BOLD}Some tests failed.{colours.NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
