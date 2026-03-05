#!/usr/bin/env python3
"""
Multi-platform load tester for Moniker resolver.
Generates sustained traffic to populate telemetry dashboards.
"""

import argparse
import asyncio
import time
from datetime import datetime
from typing import List
import urllib.request
import urllib.error


class LoadTester:
    def __init__(self, base_url: str, duration: int, concurrent: int, rps: int):
        self.base_url = base_url
        self.duration = duration
        self.concurrent = concurrent
        self.rps = rps
        self.delay = 1.0 / (rps / concurrent) if rps > 0 else 0.1

        self.stats = {
            "total": 0,
            "success": 0,
            "errors": 0,
            "start_time": None,
            "latencies": []
        }

    def make_request(self, path: str) -> tuple[bool, float]:
        """Make a single HTTP request and return (success, latency_ms)"""
        url = f"{self.base_url}{path}"
        start = time.time()

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                response.read()
                latency_ms = (time.time() - start) * 1000
                return response.status == 200, latency_ms
        except urllib.error.HTTPError as e:
            latency_ms = (time.time() - start) * 1000
            return e.code < 500, latency_ms  # 4xx is "success" for testing
        except Exception:
            latency_ms = (time.time() - start) * 1000
            return False, latency_ms

    async def worker(self, worker_id: int, paths: List[str]):
        """Worker coroutine that generates requests"""
        end_time = self.stats["start_time"] + self.duration
        path_idx = 0

        while time.time() < end_time:
            path = paths[path_idx % len(paths)]
            path_idx += 1

            # Make request (blocking, but in separate "thread" via asyncio)
            success, latency = await asyncio.to_thread(self.make_request, path)

            # Update stats
            self.stats["total"] += 1
            if success:
                self.stats["success"] += 1
            else:
                self.stats["errors"] += 1
            self.stats["latencies"].append(latency)

            # Rate limiting
            await asyncio.sleep(self.delay)

    async def run(self):
        """Run the load test"""
        print(f"🚀 Starting load test against {self.base_url}")
        print(f"   Duration: {self.duration}s")
        print(f"   Concurrent workers: {self.concurrent}")
        print(f"   Target RPS: {self.rps}")
        print(f"   Request delay: {self.delay:.3f}s")
        print()

        # Test paths
        paths = [
            "/resolve/commodities/crypto@latest",
            "/resolve/reference/rates@latest",
            "/resolve/sales/metrics/revenue@latest",
            "/resolve/hr/employee-data@latest",
            "/describe/commodities/crypto@latest",
            "/list/commodities",
            "/health",
        ]

        self.stats["start_time"] = time.time()

        # Start workers
        workers = [
            asyncio.create_task(self.worker(i, paths))
            for i in range(self.concurrent)
        ]

        # Progress reporter
        async def report_progress():
            while any(not w.done() for w in workers):
                elapsed = time.time() - self.stats["start_time"]
                actual_rps = self.stats["total"] / elapsed if elapsed > 0 else 0

                print(f"\r⏱  {elapsed:.1f}s | "
                      f"Requests: {self.stats['total']} | "
                      f"Success: {self.stats['success']} | "
                      f"Errors: {self.stats['errors']} | "
                      f"RPS: {actual_rps:.1f}",
                      end="", flush=True)

                await asyncio.sleep(1)

        reporter = asyncio.create_task(report_progress())

        # Wait for all workers
        await asyncio.gather(*workers)
        reporter.cancel()

        print()  # New line after progress
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        elapsed = time.time() - self.stats["start_time"]
        actual_rps = self.stats["total"] / elapsed

        latencies = sorted(self.stats["latencies"])
        p50 = latencies[len(latencies) // 2] if latencies else 0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
        avg = sum(latencies) / len(latencies) if latencies else 0

        print()
        print("=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"Duration:        {elapsed:.2f}s")
        print(f"Total Requests:  {self.stats['total']}")
        print(f"Successful:      {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"Errors:          {self.stats['errors']}")
        print(f"Actual RPS:      {actual_rps:.2f}")
        print()
        print(f"Latency (ms):")
        print(f"  Average:       {avg:.2f}")
        print(f"  p50:           {p50:.2f}")
        print(f"  p95:           {p95:.2f}")
        print(f"  p99:           {p99:.2f}")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(
        description="Load tester for Moniker resolver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Light load for 30 seconds
  python load_tester.py --duration 30 --concurrent 5 --rps 10

  # Heavy load for 2 minutes
  python load_tester.py --duration 120 --concurrent 20 --rps 100

  # Stress test
  python load_tester.py --duration 60 --concurrent 50 --rps 500

  # Test against Java resolver
  python load_tester.py --url http://localhost:8054 --duration 60
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8054",
        help="Base URL of resolver (default: http://localhost:8054)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in seconds (default: 30)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)"
    )
    parser.add_argument(
        "--rps",
        type=int,
        default=50,
        help="Target requests per second (default: 50)"
    )

    args = parser.parse_args()

    tester = LoadTester(
        base_url=args.url,
        duration=args.duration,
        concurrent=args.concurrent,
        rps=args.rps
    )

    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
