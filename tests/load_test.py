#!/usr/bin/env python3
"""
Multi-platform load testing and traffic simulation for Open Moniker.

Usage:
    python tests/load_test.py                    # Default: 1000 requests, 10 concurrent
    python tests/load_test.py --requests 5000    # Custom request count
    python tests/load_test.py --workers 50       # More concurrent workers
    python tests/load_test.py --duration 60      # Run for 60 seconds
    python tests/load_test.py --profile mixed    # Use mixed operation profile
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import aiohttp
except ImportError:
    print("❌ aiohttp not installed. Install with: pip install aiohttp")
    sys.exit(1)


# Test data profiles
TEST_PROFILES = {
    "read_heavy": {
        "description": "90% reads, 5% list, 5% describe",
        "operations": [
            ("resolve", 0.90),
            ("list", 0.05),
            ("describe", 0.05),
        ]
    },
    "mixed": {
        "description": "70% reads, 15% list, 10% describe, 5% lineage",
        "operations": [
            ("resolve", 0.70),
            ("list", 0.15),
            ("describe", 0.10),
            ("lineage", 0.05),
        ]
    },
    "catalog_heavy": {
        "description": "50% reads, 30% list, 20% describe",
        "operations": [
            ("resolve", 0.50),
            ("list", 0.30),
            ("describe", 0.20),
        ]
    },
}

# Sample monikers for realistic traffic
SAMPLE_MONIKERS = [
    "sales/customers@latest",
    "sales/orders@v1",
    "sales/products@v2",
    "analytics/revenue@latest",
    "analytics/user_metrics@v1",
    "marketing/campaigns@latest",
    "marketing/conversions@v1",
    "data_warehouse/fact_sales@v2",
    "data_warehouse/dim_customer@v1",
    "ops/logs@latest",
    "ops/metrics@v1",
    "ml/features@latest",
    "ml/predictions@v1",
    "finance/transactions@v2",
    "finance/reconciliation@v1",
    "hr/employees@latest",
    "hr/payroll@v1",
    "inventory/stock@latest",
    "inventory/warehouse@v1",
    "crm/contacts@v2",
]


class ColorOutput:
    """Cross-platform colored output."""
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
        """Check if colors should be enabled."""
        return sys.stdout.isatty() and sys.platform != "win32" or "ANSICON" in os.environ


class LoadTester:
    def __init__(
        self,
        base_url: str = "http://localhost:8054",
        profile: str = "mixed",
        verbose: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.profile = TEST_PROFILES[profile]
        self.verbose = verbose
        self.stats = defaultdict(lambda: {"success": 0, "error": 0, "latencies": []})
        self.start_time = None
        self.use_colors = ColorOutput.enabled()

    def _color(self, color: str, text: str) -> str:
        """Apply color if supported."""
        if self.use_colors:
            return f"{color}{text}{ColorOutput.RESET}"
        return text

    def _choose_operation(self) -> str:
        """Choose an operation based on profile weights."""
        rand = random.random()
        cumulative = 0.0
        for op, weight in self.profile["operations"]:
            cumulative += weight
            if rand <= cumulative:
                return op
        return self.profile["operations"][0][0]

    def _choose_moniker(self) -> str:
        """Choose a random moniker."""
        return random.choice(SAMPLE_MONIKERS)

    async def _make_request(
        self, session: aiohttp.ClientSession, operation: str
    ) -> Dict:
        """Make a single request."""
        moniker = self._choose_moniker()
        start = time.time()

        try:
            if operation == "resolve":
                url = f"{self.base_url}/resolve/{moniker}"
            elif operation == "describe":
                url = f"{self.base_url}/describe/{moniker}"
            elif operation == "list":
                path = moniker.split("/")[0]  # Just domain
                url = f"{self.base_url}/list/{path}"
            elif operation == "lineage":
                url = f"{self.base_url}/lineage/{moniker}"
            else:
                url = f"{self.base_url}/resolve/{moniker}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                latency = (time.time() - start) * 1000  # ms
                success = 200 <= resp.status < 300

                if self.verbose:
                    status_color = ColorOutput.GREEN if success else ColorOutput.RED
                    print(
                        f"{self._color(status_color, '●')} {operation:8s} {moniker:30s} "
                        f"{resp.status:3d} {latency:6.1f}ms"
                    )

                return {
                    "operation": operation,
                    "moniker": moniker,
                    "status": resp.status,
                    "latency_ms": latency,
                    "success": success,
                }

        except asyncio.TimeoutError:
            latency = (time.time() - start) * 1000
            if self.verbose:
                print(
                    f"{self._color(ColorOutput.RED, '●')} {operation:8s} {moniker:30s} "
                    f"TIMEOUT {latency:6.1f}ms"
                )
            return {
                "operation": operation,
                "moniker": moniker,
                "status": 0,
                "latency_ms": latency,
                "success": False,
                "error": "timeout",
            }

        except Exception as e:
            latency = (time.time() - start) * 1000
            if self.verbose:
                print(
                    f"{self._color(ColorOutput.RED, '●')} {operation:8s} {moniker:30s} "
                    f"ERROR {str(e)[:20]}"
                )
            return {
                "operation": operation,
                "moniker": moniker,
                "status": 0,
                "latency_ms": latency,
                "success": False,
                "error": str(e),
            }

    async def _worker(
        self, session: aiohttp.ClientSession, queue: asyncio.Queue, worker_id: int
    ):
        """Worker coroutine that processes requests from queue."""
        while True:
            try:
                operation = await asyncio.wait_for(queue.get(), timeout=1.0)
                if operation is None:  # Sentinel value
                    break

                result = await self._make_request(session, operation)

                # Update stats
                op = result["operation"]
                if result["success"]:
                    self.stats[op]["success"] += 1
                else:
                    self.stats[op]["error"] += 1
                self.stats[op]["latencies"].append(result["latency_ms"])

                queue.task_done()

            except asyncio.TimeoutError:
                continue

    async def run_fixed_count(self, total_requests: int, workers: int = 10):
        """Run a fixed number of requests."""
        print(f"\n{self._color(ColorOutput.BOLD, '🚀 Starting Load Test')}")
        print(f"Profile: {self._color(ColorOutput.CYAN, self.profile['description'])}")
        print(f"Target: {self._color(ColorOutput.CYAN, self.base_url)}")
        print(f"Requests: {self._color(ColorOutput.CYAN, str(total_requests))}")
        print(f"Workers: {self._color(ColorOutput.CYAN, str(workers))}")
        print()

        self.start_time = time.time()
        queue = asyncio.Queue()

        # Fill queue with operations
        for _ in range(total_requests):
            operation = self._choose_operation()
            await queue.put(operation)

        # Add sentinel values for workers
        for _ in range(workers):
            await queue.put(None)

        # Create session and workers
        connector = aiohttp.TCPConnector(limit=workers, limit_per_host=workers)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Test connectivity first
            try:
                async with session.get(
                    f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        print(
                            f"{self._color(ColorOutput.RED, '❌ Service not healthy')} "
                            f"(status {resp.status})"
                        )
                        return
                    print(f"{self._color(ColorOutput.GREEN, '✓ Service healthy')}\n")
            except Exception as e:
                print(f"{self._color(ColorOutput.RED, f'❌ Cannot connect: {e}')}")
                return

            # Start workers
            worker_tasks = [
                asyncio.create_task(self._worker(session, queue, i))
                for i in range(workers)
            ]

            # Wait for completion
            await queue.join()
            await asyncio.gather(*worker_tasks)

        self._print_summary()

    async def run_duration(self, duration_seconds: int, workers: int = 10):
        """Run for a fixed duration."""
        print(f"\n{self._color(ColorOutput.BOLD, '🚀 Starting Load Test')}")
        print(f"Profile: {self._color(ColorOutput.CYAN, self.profile['description'])}")
        print(f"Target: {self._color(ColorOutput.CYAN, self.base_url)}")
        print(f"Duration: {self._color(ColorOutput.CYAN, f'{duration_seconds}s')}")
        print(f"Workers: {self._color(ColorOutput.CYAN, str(workers))}")
        print()

        self.start_time = time.time()
        end_time = self.start_time + duration_seconds

        connector = aiohttp.TCPConnector(limit=workers, limit_per_host=workers)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Test connectivity
            try:
                async with session.get(
                    f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        print(
                            f"{self._color(ColorOutput.RED, '❌ Service not healthy')} "
                            f"(status {resp.status})"
                        )
                        return
                    print(f"{self._color(ColorOutput.GREEN, '✓ Service healthy')}\n")
            except Exception as e:
                print(f"{self._color(ColorOutput.RED, f'❌ Cannot connect: {e}')}")
                return

            # Run workers until time expires
            worker_tasks = []
            for i in range(workers):
                task = asyncio.create_task(
                    self._duration_worker(session, end_time, i)
                )
                worker_tasks.append(task)

            await asyncio.gather(*worker_tasks)

        self._print_summary()

    async def _duration_worker(
        self, session: aiohttp.ClientSession, end_time: float, worker_id: int
    ):
        """Worker that runs until end_time."""
        while time.time() < end_time:
            operation = self._choose_operation()
            result = await self._make_request(session, operation)

            # Update stats
            op = result["operation"]
            if result["success"]:
                self.stats[op]["success"] += 1
            else:
                self.stats[op]["error"] += 1
            self.stats[op]["latencies"].append(result["latency_ms"])

    def _print_summary(self):
        """Print test summary with statistics."""
        elapsed = time.time() - self.start_time
        total_requests = sum(
            s["success"] + s["error"] for s in self.stats.values()
        )
        total_success = sum(s["success"] for s in self.stats.values())
        total_errors = sum(s["error"] for s in self.stats.values())

        print(f"\n{self._color(ColorOutput.BOLD, '📊 Test Summary')}")
        print(f"{'─' * 80}")

        # Overall stats
        rps = total_requests / elapsed if elapsed > 0 else 0
        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0

        print(f"Duration:      {elapsed:.2f}s")
        print(f"Total Requests: {total_requests:,}")
        print(f"Successful:     {self._color(ColorOutput.GREEN, str(total_success))}")
        print(f"Failed:         {self._color(ColorOutput.RED, str(total_errors))}")
        print(f"Success Rate:   {success_rate:.2f}%")
        print(f"Throughput:     {self._color(ColorOutput.CYAN, f'{rps:.2f} req/s')}")
        print()

        # Per-operation stats
        print(f"{self._color(ColorOutput.BOLD, 'Per-Operation Breakdown:')}")
        print(
            f"{'Operation':<12} {'Requests':<12} {'Success':<10} {'Errors':<10} "
            f"{'Min':<8} {'Avg':<8} {'p95':<8} {'p99':<8} {'Max':<8}"
        )
        print(f"{'─' * 110}")

        for op in sorted(self.stats.keys()):
            data = self.stats[op]
            total = data["success"] + data["error"]
            latencies = sorted(data["latencies"])

            if not latencies:
                continue

            min_lat = min(latencies)
            max_lat = max(latencies)
            avg_lat = sum(latencies) / len(latencies)
            p95_lat = latencies[int(len(latencies) * 0.95)]
            p99_lat = latencies[int(len(latencies) * 0.99)]

            print(
                f"{op:<12} {total:<12,} {data['success']:<10,} {data['error']:<10,} "
                f"{min_lat:<8.1f} {avg_lat:<8.1f} {p95_lat:<8.1f} {p99_lat:<8.1f} {max_lat:<8.1f}"
            )

        print()
        print(f"{self._color(ColorOutput.GREEN, '✓ Load test complete!')}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Multi-platform load testing for Open Moniker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8054",
        help="Base URL of resolver service (default: http://localhost:8054)",
    )

    parser.add_argument(
        "--requests",
        type=int,
        help="Total number of requests to make (mutually exclusive with --duration)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Run test for N seconds (mutually exclusive with --requests)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)",
    )

    parser.add_argument(
        "--profile",
        choices=TEST_PROFILES.keys(),
        default="mixed",
        help="Traffic profile (default: mixed)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show each request",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.requests and args.duration:
        parser.error("--requests and --duration are mutually exclusive")

    if not args.requests and not args.duration:
        args.requests = 1000  # Default

    # Create tester
    tester = LoadTester(
        base_url=args.url,
        profile=args.profile,
        verbose=args.verbose,
    )

    # Run test
    try:
        if args.requests:
            asyncio.run(tester.run_fixed_count(args.requests, args.workers))
        else:
            asyncio.run(tester.run_duration(args.duration, args.workers))
    except KeyboardInterrupt:
        print(f"\n\n{tester._color(ColorOutput.YELLOW, '⚠ Test interrupted by user')}")
        if tester.start_time:
            tester._print_summary()


if __name__ == "__main__":
    main()
